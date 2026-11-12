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
- Streamlit
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

Two benchmark scenarios are implemented.

### 1. Initial-Load Scalability Benchmark

Compares the three strategies when publishing datasets into empty target databases.

### 2. Realistic Incremental Workload Benchmark

Simulates an existing dataset with updated records, newly inserted records, and changes across selected date partitions.

The strategies receive the appropriate input:

- **Full Refresh:** Receives the complete final dataset.
- **Incremental Merge:** Receives updated and new records.
- **Partition Replacement:** Receives complete snapshots of affected partitions.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Pranathireddymalikireddy/flexflow-data-pipeline-comparison.git
```

### 2. Navigate to the Project Directory

```bash
cd flexflow-data-pipeline-comparison
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows Command Prompt:

```cmd
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Benchmarks

### 1. Initial-Load Scalability Benchmark

```bash
python -m src.scalability_benchmark
```

### 2. Realistic Incremental Workload Benchmark

```bash
python -m src.incremental_workload_benchmark
```

The benchmark results are saved in the `reports/` directory.

## Run the Performance Dashboard

After generating the benchmark reports, launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard provides:

- Initial-load scalability comparison.
- Realistic incremental workload comparison.
- Execution-time and throughput charts.
- Affected partition analysis.
- Correctness validation.
- Detailed benchmark results.
- Downloadable benchmark reports.

## Run Automated Tests

Execute the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The test suite contains **15 automated tests** covering:

- Data cleaning and validation.
- Duplicate customer detection.
- Invalid order handling.
- Full Refresh publishing.
- Incremental inserts and updates.
- Timestamp-based update validation.
- Partition replacement.
- Transaction rollback.
- Retry and idempotency behaviour.

All 15 tests passed in the recorded test run.

## Reports and Documentation

| File | Description |
|---|---|
| `reports/strategy_scalability.csv` | Initial-load benchmark results |
| `reports/incremental_workload_comparison.csv` | Realistic incremental workload results |
| `docs/strategy_comparison.md` | Detailed methodology, benchmark results, complexity analysis, failure recovery, limitations, and recommendations |

## Key Findings

In the realistic incremental workload benchmark, Incremental Merge achieved the lowest execution time at all four dataset sizes in the recorded runs.

At 100,000 orders:

| Strategy | Execution Time |
|---|---:|
| Full Refresh | 2.149 seconds |
| Incremental Merge | 1.037 seconds |
| Partition Replacement | 1.261 seconds |

Key observations:

- Incremental Merge was approximately **51.7% faster** than Full Refresh at 100,000 orders.
- Partition Replacement was approximately **41.3% faster** than Full Refresh.
- Incremental Merge performed best for the tested workload because it processed only changed and newly inserted records.

These measurements represent a single local benchmark run. Actual performance may vary depending on hardware, database configuration, data distribution, and workload.

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

M. Pranathi Reddy