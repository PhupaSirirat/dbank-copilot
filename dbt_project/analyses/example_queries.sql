-- analyses/example_queries.sql
-- Example queries using the dbt marts
-- These demonstrate how to use the models for analytics

-- =====================================================
-- REQUIREMENT 1: Top 5 Root Causes
-- =====================================================

-- Top 5 root causes in the last 30 days
WITH recent_tickets AS (
    SELECT 
        root_cause_name,
        category_name,
        total_tickets,
        pct_of_period,
        pct_open,
        avg_resolution_hours,
        satisfaction_rate
    FROM {{ ref('mart_top_root_causes') }}
    WHERE created_year = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '30 days')
        AND created_month = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '30 days')
)
SELECT 
    root_cause_name,
    category_name,
    total_tickets,
    ROUND(pct_of_period, 1) || '%' as pct_of_total,
    ROUND(pct_open, 1) || '%' as pct_still_open,
    ROUND(avg_resolution_hours, 1) || ' hrs' as avg_resolution
FROM recent_tickets
ORDER BY total_tickets DESC
LIMIT 5;

-- =====================================================
-- REQUIREMENT 2: v1.2 Spike Analysis
-- =====================================================

-- Daily ticket volume showing v1.2 spike
SELECT 
    ticket_created_date,
    COUNT(*) as total_tickets,
    SUM(CASE WHEN app_version = 'v1.2' THEN 1 ELSE 0 END) as v12_tickets,
    ROUND(
        SUM(CASE WHEN app_version = 'v1.2' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as pct_v12,
    -- Moving average for baseline
    ROUND(
        AVG(COUNT(*)) OVER (
            ORDER BY ticket_created_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ),
        0
    ) as avg_7d_baseline,
    -- Anomaly detection
    CASE 
        WHEN COUNT(*) > AVG(COUNT(*)) OVER (
            ORDER BY ticket_created_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) * 1.5 THEN 'SPIKE'
        ELSE 'NORMAL'
    END as anomaly_status
FROM {{ ref('mart_ticket_analytics') }}
WHERE created_year = 2024 
    AND created_month >= 8
GROUP BY ticket_created_date
ORDER BY ticket_created_date;

-- Products affected by v1.2
SELECT 
    product_type,
    COUNT(*) as v12_tickets,
    ROUND(AVG(resolution_time_hours), 1) as avg_resolution_hrs,
    ROUND(
        SUM(CASE WHEN ticket_status = 'open' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as pct_still_open
FROM {{ ref('mart_ticket_analytics') }}
WHERE is_v12_related = true
GROUP BY product_type
ORDER BY v12_tickets DESC;

-- =====================================================
-- REQUIREMENT 3: Churned Customers SQL
-- =====================================================

-- Template: Customers with no login in last N days
-- This is the actual SQL the MCP tool will execute

-- 30-day churn
SELECT 
    customer_uuid,
    customer_segment,
    days_since_login,
    last_login_date,
    total_products,
    active_products,
    total_balance,
    churn_risk_level,
    estimated_clv
FROM {{ ref('mart_churned_customers') }}
WHERE is_churned_30d = true
ORDER BY estimated_clv DESC, days_since_login DESC;

-- 90-day churn
SELECT 
    customer_uuid,
    customer_segment,
    days_since_login,
    last_login_date,
    total_products,
    active_products,
    total_balance,
    churn_risk_level,
    estimated_clv
FROM {{ ref('mart_churned_customers') }}
WHERE is_churned_90d = true
ORDER BY estimated_clv DESC, days_since_login DESC;

-- =====================================================
-- ADDITIONAL USEFUL QUERIES
-- =====================================================

-- Customer segment performance
SELECT 
    customer_segment,
    COUNT(DISTINCT customer_uuid) as total_customers,
    SUM(CASE WHEN is_churned_30d THEN 1 ELSE 0 END) as churned_30d,
    SUM(CASE WHEN is_churned_90d THEN 1 ELSE 0 END) as churned_90d,
    ROUND(
        SUM(CASE WHEN is_churned_30d THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as churn_rate_30d_pct,
    AVG(churn_risk_score) as avg_risk_score,
    SUM(estimated_clv) as total_clv_at_risk
FROM {{ ref('mart_churned_customers') }}
GROUP BY customer_segment
ORDER BY churn_rate_30d_pct DESC;

-- Ticket trends by category
SELECT 
    category_name,
    created_year,
    created_month,
    created_month_name,
    total_tickets,
    pct_open,
    avg_resolution_hours,
    satisfaction_rate
FROM {{ ref('mart_top_root_causes') }}
WHERE created_year = 2024
ORDER BY created_year DESC, created_month DESC, total_tickets DESC;

-- High-value customers at risk
SELECT 
    customer_uuid,
    customer_segment,
    days_since_login,
    total_products,
    total_balance,
    estimated_clv,
    churn_risk_level,
    avg_satisfaction,
    open_tickets
FROM {{ ref('mart_churned_customers') }}
WHERE estimated_clv > 1000
    AND churn_risk_level IN ('high', 'critical')
ORDER BY estimated_clv DESC;

-- Product issue summary
SELECT 
    product_type,
    product_category,
    COUNT(*) as total_tickets,
    ROUND(AVG(resolution_time_hours), 1) as avg_resolution_hrs,
    ROUND(
        SUM(CASE WHEN ticket_status = 'open' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as pct_open,
    ROUND(AVG(customer_satisfaction_score), 2) as avg_satisfaction,
    SUM(CASE WHEN is_v12_related THEN 1 ELSE 0 END) as v12_related_count
FROM {{ ref('mart_ticket_analytics') }}
WHERE created_year = 2024
GROUP BY product_type, product_category
ORDER BY total_tickets DESC;

-- Time-based patterns (weekday vs weekend)
SELECT 
    CASE 
        WHEN created_on_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(*) as ticket_count,
    ROUND(AVG(resolution_time_hours), 1) as avg_resolution_hrs,
    ROUND(
        SUM(CASE WHEN ticket_status = 'open' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as pct_open
FROM {{ ref('mart_ticket_analytics') }}
WHERE created_year = 2024
GROUP BY CASE WHEN created_on_weekend THEN 'Weekend' ELSE 'Weekday' END;

-- Channel effectiveness
SELECT 
    channel,
    COUNT(*) as tickets,
    ROUND(AVG(resolution_time_hours), 1) as avg_resolution_hrs,
    ROUND(AVG(customer_satisfaction_score), 2) as avg_satisfaction,
    ROUND(
        SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        1
    ) as resolution_rate_pct
FROM {{ ref('mart_ticket_analytics') }}
GROUP BY channel
ORDER BY tickets DESC;