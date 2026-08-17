-- Fails if any order_item_id has more than one current version.
select
    order_item_id,
    count(*) as current_versions
from {{ ref('stg_order_items') }}
where is_current
group by order_item_id
having count(*) > 1
