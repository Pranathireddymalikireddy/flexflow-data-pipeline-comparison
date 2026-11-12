import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.schema import initialize_database, get_connection
from src.publish_strategies import (
    full_refresh,
    incremental_merge,
    partition_replacement,
    get_target_counts
)


def create_customers(*customer_ids):
    return pd.DataFrame({
        "customer_id": list(customer_ids)
    })


def create_orders(records):
    return pd.DataFrame(
        records,
        columns=[
            "order_id",
            "customer_id",
            "order_date",
            "amount",
            "status",
            "updated_at"
        ]
    )


class TestPublishStrategies(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = str(
            Path(self.temp_dir.name) / "test_pipeline.db"
        )

        self.db_patch = patch(
            "src.schema.DB_PATH",
            self.db_path
        )

        self.db_patch.start()

        initialize_database()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def get_orders(self):
        connection = get_connection()

        try:
            return connection.execute("""
                SELECT order_id, customer_id, order_date,
                       amount, status, updated_at
                FROM orders
                ORDER BY order_id
            """).fetchall()
        finally:
            connection.close()

    def test_full_refresh(self):

        customers = create_customers("C001", "C002")

        orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Completed", "2026-01-01 10:00:00"),
            (2, "C002", "2026-01-02", 2000,
             "Pending", "2026-01-02 10:00:00")
        ])

        full_refresh(customers, orders)

        counts = get_target_counts()

        self.assertEqual(counts["customers"], 2)
        self.assertEqual(counts["orders"], 2)

    def test_incremental_merge_inserts_new_records(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Pending", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        new_orders = create_orders([
            (2, "C001", "2026-01-02", 2000,
             "Completed", "2026-01-02 10:00:00")
        ])

        incremental_merge(customers, new_orders)

        counts = get_target_counts()

        self.assertEqual(counts["orders"], 2)

    def test_incremental_merge_updates_newer_records(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Pending", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        updated_orders = create_orders([
            (1, "C001", "2026-01-01", 1500,
             "Completed", "2026-01-01 12:00:00")
        ])

        incremental_merge(customers, updated_orders)

        result = self.get_orders()

        self.assertEqual(result[0][3], 1500)
        self.assertEqual(result[0][4], "Completed")

    def test_incremental_merge_ignores_older_records(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1500,
             "Completed", "2026-01-01 12:00:00")
        ])

        full_refresh(customers, initial_orders)

        older_orders = create_orders([
            (1, "C001", "2026-01-01", 500,
             "Pending", "2026-01-01 10:00:00")
        ])

        incremental_merge(customers, older_orders)

        result = self.get_orders()

        self.assertEqual(result[0][3], 1500)
        self.assertEqual(result[0][4], "Completed")

    def test_partition_replacement_preserves_other_dates(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Pending", "2026-01-01 10:00:00"),
            (2, "C001", "2026-01-02", 2000,
             "Pending", "2026-01-02 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        replacement_orders = create_orders([
            (3, "C001", "2026-01-01", 3000,
             "Completed", "2026-01-01 15:00:00")
        ])

        partition_replacement(
            customers,
            replacement_orders
        )

        result = self.get_orders()

        self.assertEqual(len(result), 2)

        order_ids = [row[0] for row in result]

        self.assertIn(2, order_ids)
        self.assertIn(3, order_ids)
        self.assertNotIn(1, order_ids)

    def test_failed_refresh_rolls_back(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Completed", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        invalid_orders = create_orders([
            (2, "C001", "2026-01-02", -500,
             "Pending", "2026-01-02 10:00:00")
        ])

        with self.assertRaises(Exception):
            full_refresh(customers, invalid_orders)

        result = self.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)
        self.assertEqual(result[0][3], 1000)

    def test_duplicate_order_id_uses_newer_timestamp(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Pending", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        duplicate_orders = create_orders([
            (1, "C001", "2026-01-01", 2000,
             "Completed", "2026-01-01 12:00:00"),
            (1, "C001", "2026-01-01", 1500,
             "Pending", "2026-01-01 11:00:00")
        ])

        incremental_merge(customers, duplicate_orders)

        result = self.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 2000)

    def test_incremental_merge_rolls_back_on_failure(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Completed", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        invalid_orders = create_orders([
            (2, "C001", "2026-01-02", 2000,
             "Pending", "2026-01-02 10:00:00"),
            (3, "C001", "2026-01-02", -500,
             "Pending", "2026-01-02 11:00:00")
        ])

        with self.assertRaises(Exception):
            incremental_merge(customers, invalid_orders)

        result = self.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)

    def test_partition_replacement_rolls_back_on_failure(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Completed", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        invalid_orders = create_orders([
            (2, "C001", "2026-01-01", 2000,
             "Pending", "2026-01-01 11:00:00"),
            (3, "C001", "2026-01-01", -500,
             "Pending", "2026-01-01 12:00:00")
        ])

        with self.assertRaises(Exception):
            partition_replacement(customers, invalid_orders)

        result = self.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)
        self.assertEqual(result[0][3], 1000)

    def test_retry_after_failure_succeeds(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Completed", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        invalid_orders = create_orders([
            (2, "C001", "2026-01-02", -500,
             "Pending", "2026-01-02 10:00:00")
        ])

        with self.assertRaises(Exception):
            incremental_merge(customers, invalid_orders)

        valid_orders = create_orders([
            (2, "C001", "2026-01-02", 2000,
             "Completed", "2026-01-02 11:00:00")
        ])

        incremental_merge(customers, valid_orders)

        counts = get_target_counts()

        self.assertEqual(counts["orders"], 2)

        # Retry the same successful input.
        incremental_merge(customers, valid_orders)

        counts = get_target_counts()

        self.assertEqual(counts["orders"], 2)

    def test_out_of_order_arrival_preserves_latest_record(self):

        customers = create_customers("C001")

        initial_orders = create_orders([
            (1, "C001", "2026-01-01", 1000,
             "Pending", "2026-01-01 10:00:00")
        ])

        full_refresh(customers, initial_orders)

        # First, a newer version arrives.
        newer_orders = create_orders([
            (1, "C001", "2026-01-01", 2000,
             "Completed", "2026-01-01 12:00:00")
        ])

        incremental_merge(customers, newer_orders)

        # Then, an older version arrives late.
        late_orders = create_orders([
            (1, "C001", "2026-01-01", 500,
             "Pending", "2026-01-01 09:00:00")
        ])

        incremental_merge(customers, late_orders)

        result = self.get_orders()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 2000)
        self.assertEqual(result[0][4], "Completed")
        self.assertEqual(
            result[0][5],
            "2026-01-01 12:00:00"
        )




if __name__ == "__main__":
    unittest.main(verbosity=2)