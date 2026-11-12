
import pandas as pd

from src.ingestion import load_customers, load_orders
from src.config import (
    PROCESSED_DIR,
    REJECTS_DIR,
    ALLOWED_ORDER_STATUSES,
    MIN_ORDER_AMOUNT
)


def add_reason(reasons, mask, message):
    reasons.loc[mask] = reasons.loc[mask].apply(
        lambda current: (
            f"{current}; {message}" if current else message
        )
    )


def clean_customers(customers):

    customers = customers.copy()

    reasons = pd.Series(
        "",
        index=customers.index,
        dtype="string"
    )

    customers["customer_id"] = (
        customers["customer_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

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

    valid = customers[reasons == ""].copy()
    rejected = customers[reasons != ""].copy()

    valid = valid.drop(columns=["rejection_reason"])

    return valid, rejected


def clean_orders(orders, valid_customer_ids):

    orders = orders.copy()

    reasons = pd.Series(
        "",
        index=orders.index,
        dtype="string"
    )

    # Clean customer ID and status
    orders["customer_id"] = (
        orders["customer_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    orders["status"] = (
        orders["status"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Convert data types
    orders["order_id"] = pd.to_numeric(
        orders["order_id"],
        errors="coerce"
    )

    orders["amount"] = pd.to_numeric(
        orders["amount"],
        errors="coerce"
    )

    orders["order_date_parsed"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    orders["updated_at_parsed"] = pd.to_datetime(
        orders["updated_at"],
        errors="coerce"
    )

    # Required field validation
    add_reason(
        reasons,
        orders["order_id"].isna(),
        "Missing or invalid order ID"
    )

    add_reason(
        reasons,
        orders["order_id"].notna()
        & (orders["order_id"] % 1 != 0),
        "Order ID must be an integer"
    )

    add_reason(
        reasons,
        orders["order_id"].notna()
        & (orders["order_id"] <= 0),
        "Order ID must be positive"
    )

    add_reason(
        reasons,
        orders["order_id"].notna()
        & orders["order_id"].duplicated(keep="first"),
        "Duplicate order ID"
    )

    add_reason(
        reasons,
        orders["customer_id"].isna(),
        "Missing customer ID"
    )

    add_reason(
        reasons,
        orders["customer_id"].notna()
        & ~orders["customer_id"].isin(valid_customer_ids),
        "Customer ID does not exist"
    )

    add_reason(
        reasons,
        orders["amount"].isna()
        | (orders["amount"] <= MIN_ORDER_AMOUNT),
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
        | ~orders["status"].isin(ALLOWED_ORDER_STATUSES),
        "Invalid order status"
    )

    # Separate valid and rejected records
    orders["rejection_reason"] = reasons

    valid = orders[reasons == ""].copy()
    rejected = orders[reasons != ""].copy()

    # Normalize valid output
    valid["order_id"] = valid["order_id"].astype("int64")

    valid["order_date"] = (
        valid["order_date_parsed"].dt.strftime("%Y-%m-%d")
    )

    valid["updated_at"] = (
        valid["updated_at_parsed"].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
    )

    valid = valid.drop(
        columns=[
            "order_date_parsed",
            "updated_at_parsed",
            "rejection_reason"
        ]
    )

    # Keep parsed fields out of rejected output too
    rejected = rejected.drop(
        columns=[
            "order_date_parsed",
            "updated_at_parsed"
        ]
    )

    return valid, rejected


def main():

    print("Starting Data Cleaning and Validation...\n")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTS_DIR.mkdir(parents=True, exist_ok=True)

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

    # Save cleaned data
    valid_customers.to_csv(
        PROCESSED_DIR / "customers_clean.csv",
        index=False
    )

    valid_orders.to_csv(
        PROCESSED_DIR / "orders_clean.csv",
        index=False
    )

    # Save rejected data with reasons and source information
    rejected_customers.to_csv(
        REJECTS_DIR / "customers_rejected.csv",
        index=False
    )

    rejected_orders.to_csv(
        REJECTS_DIR / "orders_rejected.csv",
        index=False
    )

    print("\nCUSTOMER SUMMARY")
    print("Input:", len(customers))
    print("Valid:", len(valid_customers))
    print("Rejected:", len(rejected_customers))

    print("\nORDER SUMMARY")
    print("Input:", len(orders))
    print("Valid:", len(valid_orders))
    print("Rejected:", len(rejected_orders))

    print("\nReconciliation")
    print(
        "Customers reconciled:",
        len(customers) == len(valid_customers) + len(rejected_customers)
    )
    print(
        "Orders reconciled:",
        len(orders) == len(valid_orders) + len(rejected_orders)
    )

    print("\nData cleaning completed successfully!")


if __name__ == "__main__":
    main()
