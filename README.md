# E-Commerce Data Engineering

This project demonstrates the development of an end-to-end e-commerce data pipeline. The goal is to collect data from external sources, generate additional business data, store raw data, transform it into an analytical format, and prepare it for reporting and analysis.

The project uses Python for data ingestion, PostgreSQL for data storage, dbt for data transformation, and Airflow for workflow orchestration.

The data model represents a typical e-commerce business, including products, users, orders, and order items. The final analytical layer will provide insights into sales performance, customer behavior, and product performance.

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

## Setup
pip install -r requirements.txt
