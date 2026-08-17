-- Current user snapshot (one row per user_id).
select
    user_id,
    user_version_id,
    first_name,
    last_name,
    email,
    telephone,
    age,
    gender,
    city,
    registration_date,
    valid_from as effective_from
from {{ ref('stg_users') }}
where is_current
