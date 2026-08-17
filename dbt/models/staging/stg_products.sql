with source as (
    select * from {{ source('raw', 'products') }}
)

select
    id as product_id,
    title as product_name,
    price::numeric(12, 2) as unit_price,
    description,
    category,
    image as image_url,
    rating_rate::numeric(3, 2) as rating_rate,
    rating_count::integer as rating_count
from source
