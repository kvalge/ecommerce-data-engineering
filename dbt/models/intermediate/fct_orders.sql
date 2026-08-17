-- Current orders with user attributes as-of order_date (SCD2 point-in-time).
with orders as (
    select *
    from {{ ref('stg_orders') }}
    where is_current
),

users as (
    select *
    from {{ ref('stg_users') }}
)

select
    o.order_id,
    o.order_version_id,
    o.user_id,
    o.order_date,
    o.order_status,
    o.payment_method,
    o.shipping_city,
    u.user_version_id as user_version_id_at_order,
    u.email as user_email_at_order,
    u.city as user_city_at_order,
    u.age as user_age_at_order,
    u.gender as user_gender_at_order
from orders as o
left join users as u
    on o.user_id = u.user_id
    and u.valid_from::date <= o.order_date
    and (u.valid_until is null or u.valid_until::date > o.order_date)
