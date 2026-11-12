# FlexFlow – Data Loading Strategy Comparison

## Project Overview

FlexFlow is a Python-based data engineering project that compares three data publishing strategies:

1. **Full Refresh** – Replaces the complete target dataset during each run.
2. **Incremental Merge** – Inserts new records and updates existing records when newer versions are available.
3. **Partition Replacement** – Replaces only the affected date-based partitions.

The project evaluates these strategies using synthetic customer and order datasets of different sizes. It compares execution time, data movement, correctness, scalability, and failure recovery.

## Objectives

- Implement all three data publishing strategies.
- Compare performance across different dataset sizes.
- Simulate a realistic incremental workload.
- Validate that all strategies produce equivalent final results.
- Test transaction rollback and retry behaviour.
- Document performance and operational trade-offs.

## Technology Stack

- Python
- Pandas
- NumPy
- SQLite
- Matplotlib
- Unit testing with Python `unittest`

## Project Structure

```text
data_pipeline_comparison/
├── app.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── rejects/
├── database/
├── docs/
│   └── strategy_comparison.md
├── reports/
│   ├── strategy_scalability.csv
│   └── incremental_workload_comparison.csv
├── src/
│   ├── cleaning.py
│   ├── comparison_runner.py
│   ├── config.py
│   ├── data_generator.py
│   ├── incremental_workload_benchmark.py
│   ├── ingestion.py
│   ├── publish_strategies.py
│   ├── scalability_benchmark.py
│   └── schema.py
├── tests/
│   ├── test_cleaning.py
│   └── test_publish_strategies.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Dataset and Benchmarking

The project evaluates four dataset sizes:

- 1,000 orders
- 10,000 orders
- 50,000 orders
- 100,000 orders

Two benchmark scenarios are implemented:

### 1. Initial-load scalability benchmark

Compares the three strategies when publishing datasets into empty target databases.

### 2. Realistic incremental workload benchmark

Simulates an existing dataset with updated records, newly inserted records, and changes across selected date partitions.

The strategies receive the appropriate input:
- Full Refresh receives the complete final dataset.
- Incremental Merge receives updated and new records.
- Partition Replacement receives complete snapshots of affected partitions.

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate to the project directory:

```bash
cd data_pipeline_comparison
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows activation:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Benchmarks

Run the initial-load scalability benchmark:

```bash
python -m src.scalability_benchmark
```

Run the realistic incremental workload benchmark:

```bash
python -m src.incremental_workload_benchmark
```

The benchmark results are saved in the `reports/` directory.

## Run Automated Tests

Execute the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The tests cover data cleaning, inserts, updates, duplicate handling, partition replacement, transaction rollback, and retry behaviour.

## Reports and Documentation

- `reports/strategy_scalability.csv` – Initial-load benchmark results.
- `reports/incremental_workload_comparison.csv` – Realistic incremental workload results.
- `docs/strategy_comparison.md` – Detailed methodology, results, complexity analysis, failure recovery, limitations, and recommendations.

## Key Findings

In the realistic incremental workload benchmark, Incremental Merge achieved the lowest execution time at all four dataset sizes in the recorded runs.

At 100,000 orders:

- Full Refresh: approximately 2.149 seconds.
- Incremental Merge: approximately 1.037 seconds.
- Partition Replacement: approximately 1.261 seconds.

These are measurements from a single local benchmark run. Actual performance can vary with hardware, database configuration, and workload.

## Limitations

- The dataset is synthetically generated.
- SQLite is used as the target database.
- Streaming and real-time distributed processing are outside the scope of this comparison.
- Benchmark timings depend on the local execution environment.
- The results represent the tested workloads and should not be treated as universal performance guarantees.

## Future Improvements

- Evaluate the strategies using PostgreSQL or cloud data warehouses.
- Add larger datasets and repeated benchmark runs.
- Explore Apache Spark for distributed processing.
- Introduce orchestration and scheduled pipeline execution.
- Extend monitoring and failure-recovery reporting.

## Author

M.Pranathi Reddy.
