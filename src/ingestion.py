
import pandas as pd

from src.config import (
    CUSTOMER_FILE,
    ORDER_FILE
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


def load_csv(file_path, required_columns, dataset_name):

    if not file_path.exists():
        raise FileNotFoundError(
            f"{dataset_name} file not found: {file_path}"
        )

    try:
        data = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError(
            f"{dataset_name} file is empty or has no header."
        )
    except pd.errors.ParserError as error:
        raise ValueError(
            f"Malformed {dataset_name} CSV: {error}"
        )

    missing_columns = set(required_columns) - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing columns: "
            f"{sorted(missing_columns)}"
        )

    # Add source traceability information
    data["source_file"] = file_path.name

    # Header is record 1, so data starts at record 2
    data["source_record_number"] = range(2, len(data) + 2)

    print(
        f"{dataset_name} loaded successfully: {len(data)} records"
    )

    return data


def load_customers():
    return load_csv(
        CUSTOMER_FILE,
        CUSTOMER_COLUMNS,
        "Customers"
    )


def load_orders():
    return load_csv(
        ORDER_FILE,
        ORDER_COLUMNS,
        "Orders"
    )


def main():

    print("Starting Data Ingestion...\n")

    customers = load_customers()
    orders = load_orders()

    print("\nCustomers Preview:")
    print(customers.head())

    print("\nOrders Preview:")
    print(orders.head())

    print("\nData Ingestion Completed Successfully!")


if __name__ == "__main__":
    main()
