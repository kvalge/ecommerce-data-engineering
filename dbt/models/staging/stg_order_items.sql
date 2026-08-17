with source as (
    select * from {{ source('raw', 'order_items') }}
)

select
    id as order_item_version_id,
    entity_id as order_item_id,
    order_id,
    product_id,
    quantity::integer as quantity,
    unit_price::numeric(12, 2) as unit_price,
    (quantity::integer * unit_price::numeric(12, 2)) as line_total,
    valid_from,
    valid_until,
    (valid_until is null) as is_current
from source
