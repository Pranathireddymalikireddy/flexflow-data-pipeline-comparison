
import pandas as pd

from src.config import RAW_DIR


def load_customers():
    file_path = RAW_DIR / "customers.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    customers = pd.read_csv(file_path)

    if customers.empty:
        raise ValueError("Customers dataset is empty!")

    print(f"Customers loaded: {len(customers)}")

    return customers


def load_orders():
    file_path = RAW_DIR / "orders.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    orders = pd.read_csv(file_path)

    if orders.empty:
        raise ValueError("Orders dataset is empty!")

    print(f"Orders loaded: {len(orders)}")

    return orders


def main():
    print("Starting Data Ingestion...")

    customers = load_customers()
    orders = load_orders()

    print("\nData Ingestion Completed Successfully!")

    print("\nCustomers Preview:")
    print(customers.head())

    print("\nOrders Preview:")
    print(orders.head())


if __name__ == "__main__":
    main()
