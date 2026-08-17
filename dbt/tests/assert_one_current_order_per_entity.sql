-- Fails if any order_id has more than one current version.
select
    order_id,
    count(*) as current_versions
from {{ ref('stg_orders') }}
where is_current
group by order_id
having count(*) > 1
