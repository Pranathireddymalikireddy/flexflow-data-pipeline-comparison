
import argparse
import pandas as pd
import numpy as np

from src.config import (
    RAW_DIR,
    RANDOM_SEED,
    DEFAULT_RECORDS,
    CUSTOMER_FILE,
    ORDER_FILE
)


def generate_data(n_orders=DEFAULT_RECORDS, seed=RANDOM_SEED):

    if n_orders <= 0:
        raise ValueError("Number of orders must be positive.")

    rng = np.random.default_rng(seed)

    # Generate customers
    n_customers = max(10, min(n_orders, max(10, n_orders // 10)))

    customers = pd.DataFrame({
        "customer_id": [
            f"C{i:04d}" for i in range(1, n_customers + 1)
        ]
    })

    # Generate order dates
    order_dates = pd.Timestamp("2026-10-01") + pd.to_timedelta(
        rng.integers(0, 30, n_orders),
        unit="D"
    )

    # Generate orders
    orders = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1),
        "customer_id": rng.choice(
            customers["customer_id"],
            n_orders
        ),
        "order_date": order_dates.strftime("%Y-%m-%d"),
        "amount": np.round(
            rng.uniform(100, 10000, n_orders),
            2
        ),
        "status": rng.choice(
            ["Pending", "Shipped", "Delivered", "Cancelled"],
            n_orders
        ),
        "updated_at": (
            order_dates
            + pd.to_timedelta(
                rng.integers(0, 72, n_orders),
                unit="h"
            )
        ).strftime("%Y-%m-%dT%H:%M:%S")
    })

    # Save source datasets
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    customers.to_csv(CUSTOMER_FILE, index=False)
    orders.to_csv(ORDER_FILE, index=False)

    print("\nData generated successfully!")
    print(f"Random seed: {seed}")
    print(f"Customers generated: {len(customers)}")
    print(f"Orders generated: {len(orders)}")
    print(f"Customer file: {CUSTOMER_FILE}")
    print(f"Order file: {ORDER_FILE}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate reproducible customer and order data"
    )

    parser.add_argument(
        "--records",
        type=int,
        default=DEFAULT_RECORDS,
        help="Number of orders to generate"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed for reproducible data"
    )

    args = parser.parse_args()

    if args.records <= 0:
        parser.error("Number of records must be positive.")

    generate_data(
        n_orders=args.records,
        seed=args.seed
    )
