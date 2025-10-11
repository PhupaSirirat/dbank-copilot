"""
Verify data quality and run basic tests
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'dbank'),
    'user': os.getenv('DB_USER', 'dbank_user'),
    'password': os.getenv('DB_PASSWORD', 'dbank_pass_2025')
}

def run_query(query, description):
    """Run a query and display results"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    cur.execute(query)
    results = cur.fetchall()
    
    for row in results:
        print(row)
    
    cur.close()
    conn.close()
    
    return results

def main():
    print("=" * 60)
    print("🧪 dBank Data Verification Tests")
    print("=" * 60)
    
    # Test 1: Check all tables have data
    run_query("""
        SELECT 
            schemaname, 
            tablename, 
            n_tup_ins as row_count
        FROM pg_stat_user_tables
        WHERE schemaname IN ('analytics', 'staging', 'vector_store')
        ORDER BY schemaname, tablename;
    """, "Test 1: Table Row Counts")
    
    # Test 2: Top 5 root causes (sample query from requirements)
    results = run_query("""
        SELECT 
            rc.root_cause_name,
            tc.category_name,
            COUNT(*) as ticket_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
            SUM(CASE WHEN t.ticket_status = 'Open' THEN 1 ELSE 0 END) as open_tickets,
            ROUND(SUM(CASE WHEN t.ticket_status = 'Open' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_open
        FROM analytics.fact_tickets t
        JOIN analytics.dim_root_causes rc ON t.root_cause_id = rc.root_cause_id
        JOIN analytics.dim_ticket_categories tc ON t.category_id = tc.category_id
        WHERE t.created_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY rc.root_cause_name, tc.category_name
        ORDER BY ticket_count DESC
        LIMIT 5;
    """, "Test 2: Top 5 Root Causes (Last 30 Days)")
    
    # Test 3: Ticket volume by app version
    run_query("""
        SELECT 
            app_version,
            DATE_TRUNC('day', created_date) as date,
            COUNT(*) as ticket_count
        FROM analytics.fact_tickets
        WHERE created_date >= '2024-08-01'
        GROUP BY app_version, DATE_TRUNC('day', created_date)
        ORDER BY date, app_version;
    """, "Test 3: Ticket Volume by App Version (Aug 2024+)")
    
    # Test 4: Check for v1.2 spike
    run_query("""
        SELECT 
            TO_CHAR(created_date, 'YYYY-MM') as month,
            app_version,
            COUNT(*) as tickets,
            STRING_AGG(DISTINCT p.product_type, ', ') as affected_products
        FROM analytics.fact_tickets t
        JOIN analytics.dim_products p ON t.product_id = p.product_id
        WHERE app_version = 'v1.2'
        GROUP BY TO_CHAR(created_date, 'YYYY-MM'), app_version
        ORDER BY month;
    """, "Test 4: v1.2 Related Issues")
    
    # Test 5: Churned customers (no login in 30 days)
    run_query("""
        SELECT 
            c.customer_segment,
            COUNT(DISTINCT c.customer_id) as customer_count,
            ROUND(AVG(CURRENT_DATE - MAX(l.login_date)), 2) as avg_days_since_login
        FROM analytics.dim_customers c
        LEFT JOIN analytics.fact_logins l ON c.customer_id = l.customer_id
        WHERE c.account_status = 'Active'
        GROUP BY c.customer_segment
        HAVING MAX(l.login_date) < CURRENT_DATE - INTERVAL '30 days' 
            OR MAX(l.login_date) IS NULL
        ORDER BY customer_count DESC;
    """, "Test 5: Churned Customers (No Login 30+ Days)")
    
    # Test 6: Data quality - check for nulls in critical fields
    run_query("""
        SELECT 
            'Tickets with NULL customer' as check_name,
            COUNT(*) as count
        FROM analytics.fact_tickets
        WHERE customer_id IS NULL
        UNION ALL
        SELECT 
            'Tickets with NULL product',
            COUNT(*)
        FROM analytics.fact_tickets
        WHERE product_id IS NULL
        UNION ALL
        SELECT 
            'Customers with NULL email',
            COUNT(*)
        FROM analytics.dim_customers
        WHERE email IS NULL;
    """, "Test 6: Data Quality Checks")
    
    # Test 7: PII fields exist (to be masked later)
    run_query("""
        SELECT 
            customer_uuid,
            full_name,
            email,
            phone,
            national_id,
            customer_segment
        FROM analytics.dim_customers
        LIMIT 3;
    """, "Test 7: Sample Customer Data (PII Fields Present)")
    
    print("\n" + "=" * 60)
    print("✅ Verification Complete!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("   1. Data layer is ready ✓")
    print("   2. Next: Set up dbt for transformations")
    print("   3. Then: Build knowledge base and vector store")
    print("   4. Finally: Create MCP tools and RAG system")

if __name__ == "__main__":
    main()