-- models/marts/mart_top_root_causes.sql
-- Aggregated root causes by time period - Powers the kpi.top_root_causes tool

{{
    config(
        materialized='table',
        tags=['marts', 'kpi', 'root_causes']
    )
}}

with ticket_analytics as (
    select * from {{ ref('mart_ticket_analytics') }}
),

aggregated as (
    select
        -- Time groupings
        created_year,
        created_month,
        created_month_name,
        created_quarter,
        
        -- Root cause dimensions
        root_cause_code,
        root_cause_name,
        root_cause_category,
        root_cause_severity,
        
        -- Category
        category_name,
        parent_category,
        
        -- Product
        product_category,
        
        -- Metrics
        count(*) as total_tickets,
        sum(case when ticket_status = 'open' then 1 else 0 end) as open_tickets,
        sum(case when ticket_status = 'closed' then 1 else 0 end) as closed_tickets,
        sum(case when is_resolved then 1 else 0 end) as resolved_tickets,
        
        -- Resolution metrics
        avg(resolution_time_hours) as avg_resolution_hours,
        percentile_cont(0.5) within group (order by resolution_time_hours) as median_resolution_hours,
        
        -- Satisfaction
        avg(customer_satisfaction_score) as avg_satisfaction_score,
        sum(case when satisfaction_level = 'satisfied' then 1 else 0 end) as satisfied_count,
        sum(case when satisfaction_level = 'unsatisfied' then 1 else 0 end) as unsatisfied_count,
        
        -- v1.2 related
        sum(case when is_v12_related then 1 else 0 end) as v12_related_tickets,
        
        -- Channels
        count(distinct case when channel = 'app' then ticket_id end) as app_channel_count,
        count(distinct case when channel = 'web' then ticket_id end) as web_channel_count,
        count(distinct case when channel = 'phone' then ticket_id end) as phone_channel_count
        
    from ticket_analytics
    group by 
        created_year,
        created_month,
        created_month_name,
        created_quarter,
        root_cause_code,
        root_cause_name,
        root_cause_category,
        root_cause_severity,
        category_name,
        parent_category,
        product_category
),

with_percentages as (
    select
        *,
        -- Calculate percentage of total tickets in period
        round(
            (total_tickets * 100.0) / sum(total_tickets) over (
                partition by created_year, created_month
            ), 
            2
        ) as pct_of_period,
        
        -- Calculate percentage open
        round(
            (open_tickets * 100.0) / nullif(total_tickets, 0), 
            2
        ) as pct_open,
        
        -- Calculate percentage v1.2 related
        round(
            (v12_related_tickets * 100.0) / nullif(total_tickets, 0), 
            2
        ) as pct_v12_related,
        
        -- Satisfaction rate
        round(
            (satisfied_count * 100.0) / nullif(satisfied_count + unsatisfied_count, 0), 
            2
        ) as satisfaction_rate,
        
        current_timestamp as dbt_updated_at
        
    from aggregated
)

select * from with_percentages
order by created_year desc, created_month desc, total_tickets desc