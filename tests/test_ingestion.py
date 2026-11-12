
import unittest
import tempfile
from pathlib import Path

from src.ingestion import load_csv


class TestIngestionSchema(unittest.TestCase):

    def test_valid_schema(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            file_path = Path(temp_dir) / "customers.csv"
            file_path.write_text(
                "customer_id\nC0001\nC0002\n",
                encoding="utf-8"
            )

            data = load_csv(
                file_path,
                ["customer_id"],
                "Customers"
            )

            self.assertEqual(len(data), 2)
            self.assertIn("source_file", data.columns)
            self.assertIn(
                "source_record_number",
                data.columns
            )

    def test_missing_column(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            file_path = Path(temp_dir) / "customers.csv"
            file_path.write_text(
                "name\nPranathi\n",
                encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "missing columns"
            ):
                load_csv(
                    file_path,
                    ["customer_id"],
                    "Customers"
                )

    def test_unexpected_column(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            file_path = Path(temp_dir) / "customers.csv"
            file_path.write_text(
                "customer_id,phone_number\nC0001,9876543210\n",
                encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "unexpected columns"
            ):
                load_csv(
                    file_path,
                    ["customer_id"],
                    "Customers"
                )


if __name__ == "__main__":
    unittest.main()
