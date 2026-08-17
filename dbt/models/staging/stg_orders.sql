with source as (
    select * from {{ source('raw', 'orders') }}
)

select
    id as order_version_id,
    entity_id as order_id,
    user_id,
    order_date::date as order_date,
    status as order_status,
    payment_method,
    shipping_city,
    valid_from,
    valid_until,
    (valid_until is null) as is_current
from source
