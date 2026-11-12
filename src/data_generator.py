
import pandas as pd
import numpy as np
import argparse

from src.config import RAW_DIR, RANDOM_SEED, DEFAULT_RECORDS


def generate_data(n_orders=DEFAULT_RECORDS, seed=RANDOM_SEED):

    rng = np.random.default_rng(seed)

    n_customers = max(10, min(n_orders, max(10, n_orders // 10)))

    customers = pd.DataFrame({
        "customer_id": [
            f"C{i:04d}" for i in range(1, n_customers + 1)
        ]
    })

    order_dates = pd.Timestamp("2026-10-01") + pd.to_timedelta(
        rng.integers(0, 30, n_orders), unit="D"
    )

    orders = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1),
        "customer_id": rng.choice(
            customers["customer_id"], n_orders
        ),
        "order_date": order_dates.strftime("%Y-%m-%d"),
        "amount": np.round(
            rng.uniform(100, 10000, n_orders), 2
        ),
        "status": rng.choice(
            ["Pending", "Shipped", "Delivered", "Cancelled"],
            n_orders
        ),
        "updated_at": (
            order_dates
            + pd.to_timedelta(
                rng.integers(0, 72, n_orders), unit="h"
            )
        ).strftime("%Y-%m-%dT%H:%M:%S")
    })

    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    orders.to_csv(RAW_DIR / "orders.csv", index=False)

    print("Data generated successfully!")
    print(f"Customers: {len(customers)}")
    print(f"Orders: {len(orders)}")


    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate sample customer and order data"
    )

    parser.add_argument(
        "--records",
        type=int,
        default=DEFAULT_RECORDS,
        help="Number of orders to generate"
    )

    args = parser.parse_args()

    if args.records <= 0:
        parser.error("Number of records must be positive.")

    generate_data(n_orders=args.records)

