
import sqlite3
import hashlib
import json

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "orders_clean.csv"

DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_FILE = DATABASE_DIR / "incremental_state.db"

CHUNK_SIZE = 100


def create_database():

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                record_hash TEXT NOT NULL
            )
        """)

    print("Persistent database is ready.")


def generate_hash(record):

    record_data = [
        str(record["customer_id"]),
        str(record["order_date"]),
        float(record["amount"]),
        str(record["status"]),
        str(record["updated_at"])
    ]

    content = json.dumps(record_data, separators=(",", ":"))

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def process_incrementally():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Cleaned orders file not found. Run Step 7 first."
        )

    create_database()

    new_records = 0
    updated_records = 0
    unchanged_records = 0

    with sqlite3.connect(DATABASE_FILE) as connection:

        for chunk in pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE
        ):

            for _, record in chunk.iterrows():

                order_id = str(record["order_id"])

                record_hash = generate_hash(record)

                existing = connection.execute(
                    """
                    SELECT record_hash
                    FROM processed_orders
                    WHERE order_id = ?
                    """,
                    (order_id,)
                ).fetchone()

                values = (
                    order_id,
                    str(record["customer_id"]),
                    str(record["order_date"]),
                    float(record["amount"]),
                    str(record["status"]),
                    str(record["updated_at"]),
                    record_hash
                )

                if existing is None:

                    connection.execute(
                        """
                        INSERT INTO processed_orders
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        values
                    )

                    new_records += 1

                elif existing[0] != record_hash:

                    connection.execute(
                        """
                        UPDATE processed_orders
                        SET
                            customer_id = ?,
                            order_date = ?,
                            amount = ?,
                            status = ?,
                            updated_at = ?,
                            record_hash = ?
                        WHERE order_id = ?
                        """,
                        (
                            values[1],
                            values[2],
                            values[3],
                            values[4],
                            values[5],
                            values[6],
                            values[0]
                        )
                    )

                    updated_records += 1

                else:

                    unchanged_records += 1

            connection.commit()

        total_records = connection.execute(
            "SELECT COUNT(*) FROM processed_orders"
        ).fetchone()[0]

        total_amount = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM processed_orders"
        ).fetchone()[0]

    print("\nPERSISTENT INCREMENTAL PROCESSING RESULTS")

    print("-----------------------------------------")

    print("New records:", new_records)

    print("Updated records:", updated_records)

    print("Unchanged records:", unchanged_records)

    print("Total records stored:", total_records)

    print("Total order amount:", round(total_amount, 2))

    print("\nIncremental processing completed successfully!")


def main():

    print("Starting Persistent Incremental Processing...\n")

    process_incrementally()


if __name__ == "__main__":
    main()
