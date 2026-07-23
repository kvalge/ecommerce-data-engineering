from datetime import date, timedelta

from faker import Faker

try:
    from .versioning import close_version, now_iso
except ImportError:
    from versioning import close_version, now_iso

SHIPPING_CITIES = [
    "Tallinn",
    "Tartu",
    "Narva",
    "Pärnu",
    "Jõhvi",
]
STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]
PAYMENT_METHODS = ["card", "bank_transfer", "cash_on_delivery"]


def create_orders(
    n: int = 10,
    user_ids: list[int] | None = None,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
    valid_from: str | None = None,
    recent: bool = True,
) -> list[dict]:
    """Create n new order versions. user_ids are user entity_ids."""
    fake = Faker()
    if not user_ids:
        user_ids = list(range(1, 11))

    at = valid_from or now_iso()
    if recent:
        start = date.today() - timedelta(days=14)
        date_start, date_end = start, date.today()
    else:
        date_start, date_end = date(2020, 1, 1), date.today()

    orders = []
    for offset in range(n):
        orders.append(
            {
                "id": start_id + offset,
                "entity_id": start_entity_id + offset,
                "user_id": fake.random_element(elements=user_ids),
                "order_date": fake.date_between(start_date=date_start, end_date=date_end).isoformat(),
                "status": fake.random_element(elements=STATUSES),
                "payment_method": fake.random_element(elements=PAYMENT_METHODS),
                "shipping_city": fake.random_element(elements=SHIPPING_CITIES),
                "valid_from": at,
                "valid_until": None,
            }
        )

    return orders


def change_order(
    current: dict,
    *,
    next_id: int,
    valid_at: str | None = None,
) -> dict:
    """Close current order version and return a new version (status / shipping_city)."""
    fake = Faker()
    at = valid_at or now_iso()
    close_version(current, at)

    return {
        "id": next_id,
        "entity_id": current["entity_id"],
        "user_id": current["user_id"],
        "order_date": current["order_date"],
        "status": fake.random_element(elements=STATUSES),
        "payment_method": current["payment_method"],
        "shipping_city": fake.random_element(elements=SHIPPING_CITIES),
        "valid_from": at,
        "valid_until": None,
    }


def drop_order(current: dict, valid_until: str | None = None) -> dict:
    """Soft-drop an order by closing its current version."""
    return close_version(current, valid_until)


def generate_orders(
    n: int = 10,
    user_ids: list[int] | None = None,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
) -> list[dict]:
    """Generate n new orders (versioned schema)."""
    return create_orders(
        n,
        user_ids,
        start_id=start_id,
        start_entity_id=start_entity_id,
    )


if __name__ == "__main__":
    orders = generate_orders(3, user_ids=[1, 2])
    print(orders)
    updated = change_order(orders[0], next_id=4)
    print("closed:", orders[0])
    print("new version:", updated)
