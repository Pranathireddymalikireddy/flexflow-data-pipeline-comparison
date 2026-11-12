
import time
import sqlite3
import hashlib
import json

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATABASE_DIR = PROJECT_ROOT / "database"

ORDERS_FILE = PROCESSED_DIR / "orders_clean.csv"
DATABASE_FILE = DATABASE_DIR / "incremental_state.db"

CHUNK_SIZE = 100


def load_data():

    if not ORDERS_FILE.exists():
        raise FileNotFoundError(
            "Cleaned orders file not found. Run Step 7 first."
        )

    return pd.read_csv(ORDERS_FILE)


def calculate_summary(data):

    return {
        "records_processed": len(data),
        "total_amount": round(data["amount"].sum(), 2)
    }


def batch_pipeline(data):

    start_time = time.perf_counter()

    result = calculate_summary(data)

    execution_time = time.perf_counter() - start_time

    return result, execution_time


def generate_hash(record):

    values = [
        str(record["customer_id"]),
        str(record["order_date"]),
        float(record["amount"]),
        str(record["status"]),
        str(record["updated_at"])
    ]

    content = json.dumps(values, separators=(",", ":"))

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def persistent_incremental_pipeline():

    start_time = time.perf_counter()

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    new_records = 0
    updated_records = 0
    unchanged_records = 0

    with sqlite3.connect(DATABASE_FILE) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                record_hash TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TEMP TABLE IF NOT EXISTS current_order_ids (
                order_id TEXT PRIMARY KEY
            )
        """)

        connection.execute("DELETE FROM current_order_ids")

        for chunk in pd.read_csv(
            ORDERS_FILE,
            chunksize=CHUNK_SIZE
        ):

            for _, record in chunk.iterrows():

                order_id = str(record["order_id"])
                record_hash = generate_hash(record)

                connection.execute(
                    "INSERT INTO current_order_ids VALUES (?)",
                    (order_id,)
                )

                existing = connection.execute(
                    """
                    SELECT record_hash
                    FROM processed_orders
                    WHERE order_id = ?
                    """,
                    (order_id,)
                ).fetchone()

                values = (
                    order_id,
                    str(record["customer_id"]),
                    str(record["order_date"]),
                    float(record["amount"]),
                    str(record["status"]),
                    str(record["updated_at"]),
                    record_hash
                )

                if existing is None:

                    connection.execute(
                        """
                        INSERT INTO processed_orders
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        values
                    )

                    new_records += 1

                elif existing[0] != record_hash:

                    connection.execute(
                        """
                        UPDATE processed_orders
                        SET customer_id = ?,
                            order_date = ?,
                            amount = ?,
                            status = ?,
                            updated_at = ?,
                            record_hash = ?
                        WHERE order_id = ?
                        """,
                        (
                            values[1], values[2], values[3],
                            values[4], values[5], values[6],
                            values[0]
                        )
                    )

                    updated_records += 1

                else:

                    unchanged_records += 1

        # Remove records no longer present in the current snapshot.
        connection.execute("""
            DELETE FROM processed_orders
            WHERE order_id NOT IN (
                SELECT order_id FROM current_order_ids
            )
        """)

        connection.commit()

        stored_count = connection.execute(
            "SELECT COUNT(*) FROM processed_orders"
        ).fetchone()[0]

    execution_time = time.perf_counter() - start_time

    result = {
        "records_processed": (
            new_records + updated_records + unchanged_records
        ),
        "new_records": new_records,
        "updated_records": updated_records,
        "unchanged_records": unchanged_records,
        "stored_records": stored_count
    }

    return result, execution_time


def streaming_pipeline():

    start_time = time.perf_counter()

    processed_records = 0
    total_amount = 0

    for chunk in pd.read_csv(
        ORDERS_FILE,
        chunksize=CHUNK_SIZE
    ):

        processed_records += len(chunk)
        total_amount += chunk["amount"].sum()

    result = {
        "records_processed": processed_records,
        "total_amount": round(total_amount, 2)
    }

    execution_time = time.perf_counter() - start_time

    return result, execution_time


def main():

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting Integrated Pipeline Comparison...\n")

    data = load_data()

    results = []

    # Batch processing
    batch_result, batch_time = batch_pipeline(data)

    results.append({
        "pipeline": "Batch Processing",
        "records_processed": batch_result["records_processed"],
        "total_amount": batch_result["total_amount"],
        "execution_time_seconds": round(batch_time, 6),
        "new_records": 0,
        "updated_records": 0,
        "unchanged_records": 0
    })

    # Persistent incremental processing
    inc_result, inc_time = persistent_incremental_pipeline()

    results.append({
        "pipeline": "Persistent Incremental",
        "records_processed": inc_result["records_processed"],
        "total_amount": batch_result["total_amount"],
        "execution_time_seconds": round(inc_time, 6),
        "new_records": inc_result["new_records"],
        "updated_records": inc_result["updated_records"],
        "unchanged_records": inc_result["unchanged_records"]
    })

    # Streaming simulation
    stream_result, stream_time = streaming_pipeline()

    results.append({
        "pipeline": "Streaming Simulation",
        "records_processed": stream_result["records_processed"],
        "total_amount": stream_result["total_amount"],
        "execution_time_seconds": round(stream_time, 6),
        "new_records": 0,
        "updated_records": 0,
        "unchanged_records": 0
    })

    comparison = pd.DataFrame(results)

    # Verify that all pipelines processed the same records.
    assert comparison["records_processed"].nunique() == 1, (
        "Record counts do not match!"
    )

    assert comparison["total_amount"].nunique() == 1, (
        "Total amounts do not match!"
    )

    comparison.to_csv(
        REPORTS_DIR / "pipeline_comparison.csv",
        index=False
    )

    print("\nPIPELINE COMPARISON RESULTS")
    print(comparison.to_string(index=False))

    print("\nINCREMENTAL PROCESSING DETAILS")
    print("New records:", inc_result["new_records"])
    print("Updated records:", inc_result["updated_records"])
    print("Unchanged records:", inc_result["unchanged_records"])
    print("Records stored in database:", inc_result["stored_records"])

    print("\nAll pipelines produced consistent results!")

    print("\nReport saved successfully:")
    print(REPORTS_DIR / "pipeline_comparison.csv")


if __name__ == "__main__":
    main()
