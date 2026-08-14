"""PostgreSQL connection helpers for the raw storage layer."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_db_env() -> None:
    """Load `.env` from the project root (does not override existing env vars)."""
    load_dotenv(_project_root() / ".env")


def get_database_url() -> str:
    """
    Return the SQLAlchemy database URL.

    Builds from POSTGRES_* when set; otherwise uses DATABASE_URL.
    """
    load_db_env()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")

    if user and password and db_name:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

    url = os.getenv("DATABASE_URL")
    if url:
        return url

    raise ValueError(
        "Set POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB in .env "
        "(or provide DATABASE_URL)"
    )

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create (and cache) a SQLAlchemy engine for Postgres."""
    return create_engine(get_database_url(), pool_pre_ping=True)


def get_connection():
    """Open a new connection from the shared engine (caller should close / use context manager)."""
    return get_engine().connect()


if __name__ == "__main__":
    with get_connection() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
        print(f"DB connection OK: {value}")
