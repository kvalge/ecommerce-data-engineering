from faker import Faker


def generate_order_items(
    n: int = 20,
    order_ids: list[int] | None = None,
    products: list[dict] | None = None,
) -> list[dict]:
    """Generate n fake order items matching the project order_items schema.

    products should be dicts with at least 'id' and 'price'.
    """
    fake = Faker()
    if not order_ids:
        order_ids = list(range(1, 11))
    if not products:
        # FakeStore API has products 1–20; placeholder prices for standalone runs
        products = [{"id": i, "price": round(fake.pyfloat(min_value=5, max_value=200, right_digits=2), 2)} for i in range(1, 21)]

    order_items = []
    for item_id in range(1, n + 1):
        product = fake.random_element(elements=products)
        order_items.append(
            {
                "id": item_id,
                "order_id": fake.random_element(elements=order_ids),
                "product_id": product["id"],
                "quantity": fake.random_int(min=1, max=5),
                "unit_price": product["price"],
            }
        )

    return order_items


if __name__ == "__main__":
    order_items = generate_order_items(5)
    print(order_items)
