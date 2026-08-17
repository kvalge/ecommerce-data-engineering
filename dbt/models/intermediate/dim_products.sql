select
    product_id,
    product_name,
    unit_price as list_price,
    category,
    description,
    image_url,
    rating_rate,
    rating_count
from {{ ref('stg_products') }}
