-- models/staging/stg_tickets.sql
-- Staging model for tickets - clean and standardize raw ticket data

{{
    config(
        materialized='view',
        tags=['staging', 'tickets']
    )
}}

with source_data as (
    select * from {{ source('analytics', 'fact_tickets') }}
),

cleaned as (
    select
        -- IDs
        ticket_id,
        ticket_number,
        customer_id,
        product_id,
        category_id,
        root_cause_id,
        
        -- Ticket attributes
        lower(trim(ticket_status)) as ticket_status,
        lower(trim(priority)) as priority,
        trim(subject) as subject,
        trim(description) as description,
        
        -- Dates
        created_date,
        resolved_date,
        closed_date,
        
        -- Metrics
        resolution_time_hours,
        customer_satisfaction_score,
        
        -- Technical details
        lower(trim(channel)) as channel,
        lower(trim(app_version)) as app_version,
        trim(assigned_to) as assigned_to,
        
        -- Metadata
        created_at,
        updated_at,
        
        -- Derived fields
        case 
            when ticket_status in ('resolved', 'closed') then true 
            else false 
        end as is_resolved,
        
        case 
            when customer_satisfaction_score >= 4 then 'satisfied'
            when customer_satisfaction_score >= 2 then 'neutral'
            when customer_satisfaction_score is not null then 'unsatisfied'
            else 'no_feedback'
        end as satisfaction_level,
        
        case
            when resolution_time_hours <= 24 then 'fast'
            when resolution_time_hours <= 72 then 'normal'
            when resolution_time_hours > 72 then 'slow'
            else 'unresolved'
        end as resolution_speed
        
    from source_data
)

select * from cleaned