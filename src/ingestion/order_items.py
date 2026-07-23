from faker import Faker

try:
    from .versioning import close_version, now_iso
except ImportError:
    from versioning import close_version, now_iso


def _default_products(fake: Faker) -> list[dict]:
    # FakeStore API has products 1–20; placeholder prices for standalone runs
    return [
        {
            "id": i,
            "price": round(fake.pyfloat(min_value=5, max_value=200, right_digits=2), 2),
        }
        for i in range(1, 21)
    ]


def create_order_items(
    n: int = 20,
    order_ids: list[int] | None = None,
    products: list[dict] | None = None,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
    valid_from: str | None = None,
) -> list[dict]:
    """Create n new order_item versions. order_ids are order entity_ids."""
    fake = Faker()
    if not order_ids:
        order_ids = list(range(1, 11))
    if not products:
        products = _default_products(fake)

    at = valid_from or now_iso()
    order_items = []

    for offset in range(n):
        product = fake.random_element(elements=products)
        order_items.append(
            {
                "id": start_id + offset,
                "entity_id": start_entity_id + offset,
                "order_id": fake.random_element(elements=order_ids),
                "product_id": product["id"],
                "quantity": fake.random_int(min=1, max=5),
                "unit_price": product["price"],
                "valid_from": at,
                "valid_until": None,
            }
        )

    return order_items


def change_order_item(
    current: dict,
    *,
    next_id: int,
    products: list[dict] | None = None,
    valid_at: str | None = None,
) -> dict:
    """Close current item version and return a new version (quantity / product)."""
    fake = Faker()
    at = valid_at or now_iso()
    close_version(current, at)

    if products:
        product = fake.random_element(elements=products)
        product_id = product["id"]
        unit_price = product["price"]
    else:
        product_id = current["product_id"]
        unit_price = current["unit_price"]

    return {
        "id": next_id,
        "entity_id": current["entity_id"],
        "order_id": current["order_id"],
        "product_id": product_id,
        "quantity": fake.random_int(min=1, max=5),
        "unit_price": unit_price,
        "valid_from": at,
        "valid_until": None,
    }


def drop_order_item(current: dict, valid_until: str | None = None) -> dict:
    """Soft-drop an order item by closing its current version."""
    return close_version(current, valid_until)


def generate_order_items(
    n: int = 20,
    order_ids: list[int] | None = None,
    products: list[dict] | None = None,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
) -> list[dict]:
    """Generate n new order items (versioned schema)."""
    return create_order_items(
        n,
        order_ids,
        products,
        start_id=start_id,
        start_entity_id=start_entity_id,
    )


if __name__ == "__main__":
    items = generate_order_items(3, order_ids=[1, 2])
    print(items)
    updated = change_order_item(items[0], next_id=4)
    print("closed:", items[0])
    print("new version:", updated)
