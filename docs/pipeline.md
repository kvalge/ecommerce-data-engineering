# How this pipeline works

This document explains the project in plain language: what each part does, why it exists, and how data moves from “raw events” to “tables you can analyze.”

If you are comfortable with analytics but new to data engineering, start here. For commands to run everything, see [README.md](../README.md).

---

## What problem does this solve?

An online shop needs answers like:

- How much revenue did we make last week?
- Which products sell best?
- Who are our most valuable customers?

Those answers need **clean, trusted tables**. Getting there usually means:

1. **Collect** data (APIs, apps, fake demo data in this project)
2. **Store** it safely (so history is not lost)
3. **Transform** it into analysis-ready tables
4. **Run** those steps on a schedule, with checks

That whole path is the **data pipeline**.

---

## Big picture

```text
  FakeStore API          Faker (demo users/orders)
        │                         │
        └────────────┬────────────┘
                     ▼
         Python batch (Docker)
         (ingest + simulate + load)
                     │
                     ▼
           PostgreSQL schema `raw`
              (as landed / history)
                     │
                     ▼
                dbt (Docker)
         staging → dimensions/facts → marts
                     │
                     ▼
         PostgreSQL schema `analytics`
           (tables for reporting)
                     ▲
                     │
                 Airflow DAG
     (docker run pipeline → dbt run → dbt test)
```

| Layer | Tool | Role in one sentence |
| --- | --- | --- |
| Ingestion | Python in Docker | Bring data in and simulate realistic changes |
| Storage | PostgreSQL (`raw`) | Keep source-like history |
| Transformation | dbt in Docker | Clean, join, and build reporting tables |
| Orchestration | Airflow in Docker | Run the steps in order, every day |

---

## Step 1 — Bring data in (Python in Docker)

**Where:** `src/ingestion/`, `src/pipeline/run_batch.py`, `Dockerfile.python`

The batch job runs in a small Python container (Compose profile `pipeline`), same idea as dbt: no local virtualenv required. Airflow starts that image with `docker run` on the shared Docker network.

### Products (real-ish API)

Products come from the public [FakeStore API](https://fakestoreapi.com/).  
**Why:** Shows how to pull from an external source instead of only inventing everything.

### Users, orders, order items (generated)

Users, orders, and line items are created with the Faker library so we have a full shop story without a real production database.  
**Why:** Lets us practice versioning, joins, and marts end-to-end locally.

### History when things change (SCD Type 2)

Customer email changes, order status updates, items get cancelled. If you overwrite the old row, you lose history.

This project keeps history with **slowly changing dimensions type 2 (SCD2)**:

| Column | Meaning |
| --- | --- |
| `entity_id` | Stable “business” id (the same person/order forever) |
| `id` | Id of **this version** of the row |
| `valid_from` / `valid_until` | When this version was active (`valid_until` is empty/NULL while it is current) |

**Why:** Analysts can answer both “what is true now?” and “what was true on the order date?”

Each batch run (`simulate_batch`) mixes new records, updates, and soft-deletes so the data behaves more like a live system.

---

## Step 2 — Store raw data (PostgreSQL)

**Where:** `sql/raw_schema.sql`, `src/storage/`

Raw tables live in schema **`raw`**:

- `raw.products` — product catalog (upserted by product id)
- `raw.users`, `raw.orders`, `raw.order_items` — versioned history

**Why a separate “raw” layer?**

- Protects the original landing zone
- Transformations can be rebuilt without re-ingesting
- Debugging is easier: “Is the bug in the source load or in dbt?”

Docker Compose starts Postgres and applies the schema on first boot.

---

## Step 3 — Transform with dbt (analytics tables)

**Where:** `dbt/`

dbt is SQL plus a project structure. Models are built in layers:

### Staging (`stg_*`)

Light cleaning on top of `raw`: rename columns, cast types, flag `is_current`, compute `line_total`.  
**Why:** One consistent place to read “cleaned source” without business logic yet.

### Intermediate (`dim_*`, `fct_*`)

A simple **star-style** model:

- Dimensions: products, users (current profile)
- Facts: orders, order items (with user attributes **as of the order date** when history matters)

**Why:** Separates “entities we describe” from “events we measure,” which keeps reporting SQL simpler.

### Marts (`mart_*`)

Ready-to-use aggregates for common questions:

- `mart_sales` — sales by day / status / city-style slices
- `mart_customers` — customer lifetime-style metrics
- `mart_products` — product performance

**Why:** Analysts and BI tools should query marts, not dig through raw history every time.

Results land in schema **`analytics`**. dbt also runs **tests** (not null, unique, relationships) so bad data fails loudly.

---

## Step 4 — Orchestrate with Airflow

**Where:** `airflow/dags/ecommerce_pipeline.py`

Airflow does not transform the data itself here. It **schedules and watches** the job by starting sibling containers:

1. Python pipeline image — ingest / simulate / load into `raw`
2. dbt image — `dbt run` (rebuild analytics models)
3. dbt image — `dbt test` (quality rules)

**Why:** One place to see success/failure, retries, and daily cadence instead of remembering manual commands.

The DAG starts **paused** so nothing surprises you until you unpause it in the UI.

---

## How a daily run feels in practice

1. New and changed shop activity is written to `raw` (history preserved).
2. dbt rebuilds staging → dims/facts → marts in `analytics`.
3. Tests confirm keys and relationships still look sane.
4. You (or a dashboard) read from `mart_*` tables.

---

## Project map (folders that matter)

| Path | What it is |
| --- | --- |
| `src/ingestion/` | API pull + fake SCD2 data + batch simulation |
| `src/storage/` | Postgres connection, load, and read helpers |
| `src/pipeline/` | One entrypoint that seeds/loads a batch |
| `Dockerfile.python` | Image for the Python batch |
| `Dockerfile.dbt` | Image for dbt transforms |
| `Dockerfile.airflow` | Airflow (+ Docker CLI to run sibling images) |
| `sql/` | Database bootstrap scripts |
| `dbt/` | Transformation project (staging → marts) |
| `airflow/` | Orchestration (DAGs, logs, config) |
| `docker-compose.yml` | Local Postgres, dbt, and Airflow services |
| `docs/pipeline.md` | This explanation |

Generated junk (dbt `target/`, Airflow logs, `.env`) stays out of git via `.gitignore`.

---

## Glossary (short)

| Term | Plain meaning |
| --- | --- |
| **ETL / ELT** | Extract data, load it, transform it (order varies; this project loads raw first, then transforms with dbt) |
| **Raw** | Closest to the source; keep history |
| **Staging** | Cleaned, standardized source tables |
| **Mart** | Business-facing table for analysis |
| **DAG** | Airflow workflow graph (“do A, then B, then C”) |
| **SCD2** | Keep old versions of a record with validity dates |

---

## What this project is (and is not)

**It is:** a local learning stack that shows a full path from ingestion to trusted marts.

**It is not:** a production shop with real PII, high availability, or cloud warehouses. Credentials live in `.env` for local demo only.
