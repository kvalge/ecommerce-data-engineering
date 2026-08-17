# E-Commerce Data Engineering

Local end-to-end pipeline: **ingest → Postgres → dbt → Airflow**.

Products come from a public API; users/orders/items are simulated with history (SCD Type 2). dbt builds analysis tables; Airflow runs the job daily.

**New to data engineering?** Read [docs/pipeline.md](docs/pipeline.md) first — it explains each step and why it exists in plain language.

---

## What you get

| Stage | Output |
| --- | --- |
| Ingestion | Products from FakeStore API + fake users/orders/items |
| Storage | PostgreSQL schema `raw` |
| Transformation | dbt models in schema `analytics` (`stg_*` → `dim_*`/`fct_*` → `mart_*`) |
| Orchestration | Airflow DAG `ecommerce_pipeline` |

---

## Prerequisites

- Python 3.11+
- Docker Desktop (Compose)
- Copy of this repo

---

## Quick start (end-to-end)

### 1. Python deps and env file

```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

1. Set DB password/port if you want (defaults work).
2. Set **`COMPOSE_PROJECT_DIR`** to this repo’s absolute path using **forward slashes**, e.g.  
   `C:/Users/you/software_development/ecommerce-data-engineering`  
   (needed so Airflow can mount the `dbt/` folder when it runs dbt).

Never commit `.env`.

### 2. Start Postgres

```bash
docker compose up -d postgres
```

On **first** start, Docker applies `sql/raw_schema.sql` and `sql/init_airflow_db.sql`.  
If Postgres was created before those scripts existed:

```bash
docker compose exec -T postgres psql -U ecommerce -d ecommerce < sql/raw_schema.sql
docker compose exec -T postgres psql -U ecommerce -d postgres < sql/init_airflow_db.sql
```

Check the connection from the host:

```bash
python src/storage/db.py
```

### 3. Load a batch into `raw` (optional manual check)

```bash
python src/pipeline/run_batch.py
```

- First run: seeds data if `raw.users` is empty.  
- Later runs: load current state → simulate creates/updates/drops → write to Postgres.

### 4. Build analytics with dbt

```bash
docker compose --profile dbt run --rm dbt debug
docker compose --profile dbt run --rm dbt run
docker compose --profile dbt run --rm dbt test
```

Optional docs site:

```bash
docker compose --profile dbt run --rm dbt docs generate
```

### 5. Run the full stack with Airflow

```bash
docker compose --profile airflow build
docker compose --profile airflow up -d
```

- UI: http://localhost:8080  
- Login: values from `.env` (default `airflow` / `airflow`)

DAG **`ecommerce_pipeline`** (starts paused):

1. `ingest_and_load` — Python batch into `raw`  
2. `dbt_run` — rebuild models  
3. `dbt_test` — quality checks  

Schedule: daily · retries: 2 (5 minutes apart).

```bash
docker compose --profile airflow exec airflow-scheduler airflow dags unpause ecommerce_pipeline
docker compose --profile airflow exec airflow-scheduler airflow dags trigger ecommerce_pipeline
```

Or unpause/trigger in the UI.

---

## Project layout

```text
src/ingestion/     Pull products + generate SCD2 users/orders/items
src/storage/       Postgres helpers (connect, load, read)
src/pipeline/      run_batch.py — one full load step
sql/               Schema + Airflow DB bootstrap
dbt/               Staging, intermediate, marts
airflow/           DAGs and Airflow config
docs/pipeline.md   Plain-language walkthrough of the pipeline
```

---

## Data model (short)

| Entity | Source | History |
| --- | --- | --- |
| Products | FakeStore API | Upsert by product id |
| Users / orders / order items | Faker + simulation | SCD2 (`entity_id`, `valid_from`, `valid_until`) |

Simulation mixes **creates**, **updates**, and **soft-drops** each batch (`src/ingestion/simulate_batch.py`).

Analytics layers:

`raw` → `analytics.stg_*` → `analytics.dim_*` / `fct_*` → `analytics.mart_sales` / `mart_customers` / `mart_products`

---

## Useful commands

| Goal | Command |
| --- | --- |
| One batch load | `python src/pipeline/run_batch.py` |
| dbt only | `docker compose --profile dbt run --rm dbt run` |
| dbt tests | `docker compose --profile dbt run --rm dbt test` |
| Start Airflow | `docker compose --profile airflow up -d` |
| Stop Airflow | `docker compose --profile airflow down` |
| Stop Postgres | `docker compose down` |

---

## Notes

- Host Postgres port comes from `.env` (`POSTGRES_PORT`; this machine often uses `5433` if `5432` is taken). Inside Docker, services still talk to `postgres:5432`.
- Airflow metadata uses a separate database (`airflow`) on the same Postgres container as the shop data (`ecommerce`).
- More detail and “why” for each step: [docs/pipeline.md](docs/pipeline.md).
