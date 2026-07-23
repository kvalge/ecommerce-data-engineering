# Progress

## Done

- Products ingestion: fetch products from FakeStore API (`src/ingestion/products.py`).
- Users generator: Faker-based fake users with schema fields id, first_name, last_name, email, telephone, age, gender, city, registration_date (`src/ingestion/users.py`).
- Orders generator: Faker-based fake orders with schema fields id, user_id, order_date, status, payment_method, shipping_city (`src/ingestion/orders.py`).
- Order items generator: Faker-based fake order_items with schema fields id, order_id, product_id, quantity, unit_price (`src/ingestion/order_items.py`).

## Next

- Store raw data in PostgreSQL.
