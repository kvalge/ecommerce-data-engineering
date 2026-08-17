{{ config(materialized='table') }}

-- Product performance: units and revenue per catalog product.
with product_stats as (
    select
        product_id,
        count(distinct order_id) as order_count,
        sum(quantity) as units_sold,
        sum(line_total) as revenue
    from {{ ref('fct_order_items') }}
    group by product_id
)

select
    p.product_id,
    p.product_name,
    p.category,
    p.list_price,
    p.rating_rate,
    p.rating_count,
    coalesce(s.order_count, 0) as order_count,
    coalesce(s.units_sold, 0) as units_sold,
    coalesce(s.revenue, 0) as revenue
from {{ ref('dim_products') }} as p
left join product_stats as s
    on p.product_id = s.product_id
