---
alwaysApply: true
---

## Core Rules

- With code writing, move on step by step, only on small step at a time.

## Code Quality

- Write clean, modular, and maintainable Python code.
- Writing code, prefer simplicity over complexity.
- Prefer small functions with single responsibility.
- Avoid duplication and hardcoded values where possible.
- Use type hints where reasonable.
- Add short, clear comments where they improve code understanding.
- Create relevant separate folders for code files.

## Project Consistency

- Keep `requirements.txt` updated whenever dependencies change.
- Keep `.env.example` updated with all required environment variables, using placeholder values (never real secrets).
- Keep `.gitignore` updated to exclude local files, caches, and sensitive data.
- Keep `README.md` updated when functionality or workflow changes.
- With every step made update docs\progress.md, what is done or changed.

## Security

- Store all sensitive environment variables (API keys, tokens, webhook URLs etc) in `.env`.
- Never commit `.env` to version control.
- Ensure `.env` is listed in `.gitignore`.

## Execution Safety

- Ensure scripts can be run manually without side effects on previous successful runs.

## Architecture

- Separate concerns.
- Follow best practicing of python, dbt and Airflow architecture.

## Overview

This project demonstrates the development of an end-to-end e-commerce data pipeline. The goal is to collect data from external sources, generate additional business data, store raw data, transform it into an analytical format, and prepare it for reporting and analysis.

The project uses Python for data ingestion, PostgreSQL for data storage, dbt for data transformation, and Airflow for workflow orchestration. And Docker for conteinerization.

The data model represents a typical e-commerce business, including products, users, orders, and order items. The final analytical layer will provide insights into sales performance, customer behavior, and product performance.

## Data
Ingests data from products API, using faker, generates fake data of users, orders, order_items.
Users: id, first_name, last_name, email, telephone, age, gender (M, W or not defined; may), city (Tallinn, Tartu, Narva, Pärnu, Viljandi, Võru, Kuressaare või Jõhvi), registration_date
Orders: id, user_id, order_date, status, payment_method, shipping_city (Tallinn, Tartu, Narva, Pärnu, või Jõhvi)
Order_Items: id, order_id, product_id, quantity, unit_price
