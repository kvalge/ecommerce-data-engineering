# Progress

## Goal

Build an end-to-end e-commerce data pipeline: ingest products from an external API and generate fake users/orders/order_items in Python, store raw data in PostgreSQL, transform it with dbt into analytical models, and orchestrate the workflow with Airflow (local services via Docker).

## Done

- Products ingestion from FakeStore API (`src/ingestion/products.py`).
- Versioned fake data (SCD Type 2) for users, orders, and order_items:
  - `id` = version row PK; `entity_id` = stable business key; `valid_from` / `valid_until` (`NULL` = current)
  - Create / change / drop helpers in `src/ingestion/users.py`, `orders.py`, `order_items.py`
  - Shared helpers in `src/ingestion/versioning.py`
- Real-life batch simulation (`src/ingestion/simulate_batch.py`): each run mixes new users/orders/items, profile/status changes, and soft-drops (order drop cascades to its current items).
- Local Postgres via Docker Compose (`docker-compose.yml`); DB placeholders in `.env.example`; local secrets in `.env` (gitignored).
- Raw Postgres schema (`sql/raw_schema.sql`): schema `raw` with `products` (upsert catalog) and SCD2 tables `users`, `orders`, `order_items`; unique partial indexes enforce one current row per `entity_id`.
- DB connection helper (`src/storage/db.py`): loads `.env`, builds SQLAlchemy engine with psycopg2 (`get_engine` / `get_connection`).
- Load functions (`src/storage/load.py`): `upsert_products` by `id`; `load_users` / `load_orders` / `load_order_items` close via `valid_until` then append new versions (re-run safe).
- Read helpers (`src/storage/read.py`): fetch raw tables and `is_seeded()`.
- Pipeline runner (`src/pipeline/run_batch.py`): upsert products; seed once if empty; otherwise load DB state → `simulate_batch` → persist.
- Manual verification: ran `run_batch` three times; current vs historical rows (`valid_until`) look correct.
- dbt via Docker: project in `dbt/` (`dbt_project.yml`, `profiles.yml`); Compose service `dbt` (`ghcr.io/dbt-labs/dbt-postgres:1.8.2`) connects to `postgres` on the Docker network; `dbt debug` OK.

## Next steps

Immediate next step: **8**.

### PostgreSQL raw storage

1. ~~Add Docker Compose for local Postgres; fill `.env.example` with DB placeholders; use `.env` for real credentials (never commit `.env`).~~
2. ~~Define raw schema for `products`, `users`, `orders`, `order_items` matching generated fields (including SCD2 columns where applicable).~~
3. ~~Add `src/storage/` with a DB connection helper (SQLAlchemy + psycopg2).~~
4. ~~Implement load functions: upsert products by `id`; for users/orders/order_items append new versions and close current rows via `valid_until` only.~~
5. ~~Wire a batch run to persist to Postgres (seed once, then `simulate_batch` writes to the DB).~~
6. ~~Manually verify after two runs: current rows (`valid_until IS NULL`) vs historical versions look correct.~~

### dbt transformation

7. ~~Initialize a dbt project and profile pointed at the same Postgres database.~~
8. Add staging models and sources for the four raw tables.
9. Add tests (`not_null`, `unique`, relationships) and enforce one current row per `entity_id` where applicable.
10. Build marts: dimension tables (`dim_users`, `dim_products`) and fact tables (`fct_orders` / `fct_order_items`) with as-of SCD2 joins.
11. Add analytical marts (sales, customer, product performance), `schema.yml` descriptions, and dbt docs.

### Airflow orchestration

12. Add Airflow via Docker Compose (share the stack with Postgres where practical).
13. Create a DAG: ingest/simulate → load Postgres → `dbt run` → `dbt test`; add schedule and retries.

### Docs polish

14. Update `README.md` with end-to-end run instructions once the full stack works.
