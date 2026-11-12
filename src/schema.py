
import sqlite3

from src.config import (
    DB_PATH,
    CUSTOMER_TABLE,
    ORDER_TABLE,
    RUN_HISTORY_TABLE,
    REJECT_TABLE
)


def get_connection():

    connection = sqlite3.connect(DB_PATH)

    # Enable foreign key validation
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Customer target table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {CUSTOMER_TABLE} (
                customer_id TEXT PRIMARY KEY
            )
        """)

        # Order target table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {ORDER_TABLE} (
                order_id INTEGER PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (customer_id)
                    REFERENCES {CUSTOMER_TABLE}(customer_id)
            )
        """)

        # Index for date-based partition operations
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_orders_order_date
            ON {ORDER_TABLE}(order_date)
        """)

        # Pipeline execution history
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {RUN_HISTORY_TABLE} (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                input_count INTEGER DEFAULT 0,
                inserted_count INTEGER DEFAULT 0,
                updated_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)

        # Rejected record history
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {REJECT_TABLE} (
                reject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                source_file TEXT,
                source_record_number INTEGER,
                record_type TEXT NOT NULL,
                rejection_reason TEXT NOT NULL,
                raw_record TEXT,

                FOREIGN KEY (run_id)
                    REFERENCES {RUN_HISTORY_TABLE}(run_id)
            )
        """)

        connection.commit()

        print("Database initialized successfully!")
        print("Tables created or verified:")
        print("-", CUSTOMER_TABLE)
        print("-", ORDER_TABLE)
        print("-", RUN_HISTORY_TABLE)
        print("-", REJECT_TABLE)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def show_database_schema():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        tables = [
            CUSTOMER_TABLE,
            ORDER_TABLE,
            RUN_HISTORY_TABLE,
            REJECT_TABLE
        ]

        print("\nDATABASE SCHEMA")

        for table in tables:

            cursor.execute(
                f"PRAGMA table_info({table})"
            )

            columns = cursor.fetchall()

            print(f"\nTable: {table}")

            for column in columns:
                print(
                    f"Column: {column[1]}, "
                    f"Type: {column[2]}, "
                    f"Primary Key: {column[5]}"
                )

    finally:
        connection.close()


if __name__ == "__main__":

    initialize_database()
    show_database_schema()
