# Progress

## Done

- Products ingestion: fetch products from FakeStore API (`src/ingestion/products.py`).
- Versioned fake data (SCD Type 2) for users, orders, order_items:
  - `id` = version row PK; `entity_id` = stable business key; `valid_from` / `valid_until` (NULL = current)
  - Helpers: create / change / drop in `users.py`, `orders.py`, `order_items.py`
  - Shared helpers in `src/ingestion/versioning.py`
- Real-life batch simulation (`src/ingestion/simulate_batch.py`): each run mixes new users/orders/items, profile/status changes, and soft-drops (order drop cascades to its current items).

## Next

- Store raw data in PostgreSQL (upsert products; append versions / close via `valid_until`).
