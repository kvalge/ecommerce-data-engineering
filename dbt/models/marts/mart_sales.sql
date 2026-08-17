{{ config(materialized='table') }}

-- Sales performance by order date, shipping city, and status.
select
    order_date,
    shipping_city,
    order_status,
    count(distinct order_id) as order_count,
    count(*) as line_item_count,
    sum(quantity) as units_sold,
    sum(line_total) as revenue
from {{ ref('fct_order_items') }}
group by
    order_date,
    shipping_city,
    order_status
