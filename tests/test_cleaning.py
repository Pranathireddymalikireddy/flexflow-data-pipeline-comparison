
import unittest
import pandas as pd

from src.cleaning import clean_customers, clean_orders


class TestDataCleaning(unittest.TestCase):

    def test_valid_customers(self):

        customers = pd.DataFrame({
            "customer_id": ["C0001", "C0002", "C0003"]
        })

        valid, rejected = clean_customers(customers)

        self.assertEqual(len(valid), 3)
        self.assertEqual(len(rejected), 0)

    def test_duplicate_customers(self):

        customers = pd.DataFrame({
            "customer_id": ["C0001", "C0001", "C0002"]
        })

        valid, rejected = clean_customers(customers)

        self.assertEqual(len(valid), 2)
        self.assertEqual(len(rejected), 1)

    def test_missing_customer_id(self):

        customers = pd.DataFrame({
            "customer_id": ["C0001", None, "C0003"]
        })

        valid, rejected = clean_customers(customers)

        self.assertEqual(len(valid), 2)
        self.assertEqual(len(rejected), 1)

    def test_invalid_orders(self):

        orders = pd.DataFrame({
            "order_id": [1, 2, 3, 4],
            "customer_id": [
                "C0001", "C0001", "C9999", "C0001"
            ],
            "order_date": [
                "2026-10-01",
                "2026-10-02",
                "2026-10-03",
                "invalid-date"
            ],
            "amount": [500, -100, 300, 400],
            "status": [
                "Delivered", "Pending",
                "Shipped", "Delivered"
            ],
            "updated_at": [
                "2026-10-01T10:00:00",
                "2026-10-02T10:00:00",
                "2026-10-03T10:00:00",
                "2026-10-04T10:00:00"
            ]
        })

        valid, rejected = clean_orders(
            orders,
            {"C0001"}
        )

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 3)

    def test_invalid_status(self):

        orders = pd.DataFrame({
            "order_id": [1],
            "customer_id": ["C0001"],
            "order_date": ["2026-10-01"],
            "amount": [500],
            "status": ["Unknown"],
            "updated_at": ["2026-10-01T10:00:00"]
        })

        valid, rejected = clean_orders(
            orders,
            {"C0001"}
        )

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)

    def test_empty_customers(self):

        customers = pd.DataFrame({
            "customer_id": []
        })

        valid, rejected = clean_customers(customers)

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 0)

    def test_empty_orders(self):

        orders = pd.DataFrame(columns=[
            "order_id",
            "customer_id",
            "order_date",
            "amount",
            "status",
            "updated_at"
        ])

        valid, rejected = clean_orders(
            orders,
            {"C0001"}
        )

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 0)

    def test_malformed_order_values(self):

        orders = pd.DataFrame({
            "order_id": ["invalid"],
            "customer_id": ["C0001"],
            "order_date": ["not-a-date"],
            "amount": ["not-a-number"],
            "status": ["Delivered"],
            "updated_at": ["invalid-timestamp"]
        })

        valid, rejected = clean_orders(
            orders,
            {"C0001"}
        )

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn(
            "Missing or invalid order ID",
            rejected.iloc[0]["rejection_reason"]
        )
        self.assertIn(
            "Invalid order amount",
            rejected.iloc[0]["rejection_reason"]
        )

    def test_invalid_customer_reference(self):

        orders = pd.DataFrame({
            "order_id": [101, 102],
            "customer_id": ["C0001", "C9999"],
            "order_date": [
                "2026-10-01",
                "2026-10-02"
            ],
            "amount": [500, 300],
            "status": ["Delivered", "Pending"],
            "updated_at": [
                "2026-10-01T10:00:00",
                "2026-10-02T10:00:00"
            ]
        })

        valid, rejected = clean_orders(
            orders,
            {"C0001"}
        )

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)

        self.assertEqual(
            rejected.iloc[0]["customer_id"],
            "C9999"
        )

        self.assertIn(
            "Customer ID does not exist",
            rejected.iloc[0]["rejection_reason"]
        )




if __name__ == "__main__":
    unittest.main()
