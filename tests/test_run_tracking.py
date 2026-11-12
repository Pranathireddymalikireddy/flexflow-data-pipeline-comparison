
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.schema import initialize_database
from src.comparison_runner import (
    create_pipeline_run,
    log_rejected_records,
    complete_pipeline_run
)


class TestRunTracking(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.db_patch = patch(
            "src.schema.DB_PATH",
            self.db_path
        )
        self.db_patch.start()

        initialize_database()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_rejected_record_logging(self):

        run_id = create_pipeline_run(
            "Tracking Test",
            2,
            1
        )

        rejected_customers = pd.DataFrame(columns=[
            "customer_id",
            "source_file",
            "source_record_number",
            "rejection_reason"
        ])

        rejected_orders = pd.DataFrame([{
            "order_id": 101,
            "customer_id": "C9999",
            "source_file": "orders.csv",
            "source_record_number": 5,
            "rejection_reason": "Customer ID does not exist"
        }])

        log_rejected_records(
            run_id,
            rejected_customers,
            rejected_orders
        )

        complete_pipeline_run(
            run_id,
            "SUCCESS",
            inserted_count=1
        )

        import sqlite3

        connection = sqlite3.connect(self.db_path)

        record = connection.execute("""
            SELECT
                run_id,
                source_file,
                source_record_number,
                record_type,
                rejection_reason
            FROM rejected_records
        """).fetchone()

        connection.close()

        self.assertEqual(record[0], run_id)
        self.assertEqual(record[1], "orders.csv")
        self.assertEqual(record[2], 5)
        self.assertEqual(record[3], "ORDER")
        self.assertEqual(
            record[4],
            "Customer ID does not exist"
        )


if __name__ == "__main__":
    unittest.main()
