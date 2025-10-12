-- models/marts/mart_churned_customers.sql
-- Customer churn analysis - no login in 30/90 days

{{
    config(
        materialized='table',
        tags=['marts', 'churn', 'customers']
    )
}}

with customers as (
    select * from {{ source('analytics', 'dim_customers') }}
),

login_activity as (
    select
        customer_id,
        max(login_date) as last_login_date,
        count(*) as total_logins,
        count(distinct login_date) as distinct_login_days,
        avg(session_duration_minutes) as avg_session_minutes,
        max(case when login_date >= current_date - interval '7 days' then 1 else 0 end) as active_last_7d,
        max(case when login_date >= current_date - interval '30 days' then 1 else 0 end) as active_last_30d,
        max(case when login_date >= current_date - interval '90 days' then 1 else 0 end) as active_last_90d
    from {{ source('analytics', 'fact_logins') }}
    where login_status = 'success'
    group by customer_id
),

product_holdings as (
    select
        customer_id,
        count(*) as total_products,
        sum(case when status = 'active' then 1 else 0 end) as active_products,
        sum(balance) as total_balance,
        max(activation_date) as last_product_activation
    from {{ source('analytics', 'fact_customer_products') }}
    group by customer_id
),

ticket_activity as (
    select
        customer_id,
        count(*) as total_tickets,
        sum(case when ticket_status = 'open' then 1 else 0 end) as open_tickets,
        max(created_date) as last_ticket_date,
        avg(customer_satisfaction_score) as avg_satisfaction
    from {{ source('analytics', 'fact_tickets') }}
    group by customer_id
)

select
    -- Customer info (with masked PII in final output)
    c.customer_uuid,
    c.customer_segment,
    c.account_status,
    c.city,
    c.registration_date,
    
    -- Login metrics
    coalesce(la.last_login_date, c.registration_date) as last_login_date,
    current_date - coalesce(la.last_login_date, c.registration_date) as days_since_login,
    coalesce(la.total_logins, 0) as total_logins,
    coalesce(la.distinct_login_days, 0) as distinct_login_days,
    coalesce(la.avg_session_minutes, 0) as avg_session_minutes,
    coalesce(la.active_last_7d, 0) as active_last_7d,
    coalesce(la.active_last_30d, 0) as active_last_30d,
    coalesce(la.active_last_90d, 0) as active_last_90d,
    
    -- Churn flags
    case 
        when la.last_login_date is null then true
        when current_date - la.last_login_date >= 30 then true
        else false
    end as is_churned_30d,
    
    case 
        when la.last_login_date is null then true
        when current_date - la.last_login_date >= 90 then true
        else false
    end as is_churned_90d,
    
    -- Churn risk score (0-100, higher = more risk)
    case
        when la.last_login_date is null then 100
        when current_date - la.last_login_date >= 90 then 90
        when current_date - la.last_login_date >= 60 then 70
        when current_date - la.last_login_date >= 30 then 50
        when current_date - la.last_login_date >= 14 then 30
        else 10
    end as churn_risk_score,
    
    case
        when current_date - coalesce(la.last_login_date, c.registration_date) >= 90 then 'critical'
        when current_date - coalesce(la.last_login_date, c.registration_date) >= 60 then 'high'
        when current_date - coalesce(la.last_login_date, c.registration_date) >= 30 then 'medium'
        when current_date - coalesce(la.last_login_date, c.registration_date) >= 14 then 'low'
        else 'active'
    end as churn_risk_level,
    
    -- Product metrics
    coalesce(ph.total_products, 0) as total_products,
    coalesce(ph.active_products, 0) as active_products,
    coalesce(ph.total_balance, 0) as total_balance,
    ph.last_product_activation,
    
    -- Ticket metrics
    coalesce(ta.total_tickets, 0) as total_tickets,
    coalesce(ta.open_tickets, 0) as open_tickets,
    ta.last_ticket_date,
    coalesce(ta.avg_satisfaction, 0) as avg_satisfaction,
    
    -- Customer lifetime value proxy
    case
        when c.customer_segment = 'premium' then 1000
        when c.customer_segment = 'standard' then 500
        else 100
    end * coalesce(ph.active_products, 0) as estimated_clv,
    
    current_timestamp as dbt_updated_at

from customers c
left join login_activity la on c.customer_id = la.customer_id
left join product_holdings ph on c.customer_id = ph.customer_id
left join ticket_activity ta on c.customer_id = ta.customer_id
where c.account_status = 'Active'