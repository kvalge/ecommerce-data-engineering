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

---

## Docker commands (order matters)

### `build` vs `up` vs `run`

| Command | When |
| --- | --- |
| **`build`** | First time, or after you change a `Dockerfile*` / `requirements.txt` |
| **`up -d`** | Start (or restart) long-running services: Postgres + Airflow |
| **`run --rm`** | One-off jobs: Python batch or dbt (not left running) |
| **`down`** | Stop containers (Postgres data volume is kept) |

You do **not** need `build` every time you start the project again.

### 1. First time only — env file

```bash
cp .env.example .env
```

Edit `.env`:

1. Defaults are fine for a local demo.
2. Set **`COMPOSE_PROJECT_DIR`** to this repo’s absolute path with **forward slashes**, e.g.  
   `C:/Users/you/software_development/ecommerce-data-engineering`

Never commit `.env`.

### 2. First time only — build custom images

```bash
docker compose --profile pipeline --profile dbt --profile airflow build
```

Builds **only** our project images (from Dockerfiles):

| Image | From |
| --- | --- |
| `ecommerce-pipeline` | `Dockerfile.python` |
| `ecommerce-dbt` | `Dockerfile.dbt` |
| `ecommerce-airflow` | `Dockerfile.airflow` |

This step does **not** create or start Postgres.

Postgres uses the public image `postgres:16` (no project Dockerfile). Docker **pulls** that image and **creates/starts** the Postgres container on the next step (`up -d`), the first time it is needed.

### 3. Start the stack (every time you want it running)

```bash
docker compose --profile airflow up -d
```

Creates and starts **containers**:

1. **Postgres** — pulls `postgres:16` if missing, creates container + data volume, applies `sql/*.sql` on first volume only  
2. **Airflow** — creates/starts Airflow containers (uses the image from step 2)

Pipeline and dbt stay as images until you `run` them or the DAG starts them.

- UI: http://localhost:8080 (default `airflow` / `airflow`)
- DAG `ecommerce_pipeline` starts **paused**. Unpause + trigger in the UI, or:

```bash
docker compose --profile airflow exec airflow-scheduler airflow dags unpause ecommerce_pipeline
docker compose --profile airflow exec airflow-scheduler airflow dags trigger ecommerce_pipeline
```

### 4. Stop the stack

```bash
docker compose --profile airflow down
```

Containers stop. **Database data stays** on the Docker volume.

### Already ran it before, then stopped?

Do **not** repeat env copy or `build`.

Just start again:

```bash
docker compose --profile airflow up -d
```

Rebuild only if you changed Dockerfiles or Python requirements:

```bash
docker compose --profile pipeline --profile dbt --profile airflow build
docker compose --profile airflow up -d
```

---

## Optional one-off jobs (stack can be up)

Postgres must be running (`up -d` above is enough).

| Goal | Command |
| --- | --- |
| One Python batch into `raw` | `docker compose --profile pipeline run --rm pipeline` |
| dbt models | `docker compose --profile dbt run --rm dbt run` |
| dbt tests | `docker compose --profile dbt run --rm dbt test` |

First batch **seeds** if `raw` is empty; later batches simulate creates/updates/drops.

---

## Project layout

```text
src/ingestion/          Pull products + generate SCD2 users/orders/items
src/storage/            Postgres helpers (connect, load, read)
src/pipeline/           run_batch.py — one full load step
Dockerfile.python       Python batch image
Dockerfile.dbt          dbt image
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

`raw` → `analytics.stg_*` → `analytics.dim_*` / `fct_*` → `analytics.mart_*`

---

## Notes

- Host Postgres port: `.env` → `POSTGRES_PORT`. Inside Docker: `postgres:5432`.
- Shop data DB: `ecommerce`. Airflow metadata DB: `airflow` (same Postgres container).
- Schema SQL runs automatically on **first** Postgres volume create only.
- More detail: [docs/pipeline.md](docs/pipeline.md).
