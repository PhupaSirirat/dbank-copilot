-- models/marts/mart_ticket_analytics.sql
-- Comprehensive ticket analytics mart with all dimensions joined

{{
    config(
        materialized='table',
        tags=['marts', 'tickets', 'analytics']
    )
}}

with tickets as (
    select * from {{ ref('stg_tickets') }}
),

customers as (
    select * from {{ source('analytics', 'dim_customers') }}
),

products as (
    select * from {{ source('analytics', 'dim_products') }}
),

categories as (
    select * from {{ source('analytics', 'dim_ticket_categories') }}
),

root_causes as (
    select * from {{ source('analytics', 'dim_root_causes') }}
),

time_dim as (
    select * from {{ source('analytics', 'dim_time') }}
)

select
    -- Ticket identifiers
    t.ticket_id,
    t.ticket_number,
    t.ticket_status,
    t.priority,
    t.is_resolved,
    t.satisfaction_level,
    t.resolution_speed,
    
    -- Customer dimension
    c.customer_uuid,
    c.customer_segment,
    c.account_status,
    c.city,
    c.registration_date,
    
    -- Product dimension
    p.product_code,
    p.product_name,
    p.product_category,
    p.product_type,
    
    -- Category dimension
    cat.category_code,
    cat.category_name,
    cat.parent_category,
    
    -- Root cause dimension
    rc.root_cause_code,
    rc.root_cause_name,
    rc.category as root_cause_category,
    rc.severity as root_cause_severity,
    
    -- Time dimensions
    td.date as created_date,
    td.year as created_year,
    td.month as created_month,
    td.month_name as created_month_name,
    td.quarter as created_quarter,
    td.week as created_week,
    td.day_name as created_day_name,
    td.is_weekend as created_on_weekend,
    
    -- Ticket details
    t.subject,
    t.channel,
    t.app_version,
    
    -- Metrics
    t.resolution_time_hours,
    t.customer_satisfaction_score,
    
    -- Dates
    t.created_date as ticket_created_date,
    t.resolved_date,
    t.closed_date,
    
    -- Calculated metrics
    case 
        when t.resolved_date is not null 
        then extract(epoch from (t.resolved_date::timestamp - t.created_date::timestamp))/3600 
    end as actual_resolution_hours,
    
    case 
        when t.app_version = 'v1.2' and t.created_date >= '2024-08-15' 
        then true 
        else false 
    end as is_v12_related,
    
    current_timestamp as dbt_updated_at

from tickets t
left join customers c on t.customer_id = c.customer_id
left join products p on t.product_id = p.product_id
left join categories cat on t.category_id = cat.category_id
left join root_causes rc on t.root_cause_id = rc.root_cause_id
left join time_dim td on t.created_date = td.date