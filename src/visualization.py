
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORTS_DIR = PROJECT_ROOT / "reports"

INPUT_FILE = REPORTS_DIR / "pipeline_comparison.csv"


def load_comparison_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Comparison report not found. "
            "Run Step 8 first."
        )

    data = pd.read_csv(INPUT_FILE)

    if data.empty:
        raise ValueError("Comparison report is empty.")

    required_columns = [
        "pipeline",
        "records_processed",
        "total_amount",
        "execution_time_seconds"
    ]

    missing = set(required_columns) - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    return data


def create_execution_time_chart(data):

    plt.figure(figsize=(9, 5))

    plt.bar(
        data["pipeline"],
        data["execution_time_seconds"]
    )

    plt.title("Pipeline Execution Time Comparison")
    plt.xlabel("Pipeline")
    plt.ylabel("Execution Time (Seconds)")
    plt.xticks(rotation=15)
    plt.tight_layout()

    plt.savefig(
        REPORTS_DIR / "execution_time_comparison.png"
    )

    plt.close()


def create_records_chart(data):

    plt.figure(figsize=(9, 5))

    plt.bar(
        data["pipeline"],
        data["records_processed"]
    )

    plt.title("Records Processed by Each Pipeline")
    plt.xlabel("Pipeline")
    plt.ylabel("Number of Records")
    plt.xticks(rotation=15)
    plt.tight_layout()

    plt.savefig(
        REPORTS_DIR / "records_processed_comparison.png"
    )

    plt.close()


def create_amount_chart(data):

    plt.figure(figsize=(9, 5))

    plt.bar(
        data["pipeline"],
        data["total_amount"]
    )

    plt.title("Total Order Amount Comparison")
    plt.xlabel("Pipeline")
    plt.ylabel("Total Order Amount")
    plt.xticks(rotation=15)
    plt.tight_layout()

    plt.savefig(
        REPORTS_DIR / "total_amount_comparison.png"
    )

    plt.close()


def main():

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting Performance Analysis...")

    data = load_comparison_data()

    if data["pipeline"].duplicated().any():
        raise ValueError("Duplicate pipeline names found.")

    print("\nPipeline Comparison Data:")
    print(data.to_string(index=False))

    if data["records_processed"].nunique() != 1:
        print("\nWARNING: Pipelines processed different record counts.")

    if data["total_amount"].nunique() != 1:
        print("\nWARNING: Pipelines produced different total amounts.")

    create_execution_time_chart(data)
    create_records_chart(data)
    create_amount_chart(data)

    print("\nPerformance Analysis Completed!")
    print("\nCharts saved in:", REPORTS_DIR)

    print("\nGenerated charts:")
    print("1. execution_time_comparison.png")
    print("2. records_processed_comparison.png")
    print("3. total_amount_comparison.png")


if __name__ == "__main__":
    main()
