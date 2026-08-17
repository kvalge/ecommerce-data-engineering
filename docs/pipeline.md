# How this pipeline works

This document explains the project in plain language: what each part does, why it exists, and how data moves from “source-like rows” to “tables you can analyze.”

If you are comfortable with analytics but new to data engineering, start here. For commands to run everything, see [README.md](../README.md).

---

## What problem does this solve?

An online shop needs answers like:

- How much revenue did we make last week?
- Which products sell best?
- Who are our most valuable customers?

Those answers need **clean, trusted tables**. Getting there usually means:

1. **Collect** data (APIs, apps, or fake demo data in this project)
2. **Store** it safely (so history is not lost)
3. **Transform** it step by step into analysis-ready tables
4. **Run** those steps on a schedule, with quality checks

That whole path is the **data pipeline**.

---

## Big picture

```text
  FakeStore API          Faker (demo users/orders)
        │                         │
        └────────────┬────────────┘
                     ▼
         Python batch (Docker)
         ingest + simulate + load
                     │
                     ▼
           PostgreSQL  schema `raw`
              products, users, orders, order_items
                     │
                     ▼
                dbt (Docker)  →  schema `analytics`
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      staging   intermediate    marts
      (stg_*)    (dim_*/fct_*)  (mart_*)
         │           │           │
         │      star schema      │
         │   (clean building     │
         │    blocks)            │
         └───────────┴───────────┘
                     ▲
                     │
              Airflow DAG (daily)
     pipeline image → dbt run → dbt test
```

| Stage | Tool | Role in one sentence |
| --- | --- | --- |
| Ingestion | Python (`Dockerfile.python`) | Bring data in and simulate realistic changes |
| Storage | PostgreSQL schema `raw` | Keep source-like history |
| Transform — staging | dbt | Light clean / rename of each raw table |
| Transform — intermediate | dbt | Dimensions + facts (star schema, history-aware joins) |
| Transform — marts | dbt | Business-ready aggregates for reporting |
| Orchestration | Airflow (`Dockerfile.airflow`) | Run the steps in order, every day |

---

## Step 1 — Bring data in (Python in Docker)

**Where:** `src/ingestion/`, `src/pipeline/run_batch.py`, `Dockerfile.python`

The batch job runs in a small Python container (Compose profile `pipeline`). Airflow starts the same image with `docker run` on the shared Docker network. No local virtualenv is required.

### Products (external API)

Products come from the public [FakeStore API](https://fakestoreapi.com/).  
**Why:** Practice pulling from an external source, not only inventing everything.

### Users, orders, order items (generated)

Users, orders, and line items are created with the Faker library so we have a full shop story without a real production database.  
**Why:** Lets us practice versioning, joins, and marts end-to-end locally.

### History when things change (SCD Type 2)

Customer email changes, order status updates, items get cancelled. If you overwrite the old row, you lose history.

This project keeps history with **slowly changing dimensions type 2 (SCD2)**:

| Column | Meaning |
| --- | --- |
| `entity_id` | Stable business id (the same person/order forever) |
| `id` | Id of **this version** of the row |
| `valid_from` / `valid_until` | When this version was active (`valid_until` is NULL while it is current) |

**Why:** You can answer both “what is true **now**?” and “what was true **on the order date**?”

Each batch (`simulate_batch`) mixes creates, updates, and soft-deletes so the data behaves more like a live system.

---

## Step 2 — Store raw data (PostgreSQL)

**Where:** `sql/raw_schema.sql`, `src/storage/`

Raw tables live in schema **`raw`**:

| Table | Contents |
| --- | --- |
| `raw.products` | Product catalog (upserted by product id) |
| `raw.users` | User history (SCD2) |
| `raw.orders` | Order history (SCD2) |
| `raw.order_items` | Line-item history (SCD2) |

**Why a separate “raw” layer?**

- Protects the landing zone (closest to the source)
- dbt models can be rebuilt without re-ingesting
- Easier debugging: “Is the bug in the load, or in a transform?”

Docker Compose starts Postgres and applies the schema on first boot.

---

## Step 3 — Transform with dbt (three layers)

**Where:** `dbt/models/`, `Dockerfile.dbt`

dbt is SQL organized as a project. Everything below lands in schema **`analytics`**.

We intentionally use **three layers**, not one big SQL dump. Each layer has one job.

```text
raw.*  →  staging (stg_*)  →  intermediate (dim_*/fct_*)  →  marts (mart_*)
              clean                building blocks              reports
```

### 3a. Staging (`dbt/models/staging/`) — clean the source

**Job:** Make each raw table pleasant to use. Almost no business logic yet.

| Model | Built from | What it does |
| --- | --- | --- |
| `stg_products` | `raw.products` | Rename/cast catalog fields |
| `stg_users` | `raw.users` | Rename ids, cast types, add `is_current` |
| `stg_orders` | `raw.orders` | Same pattern for orders |
| `stg_order_items` | `raw.order_items` | Same pattern + `line_total` (qty × price) |

Examples of staging work:

- `entity_id` → clearer names like `user_id` / `order_id`
- `id` → `user_version_id` (this version of the row)
- `is_current` = (`valid_until` is null)
- Types cast to date/integer/etc.

Staging models are **views** (always reflect latest `raw`).

**Why staging exists:** Every later model should read `stg_*`, not `raw.*`, so renaming and casting happen once.

---

### 3b. Intermediate (`dbt/models/intermediate/`) — star schema building blocks

**Job:** Turn cleaned sources into a simple **star schema**: dimensions (who/what) and facts (what happened).

This is the layer that was easy to skip in docs — but it is the bridge between “cleaned source tables” and “dashboard metrics.”

| Model | Type | Meaning |
| --- | --- | --- |
| `dim_products` | Dimension | One row per product (catalog) |
| `dim_users` | Dimension | One row per **current** user profile |
| `fct_orders` | Fact | One row per **current** order, with user attributes **as of `order_date`** |
| `fct_order_items` | Fact | One row per **current** line item (with order context needed for sales) |

**Dimension vs fact (plain language):**

- **Dimension** — describes an entity you filter or group by (customer, product).
- **Fact** — a measurable event or line (an order, a line item, revenue).

**Why intermediate exists:**

- Marts should stay thin: “sum revenue by city,” not “figure out SCD2 joins again.”
- Dims/facts are reusable: several marts can share `fct_order_items`.
- History-aware logic lives in one place (especially orders ↔ users).

#### As-of join (why `fct_orders` is special)

A user’s city or email may change **after** they placed an order. For analysis of that order, we usually want the profile that was valid **on the order date**, not today’s profile.

`fct_orders` joins current orders to user **versions** where:

`valid_from ≤ order_date < valid_until` (or still open if `valid_until` is null)

So you get fields like `user_email_at_order`, `user_city_at_order`, etc.

`dim_users` is different: it keeps only **`is_current`** rows — useful for “who is this customer **now**?” (e.g. customer mart).

Intermediate models are **tables** (materialized for join performance).

---

### 3c. Marts (`dbt/models/marts/`) — tables for people and dashboards

**Job:** Answer common business questions with ready-made aggregates. Prefer querying these from BI tools.

| Model | Question it helps answer | Built mainly from |
| --- | --- | --- |
| `mart_sales` | Sales by date / city / status | `fct_order_items` |
| `mart_customers` | Orders and lifetime value per customer | `dim_users` + facts |
| `mart_products` | Units, revenue, order coverage per product | `dim_products` + `fct_order_items` |

Marts are **tables**.

**Why marts exist:** Analysts should not rewrite star-schema joins for every report. One trusted mart per use case.

---

### Tests

dbt also runs **tests** (not null, unique, relationships, and “one current row per entity” where needed) so bad data fails loudly instead of quietly wrong dashboards.

---

## Step 4 — Orchestrate with Airflow

**Where:** `airflow/dags/ecommerce_pipeline.py`, `Dockerfile.airflow`

Airflow does not transform the data itself. It **schedules and watches** sibling containers:

1. Python pipeline image — ingest / simulate / load into `raw`
2. dbt image — `dbt run` (rebuild staging → intermediate → marts)
3. dbt image — `dbt test` (quality rules)

**Why:** One place for success/failure, retries, and a daily schedule.

The DAG starts **paused** so nothing runs until you unpause it.

---

## How a daily run feels in practice

1. New and changed shop activity is written to `raw` (history preserved).
2. dbt rebuilds **staging → intermediate → marts** in `analytics`.
3. Tests confirm keys and relationships still look sane.
4. You (or a dashboard) read from `mart_*` tables.

---

## Project map (folders that matter)

| Path | What it is |
| --- | --- |
| `src/ingestion/` | API pull + fake SCD2 data + batch simulation |
| `src/storage/` | Postgres connection, load, and read helpers |
| `src/pipeline/` | `run_batch.py` — one full load step |
| `Dockerfile.python` | Image for the Python batch |
| `Dockerfile.dbt` | Image for dbt |
| `Dockerfile.airflow` | Airflow (+ Docker CLI for sibling runs) |
| `sql/` | Database bootstrap scripts |
| `dbt/models/staging/` | `stg_*` cleaned sources |
| `dbt/models/intermediate/` | `dim_*` / `fct_*` star schema |
| `dbt/models/marts/` | `mart_*` reporting tables |
| `airflow/` | DAGs and Airflow config |
| `docker-compose.yml` | Local Postgres, pipeline, dbt, Airflow |
| `docs/pipeline.md` | This explanation |

Generated junk (dbt `target/`, Airflow logs, `.env`) stays out of git via `.gitignore`.

---

## Glossary (short)

| Term | Plain meaning |
| --- | --- |
| **ETL / ELT** | Move and reshape data; here we **load raw first**, then transform with dbt (ELT-style) |
| **Raw** | Closest to the source; keep history |
| **Staging** | Cleaned, standardized source tables (`stg_*`) |
| **Intermediate** | Reusable dims/facts between staging and marts (`dim_*`, `fct_*`) |
| **Star schema** | Facts in the middle, dimensions around them — common analytics shape |
| **Dimension** | Descriptive entity (user, product) |
| **Fact** | Measurable event/line (order, order item) |
| **Mart** | Business-facing table for analysis (`mart_*`) |
| **DAG** | Airflow workflow (“do A, then B, then C”) |
| **SCD2** | Keep old versions of a record with validity dates |
| **As-of / point-in-time join** | Attach the dimension version that was valid on the event date |

---

## What this project is (and is not)

**It is:** a local learning stack that shows a full path from ingestion to trusted marts, including an explicit intermediate (star schema) layer.

**It is not:** a production shop with real PII, high availability, or a cloud warehouse. Credentials live in `.env` for local demo only.
