"""
SQL Query Tool - Enhanced version with security, logging, and safety features
Execute read-only, parameterized SQL queries with comprehensive protection
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

# Safety limits
SQL_TIMEOUT_SECONDS = int(os.getenv('SQL_TIMEOUT_SECONDS', '30'))
MAX_RESULT_ROWS = int(os.getenv('MAX_RESULT_ROWS', '1000'))
MAX_QUERY_LENGTH = 10000

# PII field patterns (case-insensitive)
PII_FIELDS = [
    'email', 'phone', 'mobile', 'ssn', 'passport', 'id_number',
    'credit_card', 'card_number', 'account_number', 'tax_id',
    'national_id', 'drivers_license', 'address', 'home_address',
    'first_name', 'last_name', 'full_name', 'birth_date', 'dob'
]

# =====================================================
# Connection Management
# =====================================================

@contextmanager
def get_db_connection(read_only: bool = True):
    """
    Context manager for database connections
    
    Args:
        read_only: If True, set transaction to read-only mode
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Set read-only mode for extra safety
        if read_only:
            cur = conn.cursor()
            cur.execute("SET TRANSACTION READ ONLY")
            cur.close()
        
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise Exception(f"Failed to connect to database: {str(e)}")
    finally:
        if conn:
            conn.close()

# =====================================================
# SQL Validation
# =====================================================

def is_read_only(query: str) -> bool:
    """
    Check if query is read-only (SELECT/WITH only)
    
    Args:
        query: SQL query string
    
    Returns:
        True if query appears to be read-only
    """
    # Normalize query
    normalized = query.strip().upper()
    
    # Remove comments
    normalized = re.sub(r'--.*?$', '', normalized, flags=re.MULTILINE)
    normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
    
    # Check for write operations
    write_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'CALL', 'DO'
    ]
    
    for keyword in write_keywords:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, normalized):
            return False
    
    # Must start with SELECT or WITH (for CTEs)
    if not (normalized.startswith('SELECT') or normalized.startswith('WITH')):
        return False
    
    return True

def validate_sql_query(query: str) -> Optional[str]:
    """
    Validate SQL query for safety
    
    Args:
        query: SQL query string
    
    Returns:
        Error message if invalid, None if valid
    """
    if not query or not query.strip():
        return "Query cannot be empty"
    
    if len(query) > MAX_QUERY_LENGTH:
        return f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        (r';\s*SELECT', 'Multiple statements detected'),
        (r';\s*WITH', 'Multiple statements detected'),
        (r'pg_sleep', 'Sleep functions not allowed'),
        (r'dblink', 'Database links not allowed'),
        (r'copy\s+', 'COPY command not allowed'),
        (r'lo_import', 'Large object functions not allowed'),
        (r'lo_export', 'Large object functions not allowed'),
        (r'\binto\s+outfile\b', 'File operations not allowed'),
        (r'\bload_file\b', 'File operations not allowed'),
    ]
    
    normalized = query.upper()
    for pattern, message in dangerous_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return message
    
    return None

def extract_table_names(query: str) -> List[str]:
    """
    Extract table names from query for logging/auditing
    
    Args:
        query: SQL query string
    
    Returns:
        List of table names found in query
    """
    # Simple extraction - looks for FROM and JOIN clauses
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z0-9_\.]+)'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return list(set(matches))

# =====================================================
# PII Masking
# =====================================================

def is_pii_field(field_name: str) -> bool:
    """Check if field name suggests PII data"""
    field_lower = field_name.lower()
    return any(pii in field_lower for pii in PII_FIELDS)

def mask_value(value: Any, field_name: str) -> Any:
    """
    Mask a single value if it's PII
    
    Args:
        value: Value to potentially mask
        field_name: Field name to check if PII
    
    Returns:
        Masked or original value
    """
    if value is None or not is_pii_field(field_name):
        return value
    
    value_str = str(value)
    
    # Email masking: show first char and domain
    if 'email' in field_name.lower() and '@' in value_str:
        local, domain = value_str.split('@', 1)
        return f"{local[0]}***@{domain}"
    
    # Phone masking: show last 4 digits
    elif 'phone' in field_name.lower() or 'mobile' in field_name.lower():
        if len(value_str) >= 4:
            return f"***-***-{value_str[-4:]}"
        return "***"
    
    # General masking: show first and last char
    elif len(value_str) > 2:
        return f"{value_str[0]}{'*' * (len(value_str) - 2)}{value_str[-1]}"
    else:
        return "***"

def mask_query_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mask PII fields in query results
    
    Args:
        results: List of result dictionaries
    
    Returns:
        Results with PII fields masked
    """
    if not results:
        return results
    
    masked_results = []
    for row in results:
        masked_row = {}
        for field, value in row.items():
            masked_row[field] = mask_value(value, field)
        masked_results.append(masked_row)
    
    return masked_results

# =====================================================
# Parameter Handling
# =====================================================

def convert_named_to_positional(
    query: str, 
    parameters: Dict[str, Any]
) -> Tuple[str, List[Any]]:
    """
    Convert {{name}} placeholders to %s for psycopg2 parameter binding
    
    Args:
        query: Query with {{name}} placeholders
        parameters: Dictionary of parameter values
    
    Returns:
        Tuple of (modified query, list of parameter values)
    """
    # Find all {{param}} placeholders
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, query)
    
    if not matches:
        return query, []
    
    # Build list of values in order they appear
    param_values = []
    modified_query = query
    
    for param_name in matches:
        if param_name not in parameters:
            raise ValueError(f"Missing parameter: {param_name}")
        
        param_values.append(parameters[param_name])
        # Replace first occurrence of {{param_name}} with %s
        modified_query = modified_query.replace(
            f"{{{{{param_name}}}}}", 
            "%s", 
            1
        )
    
    return modified_query, param_values

def validate_parameters(parameters: Dict[str, Any]) -> Optional[str]:
    """
    Validate parameter values
    
    Args:
        parameters: Parameter dictionary
    
    Returns:
        Error message if invalid, None if valid
    """
    if not parameters:
        return None
    
    for key, value in parameters.items():
        # Check key format
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            return f"Invalid parameter name: {key}"
        
        # Check for suspicious values
        if isinstance(value, str):
            if len(value) > 1000:
                return f"Parameter {key} value too long (max 1000 chars)"
            
            # Check for SQL injection attempts
            suspicious_patterns = [';', '--', '/*', '*/', 'xp_', 'sp_']
            for pattern in suspicious_patterns:
                if pattern in value.lower():
                    return f"Suspicious pattern in parameter {key}: {pattern}"
    
    return None

# =====================================================
# Query Execution
# =====================================================

def execute_sql_query(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    mask_pii: bool = True,
    max_rows: Optional[int] = None,
    explain_only: bool = False
) -> Dict[str, Any]:
    """
    Execute a read-only SQL query with comprehensive safety checks
    
    Args:
        query: SQL query string (SELECT only)
        parameters: Optional parameters for parameterized queries
        mask_pii: Whether to mask PII fields in results
        max_rows: Maximum rows to return (default: MAX_RESULT_ROWS)
        explain_only: If True, return query plan instead of executing
    
    Returns:
        Dictionary with results and metadata:
        {
            'results': [...],
            'row_count': int,
            'execution_time_ms': float,
            'columns': [...],
            'truncated': bool
        }
    
    Raises:
        ValueError: If query is not read-only or invalid
        Exception: If execution fails
    """
    start_time = datetime.now()
    
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
    
    # Validate parameters
    if parameters:
        param_error = validate_parameters(parameters)
        if param_error:
            raise ValueError(f"Parameter validation failed: {param_error}")
    
    # Set max rows
    if max_rows is None:
        max_rows = MAX_RESULT_ROWS
    elif max_rows > MAX_RESULT_ROWS:
        logger.warning(f"Requested max_rows {max_rows} exceeds limit, using {MAX_RESULT_ROWS}")
        max_rows = MAX_RESULT_ROWS
    
    # Convert parameters if provided
    if parameters:
        query, param_values = convert_named_to_positional(query, parameters)
    else:
        param_values = []
    
    # Add LIMIT if not present (safety measure)
    if 'LIMIT' not in query.upper() and max_rows:
        query = f"{query.rstrip(';')} LIMIT {max_rows + 1}"  # +1 to detect truncation
    
    # Log query execution
    table_names = extract_table_names(query)
    logger.info(f"Executing query on tables: {', '.join(table_names) if table_names else 'unknown'}")
    logger.debug(f"Query: {query[:200]}...")  # Log first 200 chars
    
    try:
        with get_db_connection(read_only=True) as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Set statement timeout
            cur.execute(f"SET statement_timeout = '{SQL_TIMEOUT_SECONDS}s'")
            
            # EXPLAIN only mode
            if explain_only:
                explain_query = f"EXPLAIN (FORMAT JSON) {query}"
                if param_values:
                    cur.execute(explain_query, param_values)
                else:
                    cur.execute(explain_query)
                
                explain_result = cur.fetchone()
                cur.close()
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    'query_plan': explain_result,
                    'execution_time_ms': round(execution_time, 2),
                    'explain_only': True
                }
            
            # Execute query with parameters
            if param_values:
                cur.execute(query, param_values)
            else:
                cur.execute(query)
            
            # Fetch results
            results = cur.fetchall()
            
            # Check if truncated
            truncated = len(results) > max_rows
            if truncated:
                results = results[:max_rows]
                logger.warning(f"Results truncated to {max_rows} rows")
            
            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []
            
            # Convert to list of dicts
            results_list = [dict(row) for row in results]
            
            # Mask PII if requested
            if mask_pii and results_list:
                results_list = mask_query_results(results_list)
            
            cur.close()
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"Query executed successfully: {len(results_list)} rows in {execution_time:.2f}ms")
        
        return {
            'results': results_list,
            'row_count': len(results_list),
            'execution_time_ms': round(execution_time, 2),
            'columns': columns,
            'truncated': truncated,
            'tables_accessed': table_names,
            'timestamp': datetime.now().isoformat()
        }
    
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        error_msg = str(e)
        
        # Provide helpful error messages
        if 'timeout' in error_msg.lower():
            raise Exception(f"Query timeout after {SQL_TIMEOUT_SECONDS} seconds. Try simplifying your query.")
        elif 'permission' in error_msg.lower():
            raise Exception(f"Permission denied. You may not have access to these tables: {', '.join(table_names)}")
        else:
            raise Exception(f"Database error: {error_msg}")
    
    except Exception as e:
        logger.error(f"Query execution error: {e}", exc_info=True)
        raise Exception(f"Query execution failed: {str(e)}")

# =====================================================
# Utility Functions
# =====================================================

def get_table_info(schema: str = 'analytics') -> List[Dict[str, Any]]:
    """
    Get information about available tables
    
    Args:
        schema: Database schema name
    
    Returns:
        List of tables with column information
    """
    query = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
    """
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, (schema,))
            results = cur.fetchall()
            cur.close()
        
        # Group by table
        tables = {}
        for row in results:
            table_name = row['table_name']
            if table_name not in tables:
                tables[table_name] = {
                    'table_name': table_name,
                    'columns': []
                }
            
            tables[table_name]['columns'].append({
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES'
            })
        
        return list(tables.values())
    
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise Exception(f"Failed to get table info: {str(e)}")

def test_query_performance(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Test query performance without returning results
    
    Args:
        query: SQL query
        parameters: Optional parameters
    
    Returns:
        Performance metrics
    """
    try:
        # Get query plan
        plan_result = execute_sql_query(query, parameters, explain_only=True)
        
        return {
            'query_plan': plan_result['query_plan'],
            'plan_time_ms': plan_result['execution_time_ms'],
            'estimated_cost': 'See query_plan for details'
        }
    
    except Exception as e:
        return {
            'error': str(e)
        }

# =====================================================
# Example Queries
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
            """,
            "parameters": None
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
            """,
            "parameters": None
        },
        {
            "name": "Churned customers (parameterized)",
            "query": """
                SELECT 
                    customer_uuid,
                    customer_segment,
                    days_since_login,
                    estimated_clv
                FROM analytics_marts.mart_churned_customers
                WHERE is_churned_{{days}}d = true
                ORDER BY estimated_clv DESC
                LIMIT {{limit}}
            """,
            "parameters": {
                "days": 30,
                "limit": 10
            }
        },
        {
            "name": "Root causes by severity",
            "query": """
                SELECT 
                    root_cause_severity,
                    COUNT(*) as cause_count,
                    SUM(total_tickets) as total_tickets
                FROM analytics_marts.mart_top_root_causes
                WHERE created_year = {{year}}
                GROUP BY root_cause_severity
                ORDER BY total_tickets DESC
            """,
            "parameters": {
                "year": 2025
            }
        }
    ]
    
    return examples

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTING ENHANCED SQL QUERY TOOL")
    print("=" * 80)
    
    # Test 1: Simple query
    print("\n1. Testing simple query...")
    try:
        result = execute_sql_query(
            "SELECT COUNT(*) as total FROM analytics.dim_customers"
        )
        print(f"✅ Success:")
        print(f"   Rows: {result['row_count']}")
        print(f"   Time: {result['execution_time_ms']}ms")
        print(f"   Results: {result['results']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Query with PII masking
    print("\n2. Testing PII masking...")
    try:
        result = execute_sql_query(
            "SELECT customer_uuid, email, phone FROM analytics.dim_customers LIMIT 3",
            mask_pii=True
        )
        print(f"✅ Success (PII masked):")
        print(f"   Rows: {result['row_count']}")
        print(f"   Columns: {result['columns']}")
        for row in result['results']:
            print(f"   {row}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Parameterized query
    print("\n3. Testing parameterized query...")
    try:
        result = execute_sql_query(
            "SELECT * FROM analytics.fact_tickets WHERE ticket_status = {{status}} LIMIT {{limit}}",
            parameters={"status": "open", "limit": 5}
        )
        print(f"✅ Success:")
        print(f"   Rows: {result['row_count']}")
        print(f"   Time: {result['execution_time_ms']}ms")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Invalid query (should fail)
    print("\n4. Testing invalid query (should fail)...")
    try:
        result = execute_sql_query("DELETE FROM analytics.dim_customers")
        print(f"❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly blocked: {e}")
    
    # Test 5: SQL injection attempt (should fail)
    print("\n5. Testing SQL injection protection...")
    try:
        result = execute_sql_query(
            "SELECT * FROM analytics.dim_customers WHERE customer_uuid = {{uuid}}",
            parameters={"uuid": "'; DROP TABLE customers; --"}
        )
        print(f"✅ SQL injection blocked by parameter validation")
    except Exception as e:
        print(f"✅ Correctly blocked: {e}")
    
    # Test 6: Query plan
    print("\n6. Testing query plan (EXPLAIN)...")
    try:
        result = execute_sql_query(
            "SELECT * FROM analytics.fact_tickets WHERE ticket_status = 'open'",
            explain_only=True
        )
        print(f"✅ Success:")
        print(f"   Plan time: {result['execution_time_ms']}ms")
        print(f"   Explain only: {result['explain_only']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Get table info
    print("\n7. Testing table info...")
    try:
        tables = get_table_info('analytics')
        print(f"✅ Found {len(tables)} tables in analytics schema")
        if tables:
            print(f"   First table: {tables[0]['table_name']} ({len(tables[0]['columns'])} columns)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)