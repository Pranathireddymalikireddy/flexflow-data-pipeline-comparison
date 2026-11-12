
import time
import sqlite3
import pandas as pd
from datetime import datetime, timezone

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
    RUN_HISTORY_TABLE,
    REJECT_TABLE,
    REPORTS_DIR
)

def get_current_timestamp():
    return datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )


def create_pipeline_run(
    pipeline_name,
    input_count,
    rejected_count
):

    connection = get_connection()

    try:
        cursor = connection.execute(
            f"""
            INSERT INTO {RUN_HISTORY_TABLE} (
                pipeline_name,
                started_at,
                status,
                input_count,
                rejected_count
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pipeline_name,
                get_current_timestamp(),
                "RUNNING",
                input_count,
                rejected_count
            )
        )

        run_id = cursor.lastrowid

        connection.commit()

        return run_id

    finally:
        connection.close()


def log_rejected_records(
    run_id,
    rejected_customers,
    rejected_orders
):

    connection = get_connection()

    try:
        rejected_groups = [
            ("CUSTOMER", rejected_customers),
            ("ORDER", rejected_orders)
        ]

        for record_type, dataframe in rejected_groups:

            for _, record in dataframe.iterrows():

                source_file = record.get("source_file")
                source_number = record.get(
                    "source_record_number"
                )

                connection.execute(
                    f"""
                    INSERT INTO {REJECT_TABLE} (
                        run_id,
                        source_file,
                        source_record_number,
                        record_type,
                        rejection_reason,
                        raw_record
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        source_file,
                        None if pd.isna(source_number)
                        else int(source_number),
                        record_type,
                        str(record["rejection_reason"]),
                        record.to_json()
                    )
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def complete_pipeline_run(
    run_id,
    status,
    inserted_count=0,
    updated_count=0,
    error_message=None
):

    connection = get_connection()

    try:
        connection.execute(
            f"""
            UPDATE {RUN_HISTORY_TABLE}
            SET completed_at = ?,
                status = ?,
                inserted_count = ?,
                updated_count = ?,
                error_message = ?
            WHERE run_id = ?
            """,
            (
                get_current_timestamp(),
                status,
                inserted_count,
                updated_count,
                error_message,
                run_id
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


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

    return (
    valid_customers,
    valid_orders,
    rejected_customers,
    rejected_orders
)

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

    (
        customers,
        orders,
        rejected_customers,
        rejected_orders
    ) = prepare_data()

    input_count = (
    len(customers)
    + len(orders)
    + len(rejected_customers)
    + len(rejected_orders)
)
    rejected_count = (
        len(rejected_customers) + len(rejected_orders)
    )

    strategies = [
        ("Full Refresh", full_refresh),
        ("Incremental Merge", incremental_merge),
        ("Partition Replacement", partition_replacement)
    ]

    results = []
    reference_snapshot = None

    for strategy_name, strategy_function in strategies:

        print("\n" + "=" * 55)
        print("Running:", strategy_name)
        print("=" * 55)

        reset_target()

        run_id = create_pipeline_run(
            strategy_name,
            input_count,
            rejected_count
        )

        try:
            log_rejected_records(
                run_id,
                rejected_customers,
                rejected_orders
            )

            start_time = time.perf_counter()

            strategy_function(customers, orders)

            execution_time = time.perf_counter() - start_time

            target_customers, target_orders = read_target()

            metrics = calculate_metrics(
                target_customers,
                target_orders
            )

            if reference_snapshot is None:
                equivalent = True
                reference_snapshot = (
                    target_customers,
                    target_orders
                )
            else:
                equivalent = compare_results(
                    reference_snapshot,
                    (target_customers, target_orders)
                )

            status = "SUCCESS" if equivalent else "MISMATCH"

            complete_pipeline_run(
                run_id,
                status,
                inserted_count=(
                    len(target_customers) + len(target_orders)
                ),
                updated_count=0,
                error_message=(
                    None if equivalent
                    else "Strategy results differ from Full Refresh"
                )
            )

            results.append({
                "strategy": strategy_name,
                "run_id": run_id,
                "execution_time_seconds": round(
                    execution_time, 6
                ),
                "customer_count": metrics["customer_count"],
                "order_count": metrics["order_count"],
                "total_amount": metrics["total_amount"],
                "partition_count": metrics["partition_count"],
                "results_equivalent": equivalent,
                "status": status
            })

            print("Run ID:", run_id)
            print("Execution time:", round(execution_time, 6), "seconds")
            print("Customers:", metrics["customer_count"])
            print("Orders:", metrics["order_count"])
            print("Total amount:", metrics["total_amount"])
            print("Partitions:", metrics["partition_count"])
            print("Equivalent to Full Refresh:", equivalent)

        except Exception as error:

            complete_pipeline_run(
                run_id,
                "FAILED",
                error_message=str(error)
            )

            print("Pipeline failed:", str(error))
            raise

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
