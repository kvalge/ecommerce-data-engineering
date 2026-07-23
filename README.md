# E-Commerce Data Engineering

This project demonstrates the development of an end-to-end e-commerce data pipeline. The goal is to collect data from external sources, generate additional business data, store raw data, transform it into an analytical format, and prepare it for reporting and analysis.

The project uses Python for data ingestion, PostgreSQL for data storage, dbt for data transformation, and Airflow for workflow orchestration.

The data model represents a typical e-commerce business, including products, users, orders, and order items. The final analytical layer will provide insights into sales performance, customer behavior, and product performance.

## Data
Ingests data from products API, generates fake data of users, orders, order_items.

## Setup
pip install -r requirements.txt