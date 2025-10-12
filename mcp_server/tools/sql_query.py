"""
SQL Query Tool - Execute read-only, parameterized SQL queries
"""

import os
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re

from utils.sql_validator import validate_sql_query, is_read_only
from utils.pii_masking import mask_query_results

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

# SQL execution timeout (seconds)
SQL_TIMEOUT = 30

def execute_sql_query(
    query: str, 
    parameters: Dict[str, Any] = None,
    mask_pii: bool = True
) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query with safety checks
    
    Args:
        query: SQL query string (SELECT only)
        parameters: Optional parameters for parameterized queries
        mask_pii: Whether to mask PII fields in results
    
    Returns:
        List of result rows as dictionaries
    
    Raises:
        ValueError: If query is not read-only or invalid
        Exception: If execution fails
    """
    # Validate query
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Check if read-only
    if not is_read_only(query):
        raise ValueError(
            "Only SELECT queries are allowed. "
            "DELETE, UPDATE, DROP, INSERT, ALTER, and other write operations are forbidden."
        )
    
    # Validate SQL syntax and dangerous patterns
    validation_error = validate_sql_query(query)
    if validation_error:
        raise ValueError(f"Query validation failed: {validation_error}")
    
    # Replace parameter placeholders if provided
    if parameters:
        query = replace_parameters(query, parameters)
    
    # Connect and execute
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Set statement timeout
        cur.execute(f"SET statement_timeout = {SQL_TIMEOUT * 1000}")
        
        # Execute query
        cur.execute(query)
        
        # Fetch results
        results = cur.fetchall()
        
        # Convert to list of dicts
        results_list = [dict(row) for row in results]
        
        # Mask PII if requested
        if mask_pii:
            results_list = mask_query_results(results_list)
        
        cur.close()
        conn.close()
        
        return results_list
    
    except psycopg2.Error as e:
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")

def replace_parameters(query: str, parameters: Dict[str, Any]) -> str:
    """
    Replace {{param}} placeholders with safe parameter values
    
    Args:
        query: SQL query with {{param}} placeholders
        parameters: Dictionary of parameter values
    
    Returns:
        Query with parameters substituted
    """
    for key, value in parameters.items():
        placeholder = f"{{{{{key}}}}}"
        
        # Escape value based on type
        if isinstance(value, str):
            # Escape single quotes for SQL
            safe_value = value.replace("'", "''")
            safe_value = f"'{safe_value}'"
        elif value is None:
            safe_value = "NULL"
        else:
            safe_value = str(value)
        
        query = query.replace(placeholder, safe_value)
    
    return query

# =====================================================
# Example Queries (for testing)
# =====================================================

def example_queries():
    """Example SQL queries for testing"""
    
    examples = [
        {
            "name": "Top 5 customers by balance",
            "query": """
                SELECT 
                    c.customer_uuid,
                    c.customer_segment,
                    SUM(cp.balance) as total_balance
                FROM analytics.dim_customers c
                JOIN analytics.fact_customer_products cp ON c.customer_id = cp.customer_id
                WHERE cp.status = 'active'
                GROUP BY c.customer_uuid, c.customer_segment
                ORDER BY total_balance DESC
                LIMIT 5
            """
        },
        {
            "name": "Tickets by status",
            "query": """
                SELECT 
                    ticket_status,
                    COUNT(*) as count
                FROM analytics.fact_tickets
                GROUP BY ticket_status
                ORDER BY count DESC
            """
        },
        {
            "name": "Churned customers in last 30 days (parameterized)",
            "query": """
                SELECT 
                    customer_uuid,
                    customer_segment,
                    days_since_login
                FROM marts.mart_churned_customers
                WHERE is_churned_{{days}}d = true
                ORDER BY estimated_clv DESC
                LIMIT {{limit}}
            """,
            "parameters": {
                "days": "30",
                "limit": "10"
            }
        }
    ]
    
    return examples

if __name__ == "__main__":
    # Test the tool
    print("=" * 60)
    print("🧪 Testing SQL Query Tool")
    print("=" * 60)
    
    # Test 1: Simple query
    print("\n1. Testing simple query...")
    try:
        results = execute_sql_query(
            "SELECT COUNT(*) as total FROM analytics.dim_customers"
        )
        print(f"✅ Success: {results}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Query with PII
    print("\n2. Testing PII masking...")
    try:
        results = execute_sql_query(
            "SELECT customer_uuid, email, phone FROM analytics.dim_customers LIMIT 3",
            mask_pii=True
        )
        print(f"✅ Success (PII masked):")
        for row in results:
            print(f"   {row}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Invalid query (should fail)
    print("\n3. Testing invalid query (should fail)...")
    try:
        results = execute_sql_query("DELETE FROM analytics.dim_customers")
        print(f"❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly blocked: {e}")
    
    print("\n" + "=" * 60)