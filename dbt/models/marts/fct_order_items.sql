-- Current order lines joined to fct_orders (inherits as-of user context).
with items as (
    select *
    from {{ ref('stg_order_items') }}
    where is_current
),

orders as (
    select *
    from {{ ref('fct_orders') }}
)

select
    i.order_item_id,
    i.order_item_version_id,
    i.order_id,
    i.product_id,
    i.quantity,
    i.unit_price,
    i.line_total,
    o.order_date,
    o.user_id,
    o.order_status,
    o.shipping_city,
    o.user_city_at_order,
    o.user_email_at_order
from items as i
inner join orders as o
    on i.order_id = o.order_id
