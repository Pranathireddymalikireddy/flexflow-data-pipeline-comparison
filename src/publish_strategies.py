
import sqlite3
import pandas as pd

from src.schema import get_connection
from src.config import (
    CUSTOMER_TABLE,
    ORDER_TABLE
)


CUSTOMER_COLUMNS = [
    "customer_id"
]

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
    "updated_at"
]


def get_customer_records(customers):
    return list(
        customers[CUSTOMER_COLUMNS].itertuples(
            index=False,
            name=None
        )
    )


def get_order_records(orders):
    return list(
        orders[ORDER_COLUMNS].itertuples(
            index=False,
            name=None
        )
    )


def insert_customers(connection, customers):

    records = get_customer_records(customers)

    connection.executemany(
        f"""
        INSERT INTO {CUSTOMER_TABLE} (customer_id)
        VALUES (?)
        """,
        records
    )


def insert_orders(connection, orders):

    records = get_order_records(orders)

    connection.executemany(
        f"""
        INSERT INTO {ORDER_TABLE} (
            order_id,
            customer_id,
            order_date,
            amount,
            status,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        records
    )


def full_refresh(customers, orders):

    connection = get_connection()

    try:
        # Delete dependent records first
        connection.execute(
            f"DELETE FROM {ORDER_TABLE}"
        )

        connection.execute(
            f"DELETE FROM {CUSTOMER_TABLE}"
        )

        # Load the complete datasets
        insert_customers(connection, customers)
        insert_orders(connection, orders)

        connection.commit()

        print("Full Refresh completed successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def incremental_merge(customers, orders):

    connection = get_connection()

    try:
        # Add new customers without replacing existing ones
        customer_records = get_customer_records(customers)

        connection.executemany(
            f"""
            INSERT INTO {CUSTOMER_TABLE} (customer_id)
            VALUES (?)
            ON CONFLICT(customer_id) DO NOTHING
            """,
            customer_records
        )

        # Insert new orders or update only when incoming
        # updated_at is newer than the stored version
        order_records = get_order_records(orders)

        connection.executemany(
            f"""
            INSERT INTO {ORDER_TABLE} (
                order_id,
                customer_id,
                order_date,
                amount,
                status,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(order_id) DO UPDATE SET
                customer_id = excluded.customer_id,
                order_date = excluded.order_date,
                amount = excluded.amount,
                status = excluded.status,
                updated_at = excluded.updated_at

            WHERE excluded.updated_at > {ORDER_TABLE}.updated_at
            """,
            order_records
        )

        connection.commit()

        print("Incremental Merge completed successfully!")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def partition_replacement(customers, orders):

    connection = get_connection()

    try:
        # Ensure customer references exist
        customer_records = get_customer_records(customers)

        connection.executemany(
            f"""
            INSERT INTO {CUSTOMER_TABLE} (customer_id)
            VALUES (?)
            ON CONFLICT(customer_id) DO NOTHING
            """,
            customer_records
        )

        # Find the affected logical date partitions
        affected_dates = sorted(
            orders["order_date"].dropna().unique().tolist()
        )

        if not affected_dates:
            print("No order-date partitions to replace.")
        else:
            for partition_date in affected_dates:

                # Remove the existing partition
                connection.execute(
                    f"""
                    DELETE FROM {ORDER_TABLE}
                    WHERE order_date = ?
                    """,
                    (partition_date,)
                )

            # Load the complete replacement snapshot
            insert_orders(connection, orders)

        connection.commit()

        print("Partition Replacement completed successfully!")
        print("Partitions replaced:", len(affected_dates))

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_target_counts():

    connection = get_connection()

    try:
        customers_count = connection.execute(
            f"SELECT COUNT(*) FROM {CUSTOMER_TABLE}"
        ).fetchone()[0]

        orders_count = connection.execute(
            f"SELECT COUNT(*) FROM {ORDER_TABLE}"
        ).fetchone()[0]

        return {
            "customers": customers_count,
            "orders": orders_count
        }

    finally:
        connection.close()


if __name__ == "__main__":

    print("Publishing strategy module loaded successfully.")

    print("\nAvailable strategies:")
    print("1. full_refresh()")
    print("2. incremental_merge()")
    print("3. partition_replacement()")
    print("4. get_target_counts()")
