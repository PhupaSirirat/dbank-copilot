"""
KPI Tools - Pre-aggregated KPI queries from dbt marts
"""

import os
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

def get_top_root_causes(
    year: int,
    month: Optional[int] = None,
    top_n: int = 10,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get top root causes from pre-aggregated dbt mart
    
    Args:
        year: Year (e.g., 2025)
        month: Optional month (1-12)
        top_n: Number of top causes to return (1-50)
        category_filter: Optional category filter
    
    Returns:
        List of top root causes with metrics
    """
    # Validate inputs
    if year < 2020 or year > 2030:
        raise ValueError("Year must be between 2020 and 2030")
    
    if month and (month < 1 or month > 12):
        raise ValueError("Month must be between 1 and 12")
    
    if top_n < 1 or top_n > 50:
        raise ValueError("top_n must be between 1 and 50")
    
    # Build query
    query = """
        SELECT 
            root_cause_name,
            root_cause_severity,
            category_name,
            product_category,
            total_tickets,
            open_tickets,
            resolved_tickets,
            pct_of_period,
            pct_open,
            avg_resolution_hours,
            median_resolution_hours,
            avg_satisfaction_score,
            satisfaction_rate,
            v12_related_tickets,
            pct_v12_related,
            created_year,
            created_month,
            created_month_name
        FROM analytics_marts.mart_top_root_causes
        WHERE created_year = %s
    """
    
    params = [year]
    
    # Add month filter if provided
    if month:
        query += " AND created_month = %s"
        params.append(month)
    
    # Add category filter if provided
    if category_filter:
        query += " AND category_name = %s"
        params.append(category_filter)
    
    # Order and limit
    query += " ORDER BY total_tickets DESC LIMIT %s"
    params.append(top_n)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Convert to list of dicts with formatted values
        formatted_results = []
        for row in results:
            formatted_results.append({
                'root_cause': row['root_cause_name'],
                'severity': row['root_cause_severity'],
                'category': row['category_name'],
                'product_category': row['product_category'],
                'metrics': {
                    'total_tickets': int(row['total_tickets']),
                    'open_tickets': int(row['open_tickets']),
                    'resolved_tickets': int(row['resolved_tickets']),
                    'pct_of_period': float(row['pct_of_period']) if row['pct_of_period'] else 0,
                    'pct_open': float(row['pct_open']) if row['pct_open'] else 0,
                    'avg_resolution_hours': float(row['avg_resolution_hours']) if row['avg_resolution_hours'] else 0,
                    'median_resolution_hours': float(row['median_resolution_hours']) if row['median_resolution_hours'] else 0,
                    'avg_satisfaction': float(row['avg_satisfaction_score']) if row['avg_satisfaction_score'] else 0,
                    'satisfaction_rate': float(row['satisfaction_rate']) if row['satisfaction_rate'] else 0
                },
                'v12_impact': {
                    'v12_tickets': int(row['v12_related_tickets']) if row['v12_related_tickets'] else 0,
                    'pct_v12': float(row['pct_v12_related']) if row['pct_v12_related'] else 0
                },
                'time_period': {
                    'year': int(row['created_year']),
                    'month': int(row['created_month']),
                    'month_name': row['created_month_name']
                }
            })
        
        cur.close()
        conn.close()
        
        return formatted_results
    
    except psycopg2.Error as e:
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        raise Exception(f"KPI query failed: {str(e)}")

def get_churn_summary(
    days: int = 30,
    segment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get churn summary from dbt mart
    
    Args:
        days: Churn period (30 or 90)
        segment: Optional customer segment filter
    
    Returns:
        Churn summary metrics
    """
    if days not in [30, 90]:
        raise ValueError("days must be 30 or 90")
    
    churn_flag = f"is_churned_{days}d"
    
    query = f"""
        SELECT 
            COUNT(*) as total_churned,
            AVG(days_since_login) as avg_days_inactive,
            SUM(estimated_clv) as total_clv_at_risk,
            COUNT(CASE WHEN churn_risk_level = 'critical' THEN 1 END) as critical_count,
            COUNT(CASE WHEN churn_risk_level = 'high' THEN 1 END) as high_count
        FROM analytics_marts.mart_churned_customers
        WHERE {churn_flag} = true
    """
    
    params = []
    
    if segment:
        query += " AND customer_segment = %s"
        params.append(segment)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'churn_period_days': days,
            'segment': segment or 'all',
            'total_churned': int(result['total_churned']),
            'avg_days_inactive': float(result['avg_days_inactive']) if result['avg_days_inactive'] else 0,
            'total_clv_at_risk': float(result['total_clv_at_risk']) if result['total_clv_at_risk'] else 0,
            'risk_breakdown': {
                'critical': int(result['critical_count']),
                'high': int(result['high_count'])
            }
        }
    
    except Exception as e:
        raise Exception(f"Churn summary failed: {str(e)}")

def get_v12_impact_summary() -> Dict[str, Any]:
    """Get summary of v1.2 app version impact"""
    
    query = """
        SELECT 
            COUNT(*) as total_v12_tickets,
            COUNT(DISTINCT product_type) as affected_products,
            AVG(resolution_time_hours) as avg_resolution_hours,
            COUNT(CASE WHEN ticket_status = 'open' THEN 1 END) as still_open,
            STRING_AGG(DISTINCT product_type, ', ') as product_list
        FROM analytics_marts.mart_ticket_analytics
        WHERE is_v12_related = true
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(query)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'total_v12_tickets': int(result['total_v12_tickets']),
            'affected_products': int(result['affected_products']),
            'product_list': result['product_list'],
            'avg_resolution_hours': float(result['avg_resolution_hours']) if result['avg_resolution_hours'] else 0,
            'still_open': int(result['still_open']),
            'pct_still_open': round(int(result['still_open']) * 100.0 / int(result['total_v12_tickets']), 2) if result['total_v12_tickets'] > 0 else 0
        }
    
    except Exception as e:
        raise Exception(f"v1.2 impact summary failed: {str(e)}")

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing KPI Tools")
    print("=" * 60)
    
    # Test 1: Top root causes
    print("\n1. Testing top root causes...")
    try:
        results = get_top_root_causes(year=2025, month=10, top_n=5)
        print(f"✅ Found {len(results)} root causes")
        for i, rc in enumerate(results[:3], 1):
            print(f"\n   #{i}: {rc['root_cause']}")
            print(f"   Tickets: {rc['metrics']['total_tickets']} ({rc['metrics']['pct_of_period']}%)")
            print(f"   Open: {rc['metrics']['pct_open']}%")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Churn summary
    print("\n2. Testing churn summary...")
    try:
        summary = get_churn_summary(days=30)
        print(f"✅ Churn Summary (30 days):")
        print(f"   Total churned: {summary['total_churned']}")
        print(f"   Avg days inactive: {summary['avg_days_inactive']:.1f}")
        print(f"   CLV at risk: ${summary['total_clv_at_risk']:,.0f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: v1.2 impact
    print("\n3. Testing v1.2 impact...")
    try:
        impact = get_v12_impact_summary()
        print(f"✅ v1.2 Impact:")
        print(f"   Total tickets: {impact['total_v12_tickets']}")
        print(f"   Affected products: {impact['product_list']}")
        print(f"   Still open: {impact['still_open']} ({impact['pct_still_open']}%)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)