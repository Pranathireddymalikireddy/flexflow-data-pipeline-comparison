
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


STRATEGIES = {
    "Full Refresh": full_refresh,
    "Incremental Merge": incremental_merge,
    "Partition Replacement": partition_replacement
}

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

    for file_path in FILES_TO_PRESERVE:
        if file_path.exists():
            backups[file_path] = file_path.read_bytes()

    return backups


def restore_files(backups):
    for file_path, content in backups.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)


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

    finally:
        connection.close()

    return customers, orders


def results_are_equal(reference, actual):
    try:
        pd.testing.assert_frame_equal(
            reference[0],
            actual[0],
            check_dtype=False,
            check_like=False
        )

        pd.testing.assert_frame_equal(
            reference[1],
            actual[1],
            check_dtype=False,
            check_like=False
        )

        return True

    except AssertionError:
        return False


def run_benchmark():

    results = []
    backups = backup_files()

    original_db_path = schema.DB_PATH

    try:

        for size in BENCHMARK_SIZES:

            print("\n" + "=" * 60)
            print(f"BENCHMARKING DATASET: {size:,} ORDERS")
            print("=" * 60)

            # Generate dataset
            generate_data(n_orders=size, seed=42)

            # Load and clean dataset
            customers, orders = prepare_data()

            print(f"Valid customers: {len(customers)}")
            print(f"Valid orders: {len(orders)}")

            reference_result = None

            for strategy_name, strategy_function in STRATEGIES.items():

                print(f"\nRunning {strategy_name}...")

                try:
                    # Use a separate database for every strategy
                    database_path = (
                        DB_PATH.parent
                        / f"benchmark_{size}_{strategy_name.lower().replace(' ', '_')}.db"
                    )

                    if database_path.exists():
                        database_path.unlink()

                    schema.DB_PATH = database_path

                    # Initialize an empty database
                    schema.initialize_database()

                    # Measure publishing execution time
                    start_time = time.perf_counter()

                    strategy_function(customers, orders)

                    execution_time = time.perf_counter() - start_time

                    # Read published results
                    actual_result = read_database()

                    # Validate against Full Refresh
                    if strategy_name == "Full Refresh":
                        reference_result = actual_result
                        equivalent = True
                    else:
                        equivalent = results_are_equal(
                            reference_result,
                            actual_result
                        )

                    published_customers, published_orders = actual_result

                    total_amount = published_orders["amount"].sum()

                    partitions = published_orders[
                        "order_date"
                    ].nunique()

                    status = (
                        "SUCCESS"
                        if equivalent
                        else "RESULT MISMATCH"
                    )

                    results.append({
                        "dataset_size": size,
                        "strategy": strategy_name,
                        "runtime_seconds": round(execution_time, 6),
                        "customers_loaded": len(published_customers),
                        "orders_loaded": len(published_orders),
                        "total_amount": round(float(total_amount), 2),
                        "date_partitions": int(partitions),
                        "equivalent_to_full_refresh": equivalent,
                        "status": status
                    })

                    print(f"Execution time: {execution_time:.6f} seconds")
                    print(f"Orders loaded: {len(published_orders)}")
                    print(f"Equivalent results: {equivalent}")
                    print(f"Status: {status}")

                except Exception as error:

                    print(f"ERROR: {error}")

                    results.append({
                        "dataset_size": size,
                        "strategy": strategy_name,
                        "runtime_seconds": None,
                        "customers_loaded": None,
                        "orders_loaded": None,
                        "total_amount": None,
                        "date_partitions": None,
                        "equivalent_to_full_refresh": False,
                        "status": f"FAILED: {error}"
                    })

        # Save benchmark report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        report = pd.DataFrame(results)

        report_path = REPORTS_DIR / "strategy_scalability.csv"

        report.to_csv(report_path, index=False)

        print("\n" + "=" * 60)
        print("SCALABILITY BENCHMARK COMPLETED")
        print("=" * 60)

        print(report.to_string(index=False))

        print(f"\nReport saved to: {report_path}")

    finally:

        # Restore original database configuration
        schema.DB_PATH = original_db_path

        # Restore original source and cleaning files
        restore_files(backups)

        print("\nOriginal CSV files have been restored.")


if __name__ == "__main__":
    run_benchmark()
