import random
import datetime
from faker import Faker
import hashlib


def fake_region_name(fake: Faker) -> str:
    templates = [
        "{} Oblast",
        "{} Krai",
        "Republic of {}",
    ]
    return fake.random_element(templates).format(fake.unique.city())


def random_numeric(lo: float, hi: float, digits: int = 1) -> float:
    return round(random.uniform(lo, hi), digits)


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def passport_series() -> str:
    return f"{random.randint(10, 99)}{random.randint(10, 99)}"


def passport_number() -> str:
    return f"{random.randint(0, 999999):06d}"


def card_last_digits() -> str:
    return f"{random.randint(0, 9999):04d}"


def russian_plate() -> str:
    letters = "ABEKMHOPCTYX"
    region_code = random.choice([77, 78, 50, 52, 66, 96, 116, 163, 174, 197, 199, 777])
    return (
        f"{random.choice(letters)}"
        f"{random.randint(0, 999):03d}"
        f"{random.choice(letters)}{random.choice(letters)} "
        f"{region_code}"
    )


def unique_plate(used: set[str]) -> str:
    while True:
        plate = russian_plate()
        if plate not in used:
            used.add(plate)
            return plate


def random_point():
    x = round(random.uniform(30.0, 180.0), 6)
    y = round(random.uniform(30.0, 80.0), 6)
    return x, y


def pick_weighted_car_class() -> str:
    # approx fleet mix
    return random.choices(
        population=["econom", "middle", "premium", "family"],
        weights=[0.52, 0.26, 0.10, 0.12],
        k=1
    )[0]


def booking_duration_hours(kind: str) -> float:
    if kind == "mins":
        return round(random.uniform(0.2, 2.5), 2)
    return round(random.uniform(2.0, 36.0), 2)


def now_minus(days_back: int) -> datetime:
    return datetime.now() - timedelta(days=random.randint(0, days_back))


def choose_many(seq, k_min: int, k_max: int):
    if not seq:
        return []
    k = min(len(seq), random.randint(k_min, k_max))
    return random.sample(seq, k)


def insert_returning_id(cur, sql: str, params: tuple):
    cur.execute(sql, params)
    return cur.fetchone()[0]


