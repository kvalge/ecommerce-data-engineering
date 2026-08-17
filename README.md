# E-Commerce Data Engineering

Local end-to-end pipeline: **ingest → Postgres → dbt → Airflow**, all runnable with Docker.

Products come from a public API; users/orders/items are simulated with history (SCD Type 2). dbt builds analysis tables; Airflow runs the job daily.

**New to data engineering?** Read [docs/pipeline.md](docs/pipeline.md) first — it explains each step and why it exists in plain language.

---

## What you get

| Stage | Tool | Output |
| --- | --- | --- |
| Ingestion | Python (Docker) | Products + fake users/orders/items into `raw` |
| Storage | PostgreSQL | Schema `raw` |
| Transformation | dbt (Docker) | Schema `analytics` (`stg_*` → `dim_*`/`fct_*` → `mart_*`) |
| Orchestration | Airflow (Docker) | DAG `ecommerce_pipeline` |

---

## Prerequisites

- Docker Desktop (Compose)
- Copy of this repo

A local Python install is **optional** (only if you prefer running scripts on the host).

---

## Quick start (Docker end-to-end)

### 1. Env file

```bash
cp .env.example .env
```

Edit `.env`:

1. Adjust DB password/port if you want (defaults work).
2. Set **`COMPOSE_PROJECT_DIR`** to this repo’s absolute path using **forward slashes**, e.g.  
   `C:/Users/you/software_development/ecommerce-data-engineering`  
   (Airflow uses this to mount `src/` and `dbt/` into sibling containers).

Never commit `.env`.

### One command: build everything and start the stack

Builds the Python, dbt, and Airflow images, then starts **Postgres + Airflow** (the long-running services). Pipeline and dbt stay available as images for manual runs and for the Airflow DAG.

```bash
docker compose --profile pipeline --profile dbt --profile airflow build && docker compose --profile airflow up -d
```

- UI: http://localhost:8080 (default login `airflow` / `airflow`)
- Unpause and trigger DAG `ecommerce_pipeline` in the UI, or:

```bash
docker compose --profile airflow exec airflow-scheduler airflow dags unpause ecommerce_pipeline
docker compose --profile airflow exec airflow-scheduler airflow dags trigger ecommerce_pipeline
```

Stop everything:

```bash
docker compose --profile airflow down
```

### Step by step (same stack, more detail)

#### 1. Start Postgres only

```bash
docker compose up -d postgres
```

On **first** start, Docker applies `sql/raw_schema.sql` and `sql/init_airflow_db.sql`.  
If Postgres was created before those scripts existed:

```bash
docker compose exec -T postgres psql -U ecommerce -d ecommerce < sql/raw_schema.sql
docker compose exec -T postgres psql -U ecommerce -d postgres < sql/init_airflow_db.sql
```

#### 2. Run a Python batch (Docker)

```bash
docker compose --profile pipeline build
docker compose --profile pipeline run --rm pipeline
```

- First run: seeds data if `raw.users` is empty.
- Later runs: load state → simulate creates/updates/drops → write to Postgres.

Check DB connectivity the same way:

```bash
docker compose --profile pipeline run --rm pipeline python src/storage/db.py
```

#### 3. Build analytics with dbt

```bash
docker compose --profile dbt build
docker compose --profile dbt run --rm dbt debug
docker compose --profile dbt run --rm dbt run
docker compose --profile dbt run --rm dbt test
```

#### 4. Orchestrate with Airflow

```bash
docker compose --profile pipeline --profile dbt --profile airflow build
docker compose --profile airflow up -d
```

DAG **`ecommerce_pipeline`** (starts paused):

1. `ingest_and_load` — `docker run` the Python pipeline image  
2. `dbt_run` — `docker run` the dbt image  
3. `dbt_test` — dbt tests  

Schedule: daily · retries: 2 (5 minutes apart).

---

## Optional: run Python on the host

```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python src/pipeline/run_batch.py
```

Use host `POSTGRES_HOST` / `POSTGRES_PORT` from `.env` (often `localhost` and `5433`).

---

## Project layout

```text
src/ingestion/          Pull products + generate SCD2 users/orders/items
src/storage/            Postgres helpers (connect, load, read)
src/pipeline/           run_batch.py — one full load step
Dockerfile.python       Python batch image
Dockerfile.dbt          dbt image (based on dbt-postgres 1.8.2)
Dockerfile.airflow      Airflow image (+ Docker CLI for sibling runs)
sql/                    Schema + Airflow DB bootstrap
dbt/                    Staging, intermediate, marts
airflow/                DAGs and Airflow config
docs/pipeline.md        Plain-language walkthrough
```

---

## Data model (short)

| Entity | Source | History |
| --- | --- | --- |
| Products | FakeStore API | Upsert by product id |
| Users / orders / order items | Faker + simulation | SCD2 (`entity_id`, `valid_from`, `valid_until`) |

Analytics layers:

`raw` → `analytics.stg_*` → `analytics.dim_*` / `fct_*` → `analytics.mart_sales` / `mart_customers` / `mart_products`

---

## Useful commands

| Goal | Command |
| --- | --- |
| Start full stack | `docker compose --profile pipeline --profile dbt --profile airflow build && docker compose --profile airflow up -d` |
| One batch load | `docker compose --profile pipeline run --rm pipeline` |
| dbt run | `docker compose --profile dbt run --rm dbt run` |
| dbt tests | `docker compose --profile dbt run --rm dbt test` |
| Start Airflow | `docker compose --profile airflow up -d` |
| Stop stack | `docker compose --profile airflow down` |
| Stop Postgres only | `docker compose down` |

---

## Notes

- Host Postgres port comes from `.env` (`POSTGRES_PORT`). Inside Docker, services talk to `postgres:5432`.
- Airflow metadata uses DB `airflow` on the same Postgres container as shop data (`ecommerce`).
- More detail: [docs/pipeline.md](docs/pipeline.md).
