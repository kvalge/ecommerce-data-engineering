{{ config(materialized='table') }}

-- Customer behavior: lifetime activity per current user.
with order_stats as (
    select
        user_id,
        count(distinct order_id) as order_count,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from {{ ref('fct_orders') }}
    group by user_id
),

revenue_stats as (
    select
        user_id,
        sum(line_total) as lifetime_revenue,
        sum(quantity) as lifetime_units
    from {{ ref('fct_order_items') }}
    group by user_id
)

select
    u.user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.city,
    u.gender,
    u.age,
    u.registration_date,
    coalesce(o.order_count, 0) as order_count,
    o.first_order_date,
    o.last_order_date,
    coalesce(r.lifetime_revenue, 0) as lifetime_revenue,
    coalesce(r.lifetime_units, 0) as lifetime_units
from {{ ref('dim_users') }} as u
left join order_stats as o
    on u.user_id = o.user_id
left join revenue_stats as r
    on u.user_id = r.user_id
