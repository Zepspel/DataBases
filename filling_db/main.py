import random
from faker import Faker
import psycopg

from config import DEFAULT_AMOUNT
from fillers import fill_all

def main():

    fake = Faker("en_US")
    Faker.seed(42)
    random.seed(42)

    conn = psycopg.connect(
        "dbname=carsharing user=postgres password=postgres host=localhost port=5432"
    )

    print("Connected to PostgreSQL")

    try:
        with conn.cursor() as cur:
            stats = fill_all(cur, fake, DEFAULT_AMOUNT)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Fill completed:")
    for table_name, count in stats.items():
        print(f"{table_name:28} {count}")


if __name__ == "__main__":
    main()