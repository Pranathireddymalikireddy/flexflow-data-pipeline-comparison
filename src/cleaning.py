
import pandas as pd

from src.ingestion import load_customers, load_orders
from src.config import RAW_DIR


PROJECT_ROOT = RAW_DIR.parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REJECTS_DIR = PROJECT_ROOT / "data" / "rejects"


def check_columns(df, required_columns, dataset_name):
    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{dataset_name} is missing columns: {missing}"
        )


def add_reason(reasons, mask, message):
    reasons.loc[mask] = reasons.loc[mask].apply(
        lambda current: (
            f"{current}; {message}" if current else message
        )
    )


def clean_customers(customers):

    customers = customers.copy()

    check_columns(
        customers,
        ["customer_id"],
        "Customers"
    )

    customers["customer_id"] = (
        customers["customer_id"].astype("string").str.strip()
    )

    customers["customer_id"] = customers["customer_id"].replace(
        "", pd.NA
    )

    reasons = pd.Series("", index=customers.index, dtype="string")

    add_reason(
        reasons,
        customers["customer_id"].isna(),
        "Missing customer ID"
    )

    add_reason(
        reasons,
        customers["customer_id"].notna()
        & customers["customer_id"].duplicated(keep="first"),
        "Duplicate customer ID"
    )

    customers["rejection_reason"] = reasons

    valid = customers[reasons == ""].drop(
        columns=["rejection_reason"]
    )

    rejected = customers[reasons != ""]

    return valid, rejected


def clean_orders(orders, valid_customer_ids):

    orders = orders.copy()

    check_columns(
        orders,
        [
            "order_id",
            "customer_id",
            "order_date",
            "amount",
            "status",
            "updated_at"
        ],
        "Orders"
    )

    orders["customer_id"] = (
        orders["customer_id"].astype("string").str.strip()
    )

    orders["customer_id"] = orders["customer_id"].replace(
        "", pd.NA
    )

    orders["amount"] = pd.to_numeric(
        orders["amount"], errors="coerce"
    )

    orders["order_date_parsed"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )

    orders["updated_at_parsed"] = pd.to_datetime(
        orders["updated_at"], errors="coerce"
    )

    orders["status"] = (
        orders["status"].astype("string").str.strip().str.title()
    )

    allowed_statuses = [
        "Pending",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    reasons = pd.Series("", index=orders.index, dtype="string")

    add_reason(
        reasons,
        orders["order_id"].isna(),
        "Missing order ID"
    )

    add_reason(
        reasons,
        orders["order_id"].duplicated(keep="first"),
        "Duplicate order ID"
    )

    add_reason(
        reasons,
        orders["customer_id"].isna(),
        "Missing customer ID"
    )

    add_reason(
        reasons,
        ~orders["customer_id"].isin(valid_customer_ids),
        "Customer ID does not exist"
    )

    add_reason(
        reasons,
        orders["amount"].isna() | (orders["amount"] <= 0),
        "Invalid order amount"
    )

    add_reason(
        reasons,
        orders["order_date_parsed"].isna(),
        "Invalid order date"
    )

    add_reason(
        reasons,
        orders["updated_at_parsed"].isna(),
        "Invalid update timestamp"
    )

    add_reason(
        reasons,
        orders["status"].isna()
        | ~orders["status"].isin(allowed_statuses),
        "Invalid order status"
    )

    orders["rejection_reason"] = reasons

    valid = orders[reasons == ""].copy()
    rejected = orders[reasons != ""].copy()

    valid["order_date"] = (
        valid["order_date_parsed"].dt.strftime("%Y-%m-%d")
    )

    valid["updated_at"] = (
        valid["updated_at_parsed"].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
    )

    valid = valid.drop(
        columns=["order_date_parsed", "updated_at_parsed",
                 "rejection_reason"]
    )

    return valid, rejected


def main():

    print("Starting Data Cleaning and Validation...")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTS_DIR.mkdir(parents=True, exist_ok=True)

    customers = load_customers()
    orders = load_orders()

    clean_customer_data, rejected_customers = (
        clean_customers(customers)
    )

    valid_customer_ids = set(
        clean_customer_data["customer_id"]
    )

    clean_order_data, rejected_orders = clean_orders(
        orders, valid_customer_ids
    )

    clean_customer_data.to_csv(
        PROCESSED_DIR / "customers_clean.csv",
        index=False
    )

    clean_order_data.to_csv(
        PROCESSED_DIR / "orders_clean.csv",
        index=False
    )

    rejected_customers.to_csv(
        REJECTS_DIR / "customers_rejected.csv",
        index=False
    )

    rejected_orders.to_csv(
        REJECTS_DIR / "orders_rejected.csv",
        index=False
    )

    print("\nData Cleaning Completed Successfully!")

    print("\nCUSTOMER SUMMARY")
    print("Valid customers:", len(clean_customer_data))
    print("Rejected customers:", len(rejected_customers))

    print("\nORDER SUMMARY")
    print("Valid orders:", len(clean_order_data))
    print("Rejected orders:", len(rejected_orders))

    print("\nCleaned files saved in:", PROCESSED_DIR)
    print("Rejected files saved in:", REJECTS_DIR)


if __name__ == "__main__":
    main()
