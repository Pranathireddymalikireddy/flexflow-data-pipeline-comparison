
# FlexFlow - Data Pipeline Comparison

## Project Overview

FlexFlow is a Python-based data engineering project
that compares three data processing approaches:

1. Batch Processing
2. Persistent Incremental Processing
3. Streaming Simulation

The project evaluates their performance using
different dataset sizes.

## Technologies Used

- Python
- Pandas
- NumPy
- SQLite
- Matplotlib
- Streamlit

## Project Features

- Synthetic customer and order data generation
- Data ingestion and cleaning
- Duplicate and invalid record detection
- Batch processing
- Persistent incremental processing
- CSV-based streaming simulation
- SQLite-based processing history
- Performance benchmarking
- Interactive Streamlit dashboard

## Dataset Sizes

The project evaluates:

- 1,000 records
- 10,000 records
- 50,000 records

## Performance Metrics

- Execution time
- Records processed
- Processing throughput
- Total order amount
- New, updated and unchanged records

## Project Structure

```text
data_pipeline_comparison/
├── app.py
├── data/
├── database/
├── reports/
├── src/
├── tests/
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate to the project:

```bash
cd data_pipeline_comparison
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Project

Generate data:

```bash
python -m src.data_generator --records 1000
```

Clean data:

```bash
python -m src.cleaning
```

Run pipeline comparison:

```bash
python -m src.pipeline_comparison
```

Launch dashboard:

```bash
streamlit run app.py
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Limitations

- Streaming is simulated using CSV micro-batches.
- Incremental processing uses SQLite for persistent state.
- Dataset generation is synthetic.
- Performance measurements depend on hardware and execution conditions.

## Future Improvements

- Apache Kafka integration
- Apache Spark integration
- Real-time streaming
- Larger datasets
- Cloud-based deployment

## Author

Add your name here.
