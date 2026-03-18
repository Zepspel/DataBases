#import hashlib
from datetime import date, datetime, timedelta
import random

from helpers import (
    fake_region_name,
    random_numeric,
    md5_hash,
    passport_series,
    passport_number,
    card_last_digits,
    unique_plate,
    random_point,
    pick_weighted_car_class,
    booking_duration_hours,
    choose_many,
    insert_returning_id,
)


from config import (
    CAR_CLASSES,
    CAR_CLASS_INFO,
    SERVICE_NAMES,
    ROLE_NAMES,
    PAYMENT_SYSTEMS,
    ACTION_TYPES,
    BOOKING_TYPES,
    VISIT_STATUSES,
    CAR_COLORS,
)



def fill_regions(cur, fake: Faker, amount: int):
    region_ids = []

    for _ in range(amount):
        name = fake_region_name(fake)
        description = fake.paragraph(nb_sentences=3)

        region_id = insert_returning_id(
            cur,
            """
            INSERT INTO region (name, description)
            VALUES (%s, %s)
            RETURNING region_id
            """,
            (name, description),
        )
        region_ids.append(region_id)

    return region_ids


def fill_cities(cur, fake: Faker, region_ids: list[int], amount: int):
    city_rows = []

    for _ in range(amount):
        region_id = random.choice(region_ids)
        name = fake.unique.city()
        description = fake.paragraph(nb_sentences=2)

        city_id = insert_returning_id(
            cur,
            """
            INSERT INTO city (region_id, name, description)
            VALUES (%s, %s, %s)
            RETURNING city_id
            """,
            (region_id, name, description),
        )
        city_rows.append({"city_id": city_id, "region_id": region_id})

    return city_rows


def fill_districts(cur, fake: Faker, city_rows: list[dict], amount: int):
    district_rows = []

    for _ in range(amount):
        city = random.choice(city_rows)
        name = f"{fake.street_name()} District"[:32]

        district_id = insert_returning_id(
            cur,
            """
            INSERT INTO district (city_id, name)
            VALUES (%s, %s)
            RETURNING district_id
            """,
            (city["city_id"], name),
        )
        district_rows.append({
            "district_id": district_id,
            "city_id": city["city_id"],
            "region_id": city["region_id"],
        })

    return district_rows


def fill_parkings(cur, district_rows: list[dict], amount: int):
    parking_rows = []

    for _ in range(amount):
        district = random.choice(district_rows)
        x, y = random_point()

        parking_id = insert_returning_id(
            cur,
            """
            INSERT INTO parking (district_id, coords)
            VALUES (%s, POINT(%s, %s))
            RETURNING parking_id
            """,
            (district["district_id"], x, y),
        )
        parking_rows.append({
            "parking_id": parking_id,
            "district_id": district["district_id"],
        })

    return parking_rows


def fill_car_classes(cur):
    class_id_by_name = {}

    for cls in CAR_CLASSES:
        class_id = insert_returning_id(
            cur,
            """
            INSERT INTO car_class (name, description)
            VALUES (%s, %s)
            RETURNING car_class_id
            """,
            (cls, f"{cls.title()} car segment"),
        )
        class_id_by_name[cls] = class_id

    return class_id_by_name


def fill_price_list(cur, region_ids: list[int], class_id_by_name: dict[str, int]):
    price_rows = []

    for region_id in region_ids:
        regional_multiplier = random.uniform(0.92, 1.18)

        for cls_name, class_id in class_id_by_name.items():
            info = CAR_CLASS_INFO[cls_name]
            cost_min = round(random.uniform(*info["cost_min"]) * regional_multiplier, 2)
            cost_hour = round(random.uniform(*info["cost_hour"]) * regional_multiplier, 2)

            cur.execute(
                """
                INSERT INTO price_list (car_class_id, region_id, cost_min, cost_hour)
                VALUES (%s, %s, %s, %s)
                """,
                (class_id, region_id, cost_min, cost_hour),
            )
            price_rows.append({
                "car_class_id": class_id,
                "region_id": region_id,
                "cost_min": cost_min,
                "cost_hour": cost_hour,
            })

    return price_rows


def fill_cars(cur, fake: Faker, region_ids: list[int], class_id_by_name: dict[str, int], amount: int):
    car_rows = []
    used_plates = set()

    for _ in range(amount):
        cls_name = pick_weighted_car_class()
        cls_id = class_id_by_name[cls_name]
        info = CAR_CLASS_INFO[cls_name]
        brand, model = random.choice(info["brands"])
        region_id = random.choice(region_ids)

        car_id = insert_returning_id(
            cur,
            """
            INSERT INTO car (
                class_id, region_id, number, brand, model, color,
                capacity, engine_volume, fuel_consumption
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING car_id
            """,
            (
                cls_id,
                region_id,
                unique_plate(used_plates),
                brand,
                model,
                random.choice(CAR_COLORS),
                random.choice(info["capacity"]),
                random_numeric(*info["engine"], digits=1),
                random_numeric(*info["fuel"], digits=1),
            ),
        )
        car_rows.append({
            "car_id": car_id,
            "region_id": region_id,
            "class_name": cls_name,
            "class_id": cls_id,
        })

    return car_rows


def fill_sc(cur, fake: Faker, district_rows: list[dict], amount: int):
    sc_rows = []

    for i in range(amount):
        district = random.choice(district_rows)
        name = f"Service Center {i + 1}"[:32]
        address = fake.address()

        sc_id = insert_returning_id(
            cur,
            """
            INSERT INTO sc (district_id, name, address)
            VALUES (%s, %s, %s)
            RETURNING sc_id
            """,
            (district["district_id"], name, address),
        )
        sc_rows.append({
            "sc_id": sc_id,
            "district_id": district["district_id"],
        })

    return sc_rows


def fill_services(cur):
    service_rows = []

    for name, description in SERVICE_NAMES:
        service_id = insert_returning_id(
            cur,
            """
            INSERT INTO service (name, description)
            VALUES (%s, %s)
            RETURNING service_id
            """,
            (name[:32], description),
        )
        service_rows.append({"service_id": service_id, "name": name[:32]})

    return service_rows


def fill_service_sc(cur, sc_rows: list[dict], service_rows: list[dict]):
    service_sc_rows = []

    for sc in sc_rows:
        chosen = choose_many(service_rows, 4, 8)
        for service in chosen:
            base_cost = {
                "Oil change": (2500, 5500),
                "Brake inspection": (1200, 3000),
                "Tire fitting": (1800, 4500),
                "Diagnostics": (1500, 4000),
                "Suspension repair": (5000, 24000),
                "Battery service": (1000, 7000),
                "Engine repair": (12000, 90000),
                "Body repair": (6000, 70000),
                "Car wash": (500, 1800),
                "Air conditioning service": (2500, 10000),
            }.get(service["name"], (1000, 10000))

            cost = round(random.uniform(*base_cost), 2)

            service_sc_id = insert_returning_id(
                cur,
                """
                INSERT INTO service_sc (sc_id, service_id, cost)
                VALUES (%s, %s, %s)
                RETURNING service_sc_id
                """,
                (sc["sc_id"], service["service_id"], cost),
            )
            service_sc_rows.append({
                "service_sc_id": service_sc_id,
                "sc_id": sc["sc_id"],
                "service_id": service["service_id"],
                "cost": cost,
            })

    return service_sc_rows


def fill_visit_sc(cur, fake: Faker, car_rows: list[dict]):
    visit_rows = []

    causes = [
        "Scheduled maintenance",
        "Brake issue",
        "Tire wear",
        "Engine diagnostics",
        "Body damage repair",
        "Battery replacement",
        "Suspension noise",
        "Air conditioner service",
    ]

    for car in car_rows:
        visits_count = random.choices([0, 1, 2, 3], weights=[0.45, 0.30, 0.18, 0.07], k=1)[0]

        for _ in range(visits_count):
            begin = fake.date_between(start_date="-2y", end_date="today")
            duration_days = random.randint(0, 8)
            status = random.choices(VISIT_STATUSES, weights=[0.08, 0.05, 0.80, 0.07], k=1)[0]
            end = begin + timedelta(days=duration_days) if status in ("done", "cancelled") else None
            total_cost = round(random.uniform(1500, 55000), 2) if status == "done" else None

            visit_sc_id = insert_returning_id(
                cur,
                """
                INSERT INTO visit_sc (
                    car_id, begin_date, end_date, cause, status, total_cost
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING visit_sc_id
                """,
                (
                    car["car_id"],
                    begin,
                    end,
                    random.choice(causes),
                    status,
                    total_cost,
                ),
            )
            visit_rows.append({
                "visit_sc_id": visit_sc_id,
                "car_id": car["car_id"],
                "status": status,
            })

    return visit_rows


def fill_visit_sc_per_service_sc(cur, fake: Faker, visit_rows: list[dict], service_sc_rows: list[dict]):
    link_rows = []

    for visit in visit_rows:
        chosen = choose_many(service_sc_rows, 1, 4)
        for row in chosen:
            cur.execute(
                """
                INSERT INTO visit_sc_per_service_sc (visit_sc_id, service_sc_id, info)
                VALUES (%s, %s, %s)
                """,
                (
                    visit["visit_sc_id"],
                    row["service_sc_id"],
                    fake.sentence(nb_words=8),
                ),
            )
            link_rows.append((visit["visit_sc_id"], row["service_sc_id"]))

    return link_rows


def fill_maintenance_info(cur, fake: Faker, visit_rows: list[dict]):
    info_ids = []

    for visit in visit_rows:
        if random.random() < 0.75:
            dt = fake.date_between(start_date="-2y", end_date="today")
            info_id = insert_returning_id(
                cur,
                """
                INSERT INTO maintenance_info (car_id, visit_sc_id, date)
                VALUES (%s, %s, %s)
                RETURNING info_id
                """,
                (visit["car_id"], visit["visit_sc_id"], dt),
            )
            info_ids.append(info_id)

    return info_ids


def fill_roles(cur):
    role_id_by_name = {}

    for role in ROLE_NAMES:
        role_id = insert_returning_id(
            cur,
            """
            INSERT INTO role (name, description)
            VALUES (%s, %s)
            RETURNING role_id
            """,
            (role, f"{role.title()} role"),
        )
        role_id_by_name[role] = role_id

    return role_id_by_name


def fill_accounts_and_people(cur, fake: Faker, role_id_by_name: dict[str, int], employee_amount: int, renter_amount: int):
    account_rows = []
    employee_rows = []
    renter_rows = []

    used_emails = set()

    def unique_email():
        while True:
            email = fake.email().lower()
            if email not in used_emails:
                used_emails.add(email)
                return email

    # administration accounts
    for i in range(4):
        email = f"admin{i+1}@carsharing.local"
        account_id = insert_returning_id(
            cur,
            """
            INSERT INTO account (role_id, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING account_id
            """,
            (
                role_id_by_name["administration"],
                email,
                md5_hash("admin123"),
            ),
        )
        account_rows.append({"account_id": account_id, "role": "administration"})

    # employee accounts + employees
    for _ in range(employee_amount):
        email = unique_email()
        account_id = insert_returning_id(
            cur,
            """
            INSERT INTO account (role_id, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING account_id
            """,
            (
                role_id_by_name["employee"],
                email,
                md5_hash("employee123"),
            ),
        )
        employee_id = insert_returning_id(
            cur,
            """
            INSERT INTO employee (
                account_id, full_name, phone, passport_series, passport_number, birth_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING employee_id
            """,
            (
                account_id,
                fake.name(),
                fake.phone_number()[:32],
                passport_series(),
                passport_number(),
                fake.date_of_birth(minimum_age=21, maximum_age=60),
            ),
        )
        account_rows.append({"account_id": account_id, "role": "employee"})
        employee_rows.append({"employee_id": employee_id, "account_id": account_id})

    # renter accounts + renters
    for _ in range(renter_amount):
        birth_date = fake.date_of_birth(minimum_age=20, maximum_age=70)
        driver_license_date = birth_date + timedelta(days=365 * random.randint(18, 35))
        if driver_license_date > date.today():
            driver_license_date = date.today() - timedelta(days=random.randint(90, 2500))

        email = unique_email()
        account_id = insert_returning_id(
            cur,
            """
            INSERT INTO account (role_id, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING account_id
            """,
            (
                role_id_by_name["renter"],
                email,
                md5_hash("renter123"),
            ),
        )
        renter_id = insert_returning_id(
            cur,
            """
            INSERT INTO renter (
                account_id, full_name, phone, passport_series, passport_number,
                birth_date, driver_license_date, license_ack
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING renter_id
            """,
            (
                account_id,
                fake.name(),
                fake.phone_number()[:32],
                passport_series(),
                passport_number(),
                birth_date,
                driver_license_date,
                random.random() < 0.96,
            ),
        )
        account_rows.append({"account_id": account_id, "role": "renter"})
        renter_rows.append({"renter_id": renter_id, "account_id": account_id})

    return account_rows, employee_rows, renter_rows


def fill_actions(cur, fake: Faker, account_rows: list[dict]):
    action_ids = []

    for account in account_rows:
        action_count = random.choices([0, 1, 2, 3, 4], weights=[0.15, 0.32, 0.28, 0.17, 0.08], k=1)[0]
        for _ in range(action_count):
            action_id = insert_returning_id(
                cur,
                """
                INSERT INTO action (account_id, type, old_value, new_value)
                VALUES (%s, %s, %s, %s)
                RETURNING action_id
                """,
                (
                    account["account_id"],
                    random.choice(ACTION_TYPES),
                    fake.sentence(nb_words=6) if random.random() < 0.65 else None,
                    fake.sentence(nb_words=6) if random.random() < 0.80 else None,
                ),
            )
            action_ids.append(action_id)

    return action_ids


def fill_cards(cur, fake: Faker, renter_rows: list[dict]):
    card_rows = []

    for renter in renter_rows:
        cards_count = random.choices([1, 2, 3], weights=[0.74, 0.22, 0.04], k=1)[0]
        for _ in range(cards_count):
            duration = date.today() + timedelta(days=random.randint(90, 365 * 4))

            card_id = insert_returning_id(
                cur,
                """
                INSERT INTO card (
                    renter_id, payment_token, last_digits, duration, payment_system
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING card_id
                """,
                (
                    renter["renter_id"],
                    md5_hash(fake.uuid4() + str(random.random())),
                    card_last_digits(),
                    duration,
                    random.choice(PAYMENT_SYSTEMS),
                ),
            )
            card_rows.append({
                "card_id": card_id,
                "renter_id": renter["renter_id"],
            })

    return card_rows


def fill_bookings(cur, car_rows: list[dict], renter_rows: list[dict]):
    booking_rows = []

    cars_by_region = {}
    for car in car_rows:
        cars_by_region.setdefault(car["region_id"], []).append(car)

    # renters do not have region in schema, so we simply assign a plausible number of bookings
    for renter in renter_rows:
        bookings_count = random.choices(
            [0, 1, 2, 3, 4, 5, 6],
            weights=[0.10, 0.18, 0.24, 0.20, 0.14, 0.09, 0.05],
            k=1,
        )[0]

        for _ in range(bookings_count):
            car = random.choice(car_rows)
            kind = random.choices(BOOKING_TYPES, weights=[0.72, 0.28], k=1)[0]

            begin = datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
            hours = booking_duration_hours(kind)

            if random.random() < 0.10:
                end_time = None
            else:
                end_time = begin + timedelta(hours=hours)

            booking_id = insert_returning_id(
                cur,
                """
                INSERT INTO booking (
                    car_id, renter_id, begin_time, end_time, type
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING booking_id
                """,
                (
                    car["car_id"],
                    renter["renter_id"],
                    begin,
                    end_time,
                    kind,
                ),
            )
            booking_rows.append({
                "booking_id": booking_id,
                "car_id": car["car_id"],
                "renter_id": renter["renter_id"],
                "begin_time": begin,
                "end_time": end_time,
                "type": kind,
            })

    return booking_rows


def fill_gps(cur, booking_rows: list[dict]):
    gps_rows = []

    for booking in booking_rows:
        points_count = random.choices([1, 2, 3, 4, 5], weights=[0.18, 0.24, 0.24, 0.20, 0.14], k=1)[0]
        for _ in range(points_count):
            x, y = random_point()
            gps_id = insert_returning_id(
                cur,
                """
                INSERT INTO gps (car_id, booking_id, coords)
                VALUES (%s, %s, POINT(%s, %s))
                RETURNING gps_id
                """,
                (booking["car_id"], booking["booking_id"], x, y),
            )
            gps_rows.append(gps_id)

    return gps_rows


def fill_fines(cur, fake: Faker, booking_rows: list[dict]):
    fine_rows = []

    causes = [
        "Speeding",
        "Illegal parking",
        "Toll road debt",
        "Traffic camera penalty",
        "Late payment",
        "Vehicle damage compensation",
    ]

    for booking in booking_rows:
        if random.random() < 0.12:
            receiving_time = booking["begin_time"] + timedelta(days=random.randint(1, 60))
            is_paid = random.random() < 0.62
            payment_time = receiving_time + timedelta(days=random.randint(1, 40)) if is_paid else None
            amount = round(random.uniform(500, 18000), 2)

            fine_id = insert_returning_id(
                cur,
                """
                INSERT INTO fine (
                    renter_id, booking_id, cause, receiving_time, payment_time, amount
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING fine_id
                """,
                (
                    booking["renter_id"],
                    booking["booking_id"],
                    random.choice(causes),
                    receiving_time,
                    payment_time,
                    amount,
                ),
            )
            fine_rows.append({
                "fine_id": fine_id,
                "booking_id": booking["booking_id"],
                "renter_id": booking["renter_id"],
                "amount": amount,
            })

    return fine_rows


def fill_debitings(cur, booking_rows: list[dict], fine_rows: list[dict], card_rows: list[dict]):
    debiting_ids = []

    cards_by_renter = {}
    for card in card_rows:
        cards_by_renter.setdefault(card["renter_id"], []).append(card["card_id"])

    # booking debitings
    for booking in booking_rows:
        renter_cards = cards_by_renter.get(booking["renter_id"], [])
        card_id = random.choice(renter_cards) if renter_cards else None

        if booking["end_time"] is None:
            hours = round(random.uniform(0.2, 4.0), 2)
        else:
            delta = booking["end_time"] - booking["begin_time"]
            hours = max(delta.total_seconds() / 3600.0, 0.2)

        kind = booking["type"]
        amount = round(hours * random.uniform(8, 14), 2) if kind == "mins" else round(hours * random.uniform(150, 650), 2)

        debiting_id = insert_returning_id(
            cur,
            """
            INSERT INTO debiting (
                card_id, booking_id, fine_id, time_interval, amount, type
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING debiting_id
            """,
            (
                card_id,
                booking["booking_id"],
                None,
                timedelta(hours=hours),
                amount,
                "min" if kind == "mins" else "hour",
            ),
        )
        debiting_ids.append(debiting_id)

    # fine debitings
    for fine in fine_rows:
        renter_cards = cards_by_renter.get(fine["renter_id"], [])
        card_id = random.choice(renter_cards) if renter_cards else None

        debiting_id = insert_returning_id(
            cur,
            """
            INSERT INTO debiting (
                card_id, booking_id, fine_id, time_interval, amount, type
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING debiting_id
            """,
            (
                card_id,
                fine["booking_id"],
                fine["fine_id"],
                timedelta(hours=0),
                fine["amount"],
                "fine",
            ),
        )
        debiting_ids.append(debiting_id)

    return debiting_ids


# =========================================================
# Main fill routine
# =========================================================

def fill_all(cur, fake: Faker, amount: dict):
    region_ids = fill_regions(cur, fake, amount["region"])
    city_rows = fill_cities(cur, fake, region_ids, amount["city"])
    district_rows = fill_districts(cur, fake, city_rows, amount["district"])
    parking_rows = fill_parkings(cur, district_rows, amount["parking"])

    class_id_by_name = fill_car_classes(cur)
    price_rows = fill_price_list(cur, region_ids, class_id_by_name)
    car_rows = fill_cars(cur, fake, region_ids, class_id_by_name, amount["car"])

    sc_rows = fill_sc(cur, fake, district_rows, amount["sc"])
    service_rows = fill_services(cur)
    service_sc_rows = fill_service_sc(cur, sc_rows, service_rows)
    visit_rows = fill_visit_sc(cur, fake, car_rows)
    visit_links = fill_visit_sc_per_service_sc(cur, fake, visit_rows, service_sc_rows)
    maintenance_ids = fill_maintenance_info(cur, fake, visit_rows)

    role_id_by_name = fill_roles(cur)
    account_rows, employee_rows, renter_rows = fill_accounts_and_people(
        cur,
        fake,
        role_id_by_name,
        amount["employee"],
        amount["renter"],
    )
    action_ids = fill_actions(cur, fake, account_rows)

    card_rows = fill_cards(cur, fake, renter_rows)
    booking_rows = fill_bookings(cur, car_rows, renter_rows)
    gps_rows = fill_gps(cur, booking_rows)
    fine_rows = fill_fines(cur, fake, booking_rows)
    debiting_ids = fill_debitings(cur, booking_rows, fine_rows, card_rows)

    return {
        "region": len(region_ids),
        "city": len(city_rows),
        "district": len(district_rows),
        "parking": len(parking_rows),
        "car_class": len(class_id_by_name),
        "price_list": len(price_rows),
        "car": len(car_rows),
        "sc": len(sc_rows),
        "service": len(service_rows),
        "service_sc": len(service_sc_rows),
        "visit_sc": len(visit_rows),
        "visit_sc_per_service_sc": len(visit_links),
        "maintenance_info": len(maintenance_ids),
        "role": len(role_id_by_name),
        "account": len(account_rows),
        "employee": len(employee_rows),
        "renter": len(renter_rows),
        "action": len(action_ids),
        "card": len(card_rows),
        "booking": len(booking_rows),
        "gps": len(gps_rows),
        "fine": len(fine_rows),
        "debiting": len(debiting_ids),
    }

