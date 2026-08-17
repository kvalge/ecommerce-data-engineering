"""Daily ecommerce pipeline: ingest/simulate/load → dbt run → dbt test."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

default_args = {
    "owner": "ecommerce",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

_PROJECT_DIR = os.environ.get(
    "COMPOSE_PROJECT_DIR",
    "/opt/airflow/compose_project",
)
_NETWORK = os.environ.get(
    "COMPOSE_NETWORK",
    "ecommerce-data-engineering_default",
)
_PIPELINE_IMAGE = os.environ.get("PIPELINE_IMAGE", "ecommerce-pipeline:latest")
_DBT_IMAGE = os.environ.get("DBT_IMAGE", "ecommerce-dbt:1.8.2")

_PIPELINE_CMD = (
    f"docker run --rm --network {_NETWORK} "
    f'-v "{_PROJECT_DIR}/src:/app/src" '
    f'-v "{_PROJECT_DIR}/.env:/app/.env:ro" '
    "-e POSTGRES_HOST=postgres "
    "-e POSTGRES_PORT=5432 "
    "-e POSTGRES_USER "
    "-e POSTGRES_PASSWORD "
    "-e POSTGRES_DB "
    "-e PYTHONPATH=/app/src "
    f"-w /app {_PIPELINE_IMAGE} "
    "python src/pipeline/run_batch.py"
)

_DBT_RUN_BASE = (
    f"docker run --rm --network {_NETWORK} "
    f'-v "{_PROJECT_DIR}/dbt:/usr/app" '
    "-e DBT_PROFILES_DIR=/usr/app "
    "-e DBT_HOST=postgres "
    "-e DBT_PORT=5432 "
    "-e POSTGRES_USER "
    "-e POSTGRES_PASSWORD "
    "-e POSTGRES_DB "
    f"-w /usr/app {_DBT_IMAGE}"
)

with DAG(
    dag_id="ecommerce_pipeline",
    description="Ingest/simulate → load Postgres → dbt run → dbt test",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["ecommerce", "dbt"],
) as dag:
    ingest_and_load = BashOperator(
        task_id="ingest_and_load",
        bash_command=_PIPELINE_CMD,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{_DBT_RUN_BASE} run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{_DBT_RUN_BASE} test",
    )

    ingest_and_load >> dbt_run >> dbt_test
