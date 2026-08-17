"""Read raw tables from Postgres into plain dicts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

try:
    from .db import get_engine
except ImportError:
    from db import get_engine

ALLOWED_TABLES = frozenset({"users", "orders", "order_items", "products"})


def _run(
    fn: Callable[[Connection], Any],
    connection: Connection | None = None,
) -> Any:
    if connection is not None:
        return fn(connection)
    with get_engine().connect() as conn:
        return fn(conn)


def _row_to_dict(row: Any) -> dict:
    data = dict(row._mapping)
    for key, value in data.items():
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


def fetch_rows(
    table: str,
    *,
    connection: Connection | None = None,
) -> list[dict]:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Unsupported table: {table}")

    sql = text(f"SELECT * FROM raw.{table} ORDER BY id")

    def _execute(conn: Connection) -> list[dict]:
        return [_row_to_dict(row) for row in conn.execute(sql)]

    return _run(_execute, connection)


def fetch_users(*, connection: Connection | None = None) -> list[dict]:
    return fetch_rows("users", connection=connection)


def fetch_orders(*, connection: Connection | None = None) -> list[dict]:
    return fetch_rows("orders", connection=connection)


def fetch_order_items(*, connection: Connection | None = None) -> list[dict]:
    return fetch_rows("order_items", connection=connection)


def is_seeded(*, connection: Connection | None = None) -> bool:
    """True when raw.users already has at least one row."""

    def _execute(conn: Connection) -> bool:
        return bool(
            conn.execute(text("SELECT EXISTS (SELECT 1 FROM raw.users LIMIT 1)")).scalar()
        )

    return _run(_execute, connection)
