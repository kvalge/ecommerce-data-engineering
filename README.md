# E-Commerce Data Engineering

This project demonstrates the development of an end-to-end e-commerce data pipeline. The goal is to collect data from external sources, generate additional business data, store raw data, transform it into an analytical format, and prepare it for reporting and analysis.

The project uses Python for data ingestion, PostgreSQL for data storage, dbt for data transformation, and Airflow for workflow orchestration.

The data model represents a typical e-commerce business, including products, users, orders, and order items. The final analytical layer will provide insights into sales performance, customer behavior, and product performance.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
docker compose up -d
```

Copy `.env.example` to `.env` and adjust credentials if needed. Never commit `.env`. Postgres runs on the port set in `.env` (default `5432`).

Raw tables are defined in `sql/raw_schema.sql` (schema `raw`: `products`, `users`, `orders`, `order_items`). On first Postgres start, Docker applies that file automatically. If the database volume already exists, apply it manually:

```bash
docker compose exec -T postgres psql -U ecommerce -d ecommerce < sql/raw_schema.sql
```

DB connection helper: `src/storage/db.py` (reads `.env`, SQLAlchemy + psycopg2).

```bash
python src/storage/db.py
```

Load into raw tables: `src/storage/load.py` (`upsert_products`, `load_users` / `load_orders` / `load_order_items`).

```bash
python src/storage/load.py
```

Persist seed + simulated batches to Postgres:

```bash
python src/pipeline/run_batch.py
```

First run seeds when `raw.users` is empty; later runs load state from the DB, apply `simulate_batch`, and write closes/inserts.

### dbt (Docker)

dbt runs in Compose (no local `pip install dbt` needed). Project files live in `dbt/`; the container talks to Postgres as host `postgres` on port `5432` (Docker network).

```bash
docker compose up -d postgres
docker compose --profile dbt run --rm dbt debug
docker compose --profile dbt run --rm dbt run --select staging
docker compose --profile dbt run --rm dbt run
docker compose --profile dbt run --rm dbt test
```

Staging views (from `raw.*`) land in schema `analytics`: `stg_products`, `stg_users`, `stg_orders`, `stg_order_items`.

```bash
docker compose --profile dbt run --rm dbt test --select staging
```

## Data
Ingests products from the FakeStore API (`src/ingestion/products.py`).

Generates versioned fake users, orders, and order_items (SCD Type 2):
- `id` — unique version row
- `entity_id` — stable id linking versions of the same entity
- `valid_from` / `valid_until` — version validity (`valid_until` is `NULL` while current)

Modules: `src/ingestion/users.py`, `orders.py`, `order_items.py`.  
Each simulation run mixes creates, updates, and soft-drops via `src/ingestion/simulate_batch.py` (old versions stay intact).

```bash
python src/ingestion/simulate_batch.py
```
