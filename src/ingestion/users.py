from datetime import date, timedelta

from faker import Faker

try:
    from .versioning import close_version, now_iso
except ImportError:
    from versioning import close_version, now_iso

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


def _profile_fields(fake: Faker, *, recent: bool = True) -> dict:
    if recent:
        start = date.today() - timedelta(days=14)
        registration_date = fake.date_between(start_date=start, end_date=date.today())
    else:
        registration_date = fake.date_between(start_date=date(2020, 1, 1), end_date=date.today())

    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "telephone": fake.phone_number(),
        "age": fake.random_int(min=18, max=80),
        "gender": fake.random_element(elements=GENDERS),
        "city": fake.random_element(elements=CITIES),
        "registration_date": registration_date.isoformat(),
    }


def create_users(
    n: int = 10,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
    valid_from: str | None = None,
    recent: bool = True,
) -> list[dict]:
    """Create n new user versions (one version each, currently valid)."""
    fake = Faker()
    at = valid_from or now_iso()
    users = []

    for offset in range(n):
        users.append(
            {
                "id": start_id + offset,
                "entity_id": start_entity_id + offset,
                **_profile_fields(fake, recent=recent),
                "valid_from": at,
                "valid_until": None,
            }
        )

    return users


def change_user(
    current: dict,
    *,
    next_id: int,
    valid_at: str | None = None,
) -> dict:
    """Close current user version and return a new version with updated profile fields."""
    fake = Faker()
    at = valid_at or now_iso()
    close_version(current, at)

    new_row = {
        "id": next_id,
        "entity_id": current["entity_id"],
        "first_name": current["first_name"],
        "last_name": current["last_name"],
        "email": fake.unique.email(),
        "telephone": fake.phone_number(),
        "age": current["age"],
        "gender": current["gender"],
        "city": fake.random_element(elements=CITIES),
        "registration_date": current["registration_date"],
        "valid_from": at,
        "valid_until": None,
    }
    return new_row


def generate_users(
    n: int = 10,
    *,
    start_id: int = 1,
    start_entity_id: int = 1,
) -> list[dict]:
    """Generate n new users (versioned schema)."""
    return create_users(n, start_id=start_id, start_entity_id=start_entity_id)


if __name__ == "__main__":
    users = generate_users(3)
    print(users)
    updated = change_user(users[0], next_id=4)
    print("closed:", users[0])
    print("new version:", updated)
