"""
Load sample CSV data into PostgreSQL
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import os
from datetime import datetime

# Load .env but don't override existing environment variables
load_dotenv(override=False)  # ✅ Docker env vars take precedence

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5433')),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

DATA_DIR = 'data_layer/sample_data'

def get_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def load_time_dimension(conn, csv_file):
    """Load time dimension"""
    print("\n📅 Loading Time Dimension...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO analytics.dim_time 
            (date, year, quarter, month, month_name, week, day_of_month, 
             day_of_week, day_name, is_weekend, is_holiday)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO NOTHING
        """
        
        data = [
            (
                row['date'], row['year'], row['quarter'], row['month'],
                row['month_name'], row['week'], row['day_of_month'],
                row['day_of_week'], row['day_name'], row['is_weekend'],
                row['is_holiday']
            )
            for _, row in df.iterrows()
        ]
        
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        print(f"✅ Loaded {len(df)} time dimension records")

def load_customers(conn, csv_file):
    """Load customers dimension"""
    print("\n👥 Loading Customers...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO analytics.dim_customers 
            (customer_uuid, full_name, email, phone, national_id, date_of_birth,
             gender, customer_segment, registration_date, account_status, city, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_uuid) DO NOTHING
            RETURNING customer_id
        """
        
        data = [
            (
                row['customer_uuid'], row['full_name'], row['email'], 
                row['phone'], row['national_id'], row['date_of_birth'],
                row['gender'], row['customer_segment'], row['registration_date'],
                row['account_status'], row['city'], row['country']
            )
            for _, row in df.iterrows()
        ]
        
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        print(f"✅ Loaded {len(df)} customers")

def load_products(conn, csv_file):
    """Load products dimension"""
    print("\n📦 Loading Products...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO analytics.dim_products 
            (product_code, product_name, product_category, product_type, 
             description, launch_date, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_code) DO NOTHING
        """
        
        data = [
            (
                row['product_code'], row['product_name'], row['product_category'],
                row['product_type'], row['description'], row['launch_date'],
                row['is_active']
            )
            for _, row in df.iterrows()
        ]
        
        execute_batch(cur, insert_query, data, page_size=100)
        conn.commit()
        print(f"✅ Loaded {len(df)} products")

def load_ticket_categories(conn, csv_file):
    """Load ticket categories dimension"""
    print("\n🎫 Loading Ticket Categories...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO analytics.dim_ticket_categories 
            (category_code, category_name, parent_category, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (category_code) DO NOTHING
        """
        
        data = [
            (
                row['category_code'], row['category_name'], 
                row['parent_category'], None
            )
            for _, row in df.iterrows()
        ]
        
        execute_batch(cur, insert_query, data, page_size=100)
        conn.commit()
        print(f"✅ Loaded {len(df)} ticket categories")

def load_root_causes(conn, csv_file):
    """Load root causes dimension"""
    print("\n🔍 Loading Root Causes...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO analytics.dim_root_causes 
            (root_cause_code, root_cause_name, category, severity, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (root_cause_code) DO NOTHING
        """
        
        data = [
            (
                row['root_cause_code'], row['root_cause_name'],
                row['category'], row['severity'], None
            )
            for _, row in df.iterrows()
        ]
        
        execute_batch(cur, insert_query, data, page_size=100)
        conn.commit()
        print(f"✅ Loaded {len(df)} root causes")

def load_tickets(conn, csv_file):
    """Load tickets fact table"""
    print("\n🎟️  Loading Tickets...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        # Get customer mapping
        cur.execute("SELECT customer_uuid, customer_id FROM analytics.dim_customers")
        customer_map = {row[0]: row[1] for row in cur.fetchall()}
        
        # Get product mapping
        cur.execute("SELECT product_code, product_id FROM analytics.dim_products")
        product_map = {row[0]: row[1] for row in cur.fetchall()}
        
        # Get category mapping
        cur.execute("SELECT category_code, category_id FROM analytics.dim_ticket_categories")
        category_map = {row[0]: row[1] for row in cur.fetchall()}
        
        # Get root cause mapping
        cur.execute("SELECT root_cause_code, root_cause_id FROM analytics.dim_root_causes")
        root_cause_map = {row[0]: row[1] for row in cur.fetchall()}
        
        insert_query = """
            INSERT INTO analytics.fact_tickets 
            (ticket_number, customer_id, product_id, category_id, root_cause_id,
             ticket_status, priority, subject, created_date, resolved_date,
             resolution_time_hours, customer_satisfaction_score, channel, app_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticket_number) DO NOTHING
        """
        
        data = []
        for _, row in df.iterrows():
            customer_id = customer_map.get(row['customer_uuid'])
            product_id = product_map.get(row['product_code'])
            category_id = category_map.get(row['category_code'])
            root_cause_id = root_cause_map.get(row['root_cause_code'])
            
            if all([customer_id, product_id, category_id, root_cause_id]):
                data.append((
                    row['ticket_number'], customer_id, product_id, category_id,
                    root_cause_id, row['ticket_status'], row['priority'],
                    row['subject'], row['created_date'],
                    row.get('resolved_date') if pd.notna(row.get('resolved_date')) else None,
                    row.get('resolution_time_hours') if pd.notna(row.get('resolution_time_hours')) else None,
                    row.get('customer_satisfaction_score') if pd.notna(row.get('customer_satisfaction_score')) else None,
                    row['channel'], row['app_version']
                ))
        
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        print(f"✅ Loaded {len(data)} tickets")

def load_customer_products(conn, csv_file):
    """Load customer product holdings"""
    print("\n💰 Loading Customer Product Holdings...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        # Get mappings
        cur.execute("SELECT customer_uuid, customer_id FROM analytics.dim_customers")
        customer_map = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("SELECT product_code, product_id FROM analytics.dim_products")
        product_map = {row[0]: row[1] for row in cur.fetchall()}
        
        insert_query = """
            INSERT INTO analytics.fact_customer_products 
            (customer_id, product_id, activation_date, status, balance, 
             credit_limit, interest_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id, product_id, activation_date) DO NOTHING
        """
        
        data = []
        for _, row in df.iterrows():
            customer_id = customer_map.get(row['customer_uuid'])
            product_id = product_map.get(row['product_code'])
            
            if customer_id and product_id:
                data.append((
                    customer_id, product_id, row['activation_date'],
                    row['status'],
                    row.get('balance') if pd.notna(row.get('balance')) else None,
                    row.get('credit_limit') if pd.notna(row.get('credit_limit')) else None,
                    row['interest_rate']
                ))
        
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        print(f"✅ Loaded {len(data)} product holdings")

def load_logins(conn, csv_file):
    """Load login access data"""
    print("\n🔐 Loading Login Access Data...")
    df = pd.read_csv(csv_file)
    
    with conn.cursor() as cur:
        # Get customer mapping
        cur.execute("SELECT customer_uuid, customer_id FROM analytics.dim_customers")
        customer_map = {row[0]: row[1] for row in cur.fetchall()}
        
        insert_query = """
            INSERT INTO analytics.fact_logins 
            (customer_id, login_date, login_timestamp, session_duration_minutes,
             device_type, os_type, app_version, login_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = []
        for _, row in df.iterrows():
            customer_id = customer_map.get(row['customer_uuid'])
            
            if customer_id:
                data.append((
                    customer_id, row['login_date'], row['login_timestamp'],
                    row['session_duration_minutes'], row['device_type'],
                    row['os_type'], row['app_version'], row['login_status']
                ))
        
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        print(f"✅ Loaded {len(data)} login records")

def main():
    """Main execution"""
    print("=" * 60)
    print("🏦 dBank Data Loader")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("✅ Connected to PostgreSQL database")
        
        # Load in correct order (dimensions first, then facts)
        load_time_dimension(conn, f'{DATA_DIR}/time_dimension.csv')
        load_customers(conn, f'{DATA_DIR}/customers.csv')
        load_products(conn, f'{DATA_DIR}/products.csv')
        load_ticket_categories(conn, f'{DATA_DIR}/ticket_categories.csv')
        load_root_causes(conn, f'{DATA_DIR}/root_causes.csv')
        
        # Load fact tables
        load_tickets(conn, f'{DATA_DIR}/tickets.csv')
        load_customer_products(conn, f'{DATA_DIR}/customer_products.csv')
        load_logins(conn, f'{DATA_DIR}/logins.csv')
        
        print("\n" + "=" * 60)
        print("✨ Data Loading Complete!")
        print("=" * 60)
        
        # Show some stats
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    'Customers' as table_name, COUNT(*) as count 
                FROM analytics.dim_customers
                UNION ALL
                SELECT 'Products', COUNT(*) FROM analytics.dim_products
                UNION ALL
                SELECT 'Tickets', COUNT(*) FROM analytics.fact_tickets
                UNION ALL
                SELECT 'Logins', COUNT(*) FROM analytics.fact_logins
                UNION ALL
                SELECT 'Product Holdings', COUNT(*) FROM analytics.fact_customer_products
            """)
            
            print("\n📊 Database Summary:")
            for row in cur.fetchall():
                print(f"   {row[0]:<20} {row[1]:>10,}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()