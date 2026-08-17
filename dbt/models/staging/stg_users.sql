with source as (
    select * from {{ source('raw', 'users') }}
)

select
    id as user_version_id,
    entity_id as user_id,
    first_name,
    last_name,
    email,
    telephone,
    age::integer as age,
    gender,
    city,
    registration_date::date as registration_date,
    valid_from,
    valid_until,
    (valid_until is null) as is_current
from source
