"""Load raw data into Postgres (products upsert, SCD2 append/close)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

try:
    from .db import get_engine
except ImportError:
    from db import get_engine

ALLOWED_SCD2_TABLES = frozenset({"users", "orders", "order_items"})

USER_COLUMNS = [
    "id",
    "entity_id",
    "first_name",
    "last_name",
    "email",
    "telephone",
    "age",
    "gender",
    "city",
    "registration_date",
    "valid_from",
    "valid_until",
]
ORDER_COLUMNS = [
    "id",
    "entity_id",
    "user_id",
    "order_date",
    "status",
    "payment_method",
    "shipping_city",
    "valid_from",
    "valid_until",
]
ORDER_ITEM_COLUMNS = [
    "id",
    "entity_id",
    "order_id",
    "product_id",
    "quantity",
    "unit_price",
    "valid_from",
    "valid_until",
]


def _run(
    fn: Callable[[Connection], Any],
    connection: Connection | None = None,
) -> Any:
    if connection is not None:
        return fn(connection)
    with get_engine().begin() as conn:
        return fn(conn)


def normalize_product(product: dict) -> dict:
    """Flatten FakeStore API product shape to raw.products columns."""
    rating = product.get("rating") or {}
    return {
        "id": product["id"],
        "title": product["title"],
        "price": product["price"],
        "description": product.get("description"),
        "category": product.get("category"),
        "image": product.get("image"),
        "rating_rate": rating.get("rate"),
        "rating_count": rating.get("count"),
    }


def upsert_products(
    products: list[dict],
    *,
    connection: Connection | None = None,
) -> int:
    """Insert or update products by id. Returns number of rows in the batch."""
    if not products:
        return 0

    rows = [normalize_product(p) for p in products]
    sql = text(
        """
        INSERT INTO raw.products (
            id, title, price, description, category, image, rating_rate, rating_count
        ) VALUES (
            :id, :title, :price, :description, :category, :image, :rating_rate, :rating_count
        )
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            image = EXCLUDED.image,
            rating_rate = EXCLUDED.rating_rate,
            rating_count = EXCLUDED.rating_count
        """
    )

    def _execute(conn: Connection) -> int:
        conn.execute(sql, rows)
        return len(rows)

    return _run(_execute, connection)


def close_versions(
    table: str,
    closures: list[dict],
    *,
    connection: Connection | None = None,
) -> int:
    """
    Set valid_until on current version rows (by version id).

    Each closure dict needs: id, valid_until.
    Only updates rows that are still current (valid_until IS NULL).
    """
    if table not in ALLOWED_SCD2_TABLES:
        raise ValueError(f"Unsupported table: {table}")
    if not closures:
        return 0

    sql = text(
        f"""
        UPDATE raw.{table}
        SET valid_until = :valid_until
        WHERE id = :id
          AND valid_until IS NULL
        """
    )

    def _execute(conn: Connection) -> int:
        total = 0
        for row in closures:
            result = conn.execute(
                sql,
                {"id": row["id"], "valid_until": row["valid_until"]},
            )
            total += result.rowcount or 0
        return total

    return _run(_execute, connection)


def _insert_rows(
    table: str,
    columns: list[str],
    rows: list[dict],
    connection: Connection | None = None,
) -> int:
    """Insert version rows; skip ids that already exist (safe re-run)."""
    if table not in ALLOWED_SCD2_TABLES:
        raise ValueError(f"Unsupported table: {table}")
    if not rows:
        return 0

    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    sql = text(
        f"""
        INSERT INTO raw.{table} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (id) DO NOTHING
        """
    )
    payloads = [{c: row.get(c) for c in columns} for row in rows]

    def _execute(conn: Connection) -> int:
        result = conn.execute(sql, payloads)
        return result.rowcount or 0

    return _run(_execute, connection)


def insert_users(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> int:
    return _insert_rows("users", USER_COLUMNS, rows, connection)


def insert_orders(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> int:
    return _insert_rows("orders", ORDER_COLUMNS, rows, connection)


def insert_order_items(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> int:
    return _insert_rows("order_items", ORDER_ITEM_COLUMNS, rows, connection)


def load_users(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> dict[str, int]:
    """Insert new user versions; close versions that include valid_until."""
    return _load_scd2("users", USER_COLUMNS, rows, connection)


def load_orders(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> dict[str, int]:
    """Insert new order versions; close versions that include valid_until."""
    return _load_scd2("orders", ORDER_COLUMNS, rows, connection)


def load_order_items(
    rows: list[dict],
    *,
    connection: Connection | None = None,
) -> dict[str, int]:
    """Insert new order_item versions; close versions that include valid_until."""
    return _load_scd2("order_items", ORDER_ITEM_COLUMNS, rows, connection)


def _load_scd2(
    table: str,
    columns: list[str],
    rows: list[dict],
    connection: Connection | None = None,
) -> dict[str, int]:
    """
    Persist SCD2 rows safely (close before insert to keep one current entity_id):
    - UPDATE valid_until for payload rows that are closed
    - INSERT any version ids not yet in the table
    """

    def _execute(conn: Connection) -> dict[str, int]:
        closures = [
            {"id": row["id"], "valid_until": row["valid_until"]}
            for row in rows
            if row.get("valid_until") is not None
        ]
        closed = close_versions(table, closures, connection=conn)
        inserted = _insert_rows(table, columns, rows, conn)
        return {"inserted": inserted, "closed": closed}

    return _run(_execute, connection)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Allow running as a script: python src/storage/load.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ingestion.products import extract_products
    from ingestion.users import create_users

    products = extract_products()
    n_products = upsert_products(products)
    print(f"upserted products: {n_products}")

    users = create_users(3)
    # Close first user and keep a new version to demo close + insert
    from ingestion.users import change_user

    new_version = change_user(users[0], next_id=100)
    result = load_users(users + [new_version])
    print(f"users load: {result}")
