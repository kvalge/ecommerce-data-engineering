from datetime import date

from faker import Faker

SHIPPING_CITIES = [
    "Tallinn",
    "Tartu",
    "Narva",
    "Pärnu",
    "Jõhvi",
]
STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]
PAYMENT_METHODS = ["card", "bank_transfer", "cash_on_delivery"]


def generate_orders(
    n: int = 10,
    user_ids: list[int] | None = None,
) -> list[dict]:
    """Generate n fake orders matching the project order schema."""
    fake = Faker()
    if not user_ids:
        user_ids = list(range(1, 11))

    orders = []
    for order_id in range(1, n + 1):
        orders.append(
            {
                "id": order_id,
                "user_id": fake.random_element(elements=user_ids),
                "order_date": fake.date_between(
                    start_date=date(2020, 1, 1),
                    end_date=date.today(),
                ).isoformat(),
                "status": fake.random_element(elements=STATUSES),
                "payment_method": fake.random_element(elements=PAYMENT_METHODS),
                "shipping_city": fake.random_element(elements=SHIPPING_CITIES),
            }
        )

    return orders


if __name__ == "__main__":
    orders = generate_orders(5)
    print(orders)
