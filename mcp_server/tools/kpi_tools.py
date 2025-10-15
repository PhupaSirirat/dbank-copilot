"""
KPI Tools - Enhanced version with better error handling and features
Pre-aggregated KPI queries from dbt marts
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from contextlib import contextmanager
import psycopg2
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

# =====================================================
# Database Connection Management
# =====================================================

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise Exception(f"Failed to connect to database: {str(e)}")
    finally:
        if conn:
            conn.close()

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert to int"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

# =====================================================
# Root Cause Analysis
# =====================================================

def get_top_root_causes(
    year: int,
    month: Optional[int] = None,
    top_n: int = 10,
    category_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    min_tickets: int = 0
) -> List[Dict[str, Any]]:
    """
    Get top root causes from pre-aggregated dbt mart with enhanced filtering
    
    Args:
        year: Year (e.g., 2025)
        month: Optional month (1-12)
        top_n: Number of top causes to return (1-50)
        category_filter: Optional category filter
        severity_filter: Optional severity filter (critical, high, medium, low)
        min_tickets: Minimum ticket count threshold
    
    Returns:
        List of top root causes with metrics
    """
    # Validate inputs
    current_year = datetime.now().year
    if year < 2020 or year > current_year + 1:
        raise ValueError(f"Year must be between 2020 and {current_year + 1}")
    
    if month and (month < 1 or month > 12):
        raise ValueError("Month must be between 1 and 12")
    
    if top_n < 1 or top_n > 100:
        raise ValueError("top_n must be between 1 and 100")
    
    if severity_filter and severity_filter.lower() not in ['critical', 'high', 'medium', 'low']:
        raise ValueError("severity_filter must be one of: critical, high, medium, low")
    
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
    
    # Add severity filter if provided
    if severity_filter:
        query += " AND root_cause_severity = %s"
        params.append(severity_filter.lower())
    
    # Add minimum tickets threshold
    if min_tickets > 0:
        query += " AND total_tickets >= %s"
        params.append(min_tickets)
    
    # Order and limit
    query += " ORDER BY total_tickets DESC LIMIT %s"
    params.append(top_n)
    
    try:
        logger.info(f"Fetching top {top_n} root causes for {year}-{month or 'all'}")
        
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
        
        logger.info(f"Retrieved {len(results)} root causes")
        
        # Format results with safe type conversions
        formatted_results = []
        for row in results:
            formatted_results.append({
                'root_cause': row['root_cause_name'],
                'severity': row['root_cause_severity'],
                'category': row['category_name'],
                'product_category': row['product_category'],
                'metrics': {
                    'total_tickets': safe_int(row['total_tickets']),
                    'open_tickets': safe_int(row['open_tickets']),
                    'resolved_tickets': safe_int(row['resolved_tickets']),
                    'pct_of_period': safe_float(row['pct_of_period']),
                    'pct_open': safe_float(row['pct_open']),
                    'avg_resolution_hours': safe_float(row['avg_resolution_hours']),
                    'median_resolution_hours': safe_float(row['median_resolution_hours']),
                    'avg_satisfaction': safe_float(row['avg_satisfaction_score']),
                    'satisfaction_rate': safe_float(row['satisfaction_rate'])
                },
                'v12_impact': {
                    'v12_tickets': safe_int(row['v12_related_tickets']),
                    'pct_v12': safe_float(row['pct_v12_related'])
                },
                'time_period': {
                    'year': safe_int(row['created_year']),
                    'month': safe_int(row['created_month']),
                    'month_name': row['created_month_name']
                }
            })
        
        return formatted_results
    
    except psycopg2.Error as e:
        logger.error(f"Database error in get_top_root_causes: {e}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_top_root_causes: {e}", exc_info=True)
        raise Exception(f"KPI query failed: {str(e)}")

def get_root_cause_trend(
    root_cause_name: str,
    start_year: int,
    start_month: int,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get trend data for a specific root cause over time
    
    Args:
        root_cause_name: Name of the root cause
        start_year: Starting year
        start_month: Starting month
        end_year: Ending year (defaults to current)
        end_month: Ending month (defaults to current)
    
    Returns:
        List of monthly metrics for the root cause
    """
    if not end_year:
        end_year = datetime.now().year
    if not end_month:
        end_month = datetime.now().month
    
    query = """
        SELECT 
            created_year,
            created_month,
            created_month_name,
            total_tickets,
            pct_open,
            avg_resolution_hours,
            avg_satisfaction_score
        FROM analytics_marts.mart_top_root_causes
        WHERE root_cause_name = %s
        AND (
            (created_year > %s) OR 
            (created_year = %s AND created_month >= %s)
        )
        AND (
            (created_year < %s) OR 
            (created_year = %s AND created_month <= %s)
        )
        ORDER BY created_year, created_month
    """
    
    params = [root_cause_name, start_year, start_year, start_month, end_year, end_year, end_month]
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
        
        return [
            {
                'year': safe_int(row['created_year']),
                'month': safe_int(row['created_month']),
                'month_name': row['created_month_name'],
                'total_tickets': safe_int(row['total_tickets']),
                'pct_open': safe_float(row['pct_open']),
                'avg_resolution_hours': safe_float(row['avg_resolution_hours']),
                'avg_satisfaction': safe_float(row['avg_satisfaction_score'])
            }
            for row in results
        ]
    
    except Exception as e:
        logger.error(f"Error getting root cause trend: {e}")
        raise Exception(f"Root cause trend query failed: {str(e)}")

# =====================================================
# Churn Analysis
# =====================================================

def get_churn_summary(
    days: int = 30,
    segment: Optional[str] = None,
    include_breakdown: bool = True
) -> Dict[str, Any]:
    """
    Get churn summary from dbt mart with enhanced breakdown
    
    Args:
        days: Churn period (30 or 90)
        segment: Optional customer segment filter
        include_breakdown: Include detailed breakdown by risk level
    
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
            COUNT(CASE WHEN churn_risk_level = 'high' THEN 1 END) as high_count,
            COUNT(CASE WHEN churn_risk_level = 'medium' THEN 1 END) as medium_count,
            COUNT(CASE WHEN churn_risk_level = 'low' THEN 1 END) as low_count
        FROM analytics_marts.mart_churned_customers
        WHERE {churn_flag} = true
    """
    
    params = []
    
    if segment:
        query += " AND customer_segment = %s"
        params.append(segment)
    
    try:
        logger.info(f"Fetching churn summary for {days}-day period, segment: {segment or 'all'}")
        
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            result = cur.fetchone()
            cur.close()
        
        total_churned = safe_int(result['total_churned'])
        
        summary = {
            'churn_period_days': days,
            'segment': segment or 'all',
            'total_churned': total_churned,
            'avg_days_inactive': round(safe_float(result['avg_days_inactive']), 1),
            'total_clv_at_risk': round(safe_float(result['total_clv_at_risk']), 2)
        }
        
        if include_breakdown and total_churned > 0:
            summary['risk_breakdown'] = {
                'critical': {
                    'count': safe_int(result['critical_count']),
                    'percentage': round(safe_int(result['critical_count']) * 100.0 / total_churned, 1)
                },
                'high': {
                    'count': safe_int(result['high_count']),
                    'percentage': round(safe_int(result['high_count']) * 100.0 / total_churned, 1)
                },
                'medium': {
                    'count': safe_int(result['medium_count']),
                    'percentage': round(safe_int(result['medium_count']) * 100.0 / total_churned, 1)
                },
                'low': {
                    'count': safe_int(result['low_count']),
                    'percentage': round(safe_int(result['low_count']) * 100.0 / total_churned, 1)
                }
            }
        
        logger.info(f"Churn summary: {total_churned} churned customers")
        return summary
    
    except Exception as e:
        logger.error(f"Error in get_churn_summary: {e}")
        raise Exception(f"Churn summary failed: {str(e)}")

def get_churn_by_segment() -> List[Dict[str, Any]]:
    """Get churn rates broken down by customer segment"""
    
    query = """
        SELECT 
            customer_segment,
            COUNT(*) as churned_count,
            AVG(estimated_clv) as avg_clv_at_risk,
            AVG(days_since_login) as avg_days_inactive
        FROM analytics_marts.mart_churned_customers
        WHERE is_churned_30d = true
        GROUP BY customer_segment
        ORDER BY churned_count DESC
    """
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query)
            results = cur.fetchall()
            cur.close()
        
        return [
            {
                'segment': row['customer_segment'],
                'churned_count': safe_int(row['churned_count']),
                'avg_clv_at_risk': round(safe_float(row['avg_clv_at_risk']), 2),
                'avg_days_inactive': round(safe_float(row['avg_days_inactive']), 1)
            }
            for row in results
        ]
    
    except Exception as e:
        logger.error(f"Error getting churn by segment: {e}")
        raise Exception(f"Churn by segment query failed: {str(e)}")

# =====================================================
# v1.2 Impact Analysis
# =====================================================

def get_v12_impact_summary(include_details: bool = False) -> Dict[str, Any]:
    """
    Get summary of v1.2 app version impact with optional details
    
    Args:
        include_details: Include detailed breakdown by product
    
    Returns:
        v1.2 impact summary
    """
    
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
        logger.info("Fetching v1.2 impact summary")
        
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query)
            result = cur.fetchone()
            
            total_tickets = safe_int(result['total_v12_tickets'])
            still_open = safe_int(result['still_open'])
            
            summary = {
                'total_v12_tickets': total_tickets,
                'affected_products': safe_int(result['affected_products']),
                'product_list': result['product_list'],
                'avg_resolution_hours': round(safe_float(result['avg_resolution_hours']), 2),
                'still_open': still_open,
                'pct_still_open': round(still_open * 100.0 / total_tickets, 2) if total_tickets > 0 else 0,
                'pct_resolved': round((total_tickets - still_open) * 100.0 / total_tickets, 2) if total_tickets > 0 else 0
            }
            
            # Add detailed breakdown if requested
            if include_details and total_tickets > 0:
                detail_query = """
                    SELECT 
                        product_type,
                        COUNT(*) as ticket_count,
                        AVG(resolution_time_hours) as avg_resolution_hours,
                        COUNT(CASE WHEN ticket_status = 'open' THEN 1 END) as open_count
                    FROM analytics_marts.mart_ticket_analytics
                    WHERE is_v12_related = true
                    GROUP BY product_type
                    ORDER BY ticket_count DESC
                """
                
                cur.execute(detail_query)
                details = cur.fetchall()
                
                summary['product_breakdown'] = [
                    {
                        'product': row['product_type'],
                        'ticket_count': safe_int(row['ticket_count']),
                        'pct_of_total': round(safe_int(row['ticket_count']) * 100.0 / total_tickets, 1),
                        'avg_resolution_hours': round(safe_float(row['avg_resolution_hours']), 2),
                        'open_count': safe_int(row['open_count'])
                    }
                    for row in details
                ]
            
            cur.close()
        
        logger.info(f"v1.2 impact: {total_tickets} tickets, {still_open} still open")
        return summary
    
    except Exception as e:
        logger.error(f"Error in get_v12_impact_summary: {e}")
        raise Exception(f"v1.2 impact summary failed: {str(e)}")

# =====================================================
# Comparative Analysis
# =====================================================

def compare_periods(
    year1: int,
    month1: int,
    year2: int,
    month2: int,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Compare top root causes between two time periods
    
    Args:
        year1, month1: First period
        year2, month2: Second period
        top_n: Number of top causes to compare
    
    Returns:
        Comparative analysis
    """
    try:
        logger.info(f"Comparing {year1}-{month1} vs {year2}-{month2}")
        
        period1 = get_top_root_causes(year1, month1, top_n)
        period2 = get_top_root_causes(year2, month2, top_n)
        
        # Calculate changes
        period1_map = {rc['root_cause']: rc for rc in period1}
        period2_map = {rc['root_cause']: rc for rc in period2}
        
        all_causes = set(period1_map.keys()) | set(period2_map.keys())
        
        comparisons = []
        for cause in all_causes:
            p1 = period1_map.get(cause)
            p2 = period2_map.get(cause)
            
            if p1 and p2:
                ticket_change = p2['metrics']['total_tickets'] - p1['metrics']['total_tickets']
                pct_change = (ticket_change / p1['metrics']['total_tickets'] * 100) if p1['metrics']['total_tickets'] > 0 else 0
                
                comparisons.append({
                    'root_cause': cause,
                    'period1_tickets': p1['metrics']['total_tickets'],
                    'period2_tickets': p2['metrics']['total_tickets'],
                    'change': ticket_change,
                    'pct_change': round(pct_change, 1),
                    'trend': 'increasing' if ticket_change > 0 else 'decreasing' if ticket_change < 0 else 'stable'
                })
            elif p1:
                comparisons.append({
                    'root_cause': cause,
                    'period1_tickets': p1['metrics']['total_tickets'],
                    'period2_tickets': 0,
                    'change': -p1['metrics']['total_tickets'],
                    'pct_change': -100.0,
                    'trend': 'resolved'
                })
            else:  # p2
                comparisons.append({
                    'root_cause': cause,
                    'period1_tickets': 0,
                    'period2_tickets': p2['metrics']['total_tickets'],
                    'change': p2['metrics']['total_tickets'],
                    'pct_change': float('inf'),
                    'trend': 'new'
                })
        
        # Sort by absolute change
        comparisons.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return {
            'period1': f"{year1}-{month1:02d}",
            'period2': f"{year2}-{month2:02d}",
            'total_period1_tickets': sum(rc['metrics']['total_tickets'] for rc in period1),
            'total_period2_tickets': sum(rc['metrics']['total_tickets'] for rc in period2),
            'comparisons': comparisons
        }
    
    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise Exception(f"Period comparison failed: {str(e)}")

# =====================================================
# Quick Stats
# =====================================================

def get_quick_stats(year: int, month: int) -> Dict[str, Any]:
    """
    Get quick overview statistics for a time period
    
    Args:
        year: Year
        month: Month
    
    Returns:
        Quick stats summary
    """
    try:
        logger.info(f"Fetching quick stats for {year}-{month}")
        
        # Get top root causes
        root_causes = get_top_root_causes(year, month, top_n=5)
        
        # Get v1.2 impact
        v12_impact = get_v12_impact_summary()
        
        # Get churn summary
        churn = get_churn_summary(days=30)
        
        total_tickets = sum(rc['metrics']['total_tickets'] for rc in root_causes)
        
        return {
            'time_period': f"{year}-{month:02d}",
            'total_tickets': total_tickets,
            'top_root_cause': root_causes[0]['root_cause'] if root_causes else None,
            'top_root_cause_tickets': root_causes[0]['metrics']['total_tickets'] if root_causes else 0,
            'v12_impact': {
                'total_tickets': v12_impact['total_v12_tickets'],
                'still_open': v12_impact['still_open']
            },
            'churn': {
                'total_churned': churn['total_churned'],
                'clv_at_risk': churn['total_clv_at_risk']
            },
            'top_5_root_causes': [
                {
                    'name': rc['root_cause'],
                    'tickets': rc['metrics']['total_tickets'],
                    'severity': rc['severity']
                }
                for rc in root_causes[:5]
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        raise Exception(f"Quick stats failed: {str(e)}")

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TESTING ENHANCED KPI TOOLS")
    print("=" * 80)
    
    # Test 1: Top root causes with filters
    print("\n1. Testing top root causes with enhanced filters...")
    try:
        results = get_top_root_causes(
            year=2025, 
            month=10, 
            top_n=5,
            min_tickets=5
        )
        print(f"✅ Found {len(results)} root causes")
        for i, rc in enumerate(results[:3], 1):
            print(f"\n   #{i}: {rc['root_cause']} ({rc['severity']})")
            print(f"   Tickets: {rc['metrics']['total_tickets']} ({rc['metrics']['pct_of_period']}%)")
            print(f"   Open: {rc['metrics']['pct_open']}%")
            print(f"   Avg Resolution: {rc['metrics']['avg_resolution_hours']:.1f}h")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Churn summary with breakdown
    print("\n2. Testing churn summary with breakdown...")
    try:
        summary = get_churn_summary(days=30, include_breakdown=True)
        print(f"✅ Churn Summary (30 days):")
        print(f"   Total churned: {summary['total_churned']}")
        print(f"   Avg days inactive: {summary['avg_days_inactive']}")
        print(f"   CLV at risk: ${summary['total_clv_at_risk']:,.0f}")
        if 'risk_breakdown' in summary:
            print(f"   Risk Breakdown:")
            for level, data in summary['risk_breakdown'].items():
                print(f"     {level.capitalize()}: {data['count']} ({data['percentage']}%)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: v1.2 impact with details
    print("\n3. Testing v1.2 impact with details...")
    try:
        impact = get_v12_impact_summary(include_details=True)
        print(f"✅ v1.2 Impact:")
        print(f"   Total tickets: {impact['total_v12_tickets']}")
        print(f"   Still open: {impact['still_open']} ({impact['pct_still_open']}%)")
        print(f"   Resolved: {impact['pct_resolved']}%")
        if 'product_breakdown' in impact:
            print(f"   Top affected products:")
            for prod in impact['product_breakdown'][:3]:
                print(f"     {prod['product']}: {prod['ticket_count']} tickets ({prod['pct_of_total']}%)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Churn by segment
    print("\n4. Testing churn by segment...")
    try:
        segments = get_churn_by_segment()
        print(f"✅ Churn by Segment:")
        for seg in segments[:3]:
            print(f"   {seg['segment']}: {seg['churned_count']} customers, ${seg['avg_clv_at_risk']:,.0f} avg CLV")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Quick stats
    print("\n5. Testing quick stats...")
    try:
        stats = get_quick_stats(year=2025, month=10)
        print(f"✅ Quick Stats for {stats['time_period']}:")
        print(f"   Total tickets: {stats['total_tickets']}")
        print(f"   Top issue: {stats['top_root_cause']} ({stats['top_root_cause_tickets']} tickets)")
        print(f"   v1.2 tickets: {stats['v12_impact']['total_tickets']}")
        print(f"   Churned customers: {stats['churn']['total_churned']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Period comparison
    print("\n6. Testing period comparison...")
    try:
        comparison = compare_periods(2025, 9, 2025, 10, top_n=5)
        print(f"✅ Period Comparison:")
        print(f"   {comparison['period1']}: {comparison['total_period1_tickets']} tickets")
        print(f"   {comparison['period2']}: {comparison['total_period2_tickets']} tickets")
        print(f"   Top changes:")
        for comp in comparison['comparisons'][:3]:
            print(f"     {comp['root_cause']}: {comp['change']:+d} ({comp['trend']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)