
import time
import pandas as pd

import src.schema as schema

from src.config import (
    BENCHMARK_SIZES,
    DB_PATH,
    REPORTS_DIR,
    CUSTOMER_FILE,
    ORDER_FILE,
    CLEAN_CUSTOMER_FILE,
    CLEAN_ORDER_FILE,
    REJECTED_CUSTOMER_FILE,
    REJECTED_ORDER_FILE
)

from src.data_generator import generate_data
from src.comparison_runner import prepare_data

from src.publish_strategies import (
    full_refresh,
    incremental_merge,
    partition_replacement
)


FILES_TO_PRESERVE = [
    CUSTOMER_FILE,
    ORDER_FILE,
    CLEAN_CUSTOMER_FILE,
    CLEAN_ORDER_FILE,
    REJECTED_CUSTOMER_FILE,
    REJECTED_ORDER_FILE
]


def backup_files():
    backups = {}

    for path in FILES_TO_PRESERVE:
        if path.exists():
            backups[path] = path.read_bytes()

    return backups


def restore_files(backups):
    for path, content in backups.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_database():
    connection = schema.get_connection()

    try:
        customers = pd.read_sql_query(
            "SELECT * FROM customers ORDER BY customer_id",
            connection
        )

        orders = pd.read_sql_query(
            "SELECT * FROM orders ORDER BY order_id",
            connection
        )

        return customers, orders

    finally:
        connection.close()


def equivalent_results(reference, actual):
    try:
        pd.testing.assert_frame_equal(
            reference[0],
            actual[0],
            check_dtype=False
        )

        pd.testing.assert_frame_equal(
            reference[1],
            actual[1],
            check_dtype=False
        )

        return True

    except AssertionError:
        return False




def create_workload(customers, final_orders):

    initial_count = int(len(final_orders) * 0.80)

    initial_orders = final_orders.iloc[:initial_count].copy()

    new_orders = final_orders.iloc[initial_count:].copy()

    # Select only 10 date partitions for changes
    all_dates = sorted(final_orders["order_date"].unique())

    affected_dates = all_dates[-10:]

    # Keep updates within the selected partitions
    candidate_updates = initial_orders[
        initial_orders["order_date"].isin(affected_dates)
    ].copy()

    update_count = int(len(initial_orders) * 0.20)

    updated_orders = candidate_updates.sample(
        n=update_count,
        random_state=42
    ).copy()

    updated_orders["amount"] = (
        updated_orders["amount"] * 1.05
    ).round(2)

    updated_orders["status"] = "Delivered"

    updated_orders["updated_at"] = (
        pd.to_datetime(updated_orders["updated_at"])
        + pd.Timedelta(days=1)
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Place new orders only in the selected partitions
    new_orders["order_date"] = [
        affected_dates[i % len(affected_dates)]
        for i in range(len(new_orders))
    ]

    delta_orders = pd.concat(
        [updated_orders, new_orders],
        ignore_index=True
    )

    # Construct the expected final dataset
    expected_final_orders = pd.concat(
        [
            initial_orders.drop(index=updated_orders.index),
            updated_orders,
            new_orders
        ],
        ignore_index=True
    )

    # Include complete snapshots for affected dates
    replacement_orders = expected_final_orders[
        expected_final_orders["order_date"].isin(affected_dates)
    ].copy()

    return (
        expected_final_orders,
        initial_orders,
        delta_orders,
        replacement_orders,
        affected_dates
    )


    # 80% of records form the existing database
    initial_count = int(len(final_orders) * 0.80)

    initial_orders = final_orders.iloc[:initial_count].copy()

    # Update 20% of existing orders
    update_count = max(1, int(len(initial_orders) * 0.20))

    updated_orders = initial_orders.sample(
        n=update_count,
        random_state=42
    ).copy()

    updated_orders["amount"] = (
        updated_orders["amount"] * 1.05
    ).round(2)

    updated_orders["status"] = "Delivered"

    updated_orders["updated_at"] = (
        pd.to_datetime(updated_orders["updated_at"])
        + pd.Timedelta(days=1)
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Remaining 20% are new orders
    new_orders = final_orders.iloc[initial_count:].copy()

    # Delta contains only updated and new records
    delta_orders = pd.concat(
        [updated_orders, new_orders],
        ignore_index=True
    )

    # Partition replacement needs complete snapshots
    # for every date touched by the delta
    affected_dates = delta_orders["order_date"].unique()

    replacement_orders = final_orders[
        final_orders["order_date"].isin(affected_dates)
    ].copy()

    return (
        initial_orders,
        delta_orders,
        replacement_orders,
        affected_dates
    )


def run_benchmark():

    results = []
    backups = backup_files()
    original_db_path = schema.DB_PATH

    try:

        for size in BENCHMARK_SIZES:

            print("\n" + "=" * 65)
            print(f"INCREMENTAL WORKLOAD: {size:,} FINAL ORDERS")
            print("=" * 65)

            generate_data(n_orders=size, seed=42)

            customers, final_orders = prepare_data()

            (
    expected_final_orders,
    initial_orders,
    delta_orders,
    replacement_orders,
    affected_dates
) = create_workload(customers, final_orders)

            print(f"\nInitial orders: {len(initial_orders):,}")
            print(f"Updated orders: {int(len(initial_orders) * 0.20):,}")
            print(f"New orders: {len(final_orders) - len(initial_orders):,}")
            print(f"Delta records: {len(delta_orders):,}")
            print(f"Affected date partitions: {len(affected_dates)}")
            print(f"Replacement snapshot records: {len(replacement_orders):,}")

            strategies = {
                "Full Refresh": (
    full_refresh,
    expected_final_orders
),
                "Incremental Merge": (
                    incremental_merge,
                    delta_orders
                ),
                "Partition Replacement": (
                    partition_replacement,
                    replacement_orders
                )
            }

            reference_result = None

            for strategy_name, (strategy_function, input_orders) in strategies.items():

                print(f"\nRunning {strategy_name}...")

                database_path = (
                    DB_PATH.parent
                    / f"incremental_{size}_{strategy_name.lower().replace(' ', '_')}.db"
                )

                if database_path.exists():
                    database_path.unlink()

                try:
                    schema.DB_PATH = database_path

                    # Create an identical initial database
                    schema.initialize_database()
                    full_refresh(customers, initial_orders)

                    # Measure only the change-processing operation
                    start_time = time.perf_counter()

                    strategy_function(customers, input_orders)

                    runtime = time.perf_counter() - start_time

                    actual_result = read_database()

                    if strategy_name == "Full Refresh":
                        reference_result = actual_result
                        equivalent = True
                    else:
                        equivalent = equivalent_results(
                            reference_result,
                            actual_result
                        )

                    actual_customers, actual_orders = actual_result

                    status = (
                        "SUCCESS"
                        if equivalent
                        else "RESULT MISMATCH"
                    )

                    results.append({
                        "dataset_size": size,
                        "strategy": strategy_name,
                        "initial_orders": len(initial_orders),
                        "delta_orders": len(input_orders),
                        "affected_partitions": (
                            len(affected_dates)
                            if strategy_name == "Partition Replacement"
                            else None
                        ),
                        "runtime_seconds": round(runtime, 6),
                        "final_customers": len(actual_customers),
                        "final_orders": len(actual_orders),
                        "total_amount": round(
                            float(actual_orders["amount"].sum()),
                            2
                        ),
                        "equivalent_to_full_refresh": equivalent,
                        "status": status
                    })

                    print(f"Execution time: {runtime:.6f} seconds")
                    print(f"Final orders: {len(actual_orders):,}")
                    print(f"Equivalent results: {equivalent}")
                    print(f"Status: {status}")

                except Exception as error:

                    print(f"ERROR: {error}")

                    results.append({
                        "dataset_size": size,
                        "strategy": strategy_name,
                        "initial_orders": len(initial_orders),
                        "delta_orders": len(input_orders),
                        "affected_partitions": None,
                        "runtime_seconds": None,
                        "final_customers": None,
                        "final_orders": None,
                        "total_amount": None,
                        "equivalent_to_full_refresh": False,
                        "status": f"FAILED: {error}"
                    })

                finally:
                    schema.DB_PATH = original_db_path

        report = pd.DataFrame(results)

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        report_path = (
            REPORTS_DIR / "incremental_workload_comparison.csv"
        )

        report.to_csv(report_path, index=False)

        print("\n" + "=" * 65)
        print("INCREMENTAL WORKLOAD BENCHMARK COMPLETED")
        print("=" * 65)

        print(report.to_string(index=False))

        print(f"\nReport saved to: {report_path}")

    finally:

        schema.DB_PATH = original_db_path
        restore_files(backups)

        print("\nOriginal CSV files have been restored.")


if __name__ == "__main__":
    run_benchmark()
