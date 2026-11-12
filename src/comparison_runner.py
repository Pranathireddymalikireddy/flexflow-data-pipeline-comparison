
import time
import sqlite3
import pandas as pd

from src.ingestion import load_customers, load_orders
from src.cleaning import clean_customers, clean_orders
from src.publish_strategies import (
    full_refresh,
    incremental_merge,
    partition_replacement
)
from src.schema import get_connection, initialize_database
from src.config import (
    CUSTOMER_TABLE,
    ORDER_TABLE,
    REPORTS_DIR
)


def prepare_data():

    print("\nPreparing source data...")

    customers = load_customers()
    orders = load_orders()

    valid_customers, rejected_customers = clean_customers(
        customers
    )

    valid_customer_ids = set(
        valid_customers["customer_id"].dropna()
    )

    valid_orders, rejected_orders = clean_orders(
        orders,
        valid_customer_ids
    )

    print("\nData preparation completed.")
    print("Valid customers:", len(valid_customers))
    print("Valid orders:", len(valid_orders))
    print("Rejected customers:", len(rejected_customers))
    print("Rejected orders:", len(rejected_orders))

    return valid_customers, valid_orders


def reset_target():

    connection = get_connection()

    try:
        connection.execute(
            f"DELETE FROM {ORDER_TABLE}"
        )

        connection.execute(
            f"DELETE FROM {CUSTOMER_TABLE}"
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def read_target():

    connection = get_connection()

    try:

        customers = pd.read_sql_query(
            f"""
            SELECT customer_id
            FROM {CUSTOMER_TABLE}
            ORDER BY customer_id
            """,
            connection
        )

        orders = pd.read_sql_query(
            f"""
            SELECT
                order_id,
                customer_id,
                order_date,
                amount,
                status,
                updated_at
            FROM {ORDER_TABLE}
            ORDER BY order_id
            """,
            connection
        )

        return customers, orders

    finally:
        connection.close()


def calculate_metrics(customers, orders):

    return {
        "customer_count": len(customers),
        "order_count": len(orders),
        "total_amount": round(
            float(orders["amount"].sum()), 2
        ),
        "partition_count": orders["order_date"].nunique()
    }


def compare_results(reference, actual):

    reference_customers, reference_orders = reference
    actual_customers, actual_orders = actual

    try:

        pd.testing.assert_frame_equal(
            reference_customers,
            actual_customers,
            check_dtype=False
        )

        pd.testing.assert_frame_equal(
            reference_orders,
            actual_orders,
            check_dtype=False,
            check_exact=False,
            rtol=1e-9,
            atol=1e-9
        )

        return True

    except AssertionError:
        return False


def run_comparison():

    initialize_database()

    customers, orders = prepare_data()

    strategies = [
        ("Full Refresh", full_refresh),
        ("Incremental Merge", incremental_merge),
        ("Partition Replacement", partition_replacement)
    ]

    results = []
    snapshots = {}

    reference_snapshot = None

    for strategy_name, strategy_function in strategies:

        print("\n" + "=" * 55)
        print("Running:", strategy_name)
        print("=" * 55)

        # Give every strategy the same initial target state
        reset_target()

        start_time = time.perf_counter()

        strategy_function(customers, orders)

        execution_time = time.perf_counter() - start_time

        target_customers, target_orders = read_target()

        metrics = calculate_metrics(
            target_customers,
            target_orders
        )

        snapshots[strategy_name] = (
            target_customers,
            target_orders
        )

        if reference_snapshot is None:
            reference_snapshot = snapshots[strategy_name]
            equivalent = True
        else:
            equivalent = compare_results(
                reference_snapshot,
                snapshots[strategy_name]
            )

        results.append({
            "strategy": strategy_name,
            "execution_time_seconds": round(
                execution_time, 6
            ),
            "customer_count": metrics["customer_count"],
            "order_count": metrics["order_count"],
            "total_amount": metrics["total_amount"],
            "partition_count": metrics["partition_count"],
            "results_equivalent": equivalent,
            "status": "SUCCESS" if equivalent else "MISMATCH"
        })

        print("Execution time:", round(execution_time, 6), "seconds")
        print("Customers:", metrics["customer_count"])
        print("Orders:", metrics["order_count"])
        print("Total amount:", metrics["total_amount"])
        print("Partitions:", metrics["partition_count"])
        print("Equivalent to Full Refresh:", equivalent)

    report = pd.DataFrame(results)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORTS_DIR / "strategy_comparison.csv"

    report.to_csv(report_path, index=False)

    print("\n" + "=" * 55)
    print("FINAL COMPARISON REPORT")
    print("=" * 55)

    print(report.to_string(index=False))

    print("\nReport saved to:", report_path)

    if report["status"].eq("SUCCESS").all():
        print("\nAll three strategies produced equivalent results!")
    else:
        raise AssertionError(
            "At least one strategy produced different results."
        )


if __name__ == "__main__":
    run_comparison()
