"""Persist a seed (once) and subsequent simulate_batch runs to Postgres."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python src/pipeline/run_batch.py`
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ingestion.products import extract_products
from ingestion.simulate_batch import BatchConfig, State, seed_state, simulate_batch
from ingestion.versioning import current_rows
from storage.db import get_engine
from storage.load import load_order_items, load_orders, load_users, upsert_products
from storage.read import fetch_order_items, fetch_orders, fetch_users, is_seeded


def _db_summary() -> dict[str, int]:
    users = fetch_users()
    orders = fetch_orders()
    items = fetch_order_items()
    return {
        "users_total": len(users),
        "users_current": len(current_rows(users)),
        "orders_total": len(orders),
        "orders_current": len(current_rows(orders)),
        "order_items_total": len(items),
        "order_items_current": len(current_rows(items)),
    }


def _persist_state(state: State) -> dict[str, dict[str, int]]:
    return {
        "users": load_users(state.users),
        "orders": load_orders(state.orders),
        "order_items": load_order_items(state.order_items),
    }


def run_batch(*, config: BatchConfig | None = None) -> dict:
    """
    Upsert products, seed raw tables once if empty, otherwise:
    load state from DB -> simulate_batch -> persist closes/inserts.
    """
    products = extract_products()
    product_count = upsert_products(products)

    if not is_seeded():
        state = seed_state(products=products)
        persisted = _persist_state(state)
        return {
            "action": "seed",
            "products_upserted": product_count,
            "persisted": persisted,
            "db": _db_summary(),
        }

    state = State(
        users=fetch_users(),
        orders=fetch_orders(),
        order_items=fetch_order_items(),
    )
    simulate_batch(state, config=config, products=products)
    persisted = _persist_state(state)
    return {
        "action": "batch",
        "products_upserted": product_count,
        "persisted": persisted,
        "db": _db_summary(),
    }


if __name__ == "__main__":
    from sqlalchemy import text

    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))

    result = run_batch()
    print(result)
