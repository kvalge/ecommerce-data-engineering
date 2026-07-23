from datetime import date

from faker import Faker

CITIES = [
    "Tallinn",
    "Tartu",
    "Narva",
    "Pärnu",
    "Viljandi",
    "Võru",
    "Kuressaare",
    "Jõhvi",
]
GENDERS = ["M", "W", "not defined"]


def generate_users(n: int = 10) -> list[dict]:
    """Generate n fake users matching the project user schema."""
    fake = Faker()
    users = []

    for user_id in range(1, n + 1):
        users.append(
            {
                "id": user_id,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "telephone": fake.phone_number(),
                "age": fake.random_int(min=18, max=80),
                "gender": fake.random_element(elements=GENDERS),
                "city": fake.random_element(elements=CITIES),
                "registration_date": fake.date_between(
                    start_date=date(2020, 1, 1),
                    end_date=date.today(),
                ).isoformat(),
            }
        )

    return users


if __name__ == "__main__":
    users = generate_users(5)
    print(users)
