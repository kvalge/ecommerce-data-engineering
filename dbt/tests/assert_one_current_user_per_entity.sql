-- Fails if any user_id has more than one current version.
select
    user_id,
    count(*) as current_versions
from {{ ref('stg_users') }}
where is_current
group by user_id
having count(*) > 1
