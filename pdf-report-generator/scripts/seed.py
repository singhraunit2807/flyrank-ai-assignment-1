from datetime import datetime, timedelta
from pathlib import Path
import random
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "report.db"

CUSTOMERS = ["Aarav", "Diya", "Kabir", "Anaya", "Vihaan", "Meera", "Arjun", "Ishita", "Rohan", "Kiara"]
PRODUCTS = ["Wireless Mouse", "Keyboard", "USB-C Hub", "Laptop Stand", "Webcam", "Headphones"]


def main() -> None:
    random.seed(42)
    now = datetime.now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS orders")
        conn.execute(
            """CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        for _ in range(200):
            created = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            conn.execute(
                "INSERT INTO orders(customer, product, amount, created_at) VALUES (?, ?, ?, ?)",
                (random.choice(CUSTOMERS), random.choice(PRODUCTS), round(random.uniform(5, 200), 2), created.isoformat(timespec="seconds")),
            )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"Seeded {count} orders into {DB_PATH}")


if __name__ == "__main__":
    main()
