"""Simulate a real-life batch: new, changed, and dropped users/orders/order_items."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from faker import Faker

try:
    from .order_items import change_order_item, create_order_items, drop_order_item
    from .orders import change_order, create_orders, drop_order
    from .users import change_user, create_users
    from .versioning import current_rows, next_ids, now_iso
except ImportError:
    from order_items import change_order_item, create_order_items, drop_order_item
    from orders import change_order, create_orders, drop_order
    from users import change_user, create_users
    from versioning import current_rows, next_ids, now_iso


@dataclass
class BatchConfig:
    new_users: int = 3
    user_updates: int = 2
    new_orders: int = 5
    order_updates: int = 1
    order_drops: int = 1
    items_per_new_order_min: int = 1
    items_per_new_order_max: int = 3
    item_updates: int = 1
    item_drops: int = 1


@dataclass
class State:
    users: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    order_items: list[dict] = field(default_factory=list)


def seed_state(
    *,
    n_users: int = 10,
    n_orders: int = 15,
    n_items: int = 30,
    products: list[dict] | None = None,
) -> State:
    """Build an initial in-memory history (all currently valid)."""
    users = create_users(n_users, recent=False)
    user_entity_ids = [u["entity_id"] for u in users]
    orders = create_orders(n_orders, user_entity_ids, recent=False)
    order_entity_ids = [o["entity_id"] for o in orders]
    order_items = create_order_items(n_items, order_entity_ids, products)
    return State(users=users, orders=orders, order_items=order_items)


def _pick(_fake: Faker, rows: list[dict], n: int) -> list[dict]:
    if not rows or n <= 0:
        return []
    n = min(n, len(rows))
    return random.sample(rows, n)


def simulate_batch(
    state: State,
    *,
    config: BatchConfig | None = None,
    products: list[dict] | None = None,
) -> State:
    """
    Apply one mixed batch of creates, changes, and drops.

    Mutates version rows in place when closing; appends new versions to state lists.
    Only touches currently valid rows. Dropped order entity_ids are not reused.
    """
    config = config or BatchConfig()
    fake = Faker()
    at = now_iso()
    dropped_order_entity_ids: set[int] = set()

    # --- new users ---
    next_id, next_entity_id = next_ids(state.users)
    new_users = create_users(
        config.new_users,
        start_id=next_id,
        start_entity_id=next_entity_id,
        valid_from=at,
    )
    state.users.extend(new_users)

    # --- user updates ---
    for user in _pick(fake, current_rows(state.users), config.user_updates):
        next_id, _ = next_ids(state.users)
        state.users.append(change_user(user, next_id=next_id, valid_at=at))

    # --- new orders (may use old + new current users) ---
    current_user_ids = [u["entity_id"] for u in current_rows(state.users)]
    next_id, next_entity_id = next_ids(state.orders)
    new_orders = create_orders(
        config.new_orders,
        current_user_ids,
        start_id=next_id,
        start_entity_id=next_entity_id,
        valid_from=at,
    )
    state.orders.extend(new_orders)

    # --- items for new orders ---
    for order in new_orders:
        n_items = fake.random_int(
            min=config.items_per_new_order_min,
            max=config.items_per_new_order_max,
        )
        next_id, next_entity_id = next_ids(state.order_items)
        state.order_items.extend(
            create_order_items(
                n_items,
                [order["entity_id"]],
                products,
                start_id=next_id,
                start_entity_id=next_entity_id,
                valid_from=at,
            )
        )

    # --- order updates (exclude rows we will drop if possible by updating first) ---
    for order in _pick(fake, current_rows(state.orders), config.order_updates):
        next_id, _ = next_ids(state.orders)
        state.orders.append(change_order(order, next_id=next_id, valid_at=at))

    # --- order drops (+ cascade close current items) ---
    for order in _pick(fake, current_rows(state.orders), config.order_drops):
        drop_order(order, valid_until=at)
        dropped_order_entity_ids.add(order["entity_id"])
        for item in current_rows(state.order_items):
            if item["order_id"] == order["entity_id"]:
                drop_order_item(item, valid_until=at)

    # --- item updates (skip items on dropped orders) ---
    updatable_items = [
        item
        for item in current_rows(state.order_items)
        if item["order_id"] not in dropped_order_entity_ids
    ]
    for item in _pick(fake, updatable_items, config.item_updates):
        next_id, _ = next_ids(state.order_items)
        state.order_items.append(
            change_order_item(item, next_id=next_id, products=products, valid_at=at)
        )

    # --- item drops (partial cancel; skip already closed / dropped-order items) ---
    droppable_items = [
        item
        for item in current_rows(state.order_items)
        if item["order_id"] not in dropped_order_entity_ids
    ]
    for item in _pick(fake, droppable_items, config.item_drops):
        drop_order_item(item, valid_until=at)

    return state


def _summary(state: State) -> dict:
    return {
        "users_total": len(state.users),
        "users_current": len(current_rows(state.users)),
        "orders_total": len(state.orders),
        "orders_current": len(current_rows(state.orders)),
        "order_items_total": len(state.order_items),
        "order_items_current": len(current_rows(state.order_items)),
    }


if __name__ == "__main__":
    state = seed_state()
    print("seed:", _summary(state))
    simulate_batch(state)
    print("after batch 1:", _summary(state))
    simulate_batch(state)
    print("after batch 2:", _summary(state))

    # Show one user with history if any updates happened
    from collections import Counter

    counts = Counter(u["entity_id"] for u in state.users)
    multi = [eid for eid, c in counts.items() if c > 1]
    if multi:
        eid = multi[0]
        versions = [u for u in state.users if u["entity_id"] == eid]
        print(f"user entity_id={eid} versions:")
        for v in versions:
            print(
                {
                    "id": v["id"],
                    "email": v["email"],
                    "city": v["city"],
                    "valid_from": v["valid_from"],
                    "valid_until": v["valid_until"],
                }
            )
