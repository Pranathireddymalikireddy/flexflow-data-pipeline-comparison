
import streamlit as st
import pandas as pd
from pathlib import Path

# Dashboard configuration
st.set_page_config(
    page_title="FlexFlow Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"

st.title("📊 FlexFlow - Advanced Performance Dashboard")

st.write(
    "Analyze Batch Processing, Persistent Incremental Processing "
    "and Streaming Simulation across different dataset sizes."
)

st.divider()


# Load benchmark reports
@st.cache_data
def load_benchmarks():

    datasets = {
        1000: "comparison_1000.csv",
        10000: "comparison_10000.csv",
        50000: "comparison_50000.csv"
    }

    frames = []

    for size, filename in datasets.items():

        file_path = REPORTS_DIR / filename

        if file_path.exists():

            data = pd.read_csv(file_path)

            data["dataset_size"] = size

            frames.append(data)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


data = load_benchmarks()


if data.empty:

    st.warning("No benchmark reports found.")

    st.info(
        "Generate the benchmark reports using Step 11 "
        "before opening this dashboard."
    )

    st.stop()


# Validate required columns
required_columns = [
    "pipeline",
    "records_processed",
    "execution_time_seconds",
    "total_amount"
]

missing = [
    col for col in required_columns
    if col not in data.columns
]

if missing:

    st.error(f"Missing columns: {missing}")
    st.stop()


# Clean data
data["execution_time_seconds"] = pd.to_numeric(
    data["execution_time_seconds"],
    errors="coerce"
)

data["records_processed"] = pd.to_numeric(
    data["records_processed"],
    errors="coerce"
)

data["total_amount"] = pd.to_numeric(
    data["total_amount"],
    errors="coerce"
)

data = data.dropna(subset=required_columns)

if data.empty:
    st.error("Benchmark reports contain no valid records.")
    st.stop()


data["records_per_second"] = (
    data["records_processed"]
    / data["execution_time_seconds"].replace(0, float("nan"))
)


# Sidebar
st.sidebar.header("Dashboard Filters")

selected_sizes = st.sidebar.multiselect(
    "Select Dataset Sizes",
    options=sorted(data["dataset_size"].unique()),
    default=sorted(data["dataset_size"].unique())
)

selected_pipelines = st.sidebar.multiselect(
    "Select Pipelines",
    options=sorted(data["pipeline"].unique()),
    default=sorted(data["pipeline"].unique())
)


filtered = data[
    data["dataset_size"].isin(selected_sizes)
    & data["pipeline"].isin(selected_pipelines)
]


if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# KPI metrics
st.subheader("Performance Overview")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Dataset Sizes",
    filtered["dataset_size"].nunique()
)

col2.metric(
    "Pipeline Results",
    len(filtered)
)

col3.metric(
    "Pipelines Compared",
    filtered["pipeline"].nunique()
)

st.divider()


# Execution time chart
st.subheader("1. Execution Time Comparison")

execution_chart = filtered.pivot_table(
    index="dataset_size",
    columns="pipeline",
    values="execution_time_seconds",
    aggfunc="mean"
)

st.line_chart(execution_chart)

st.caption("Lower execution time indicates faster processing.")


# Records per second
st.subheader("2. Processing Throughput")

throughput_chart = filtered.pivot_table(
    index="dataset_size",
    columns="pipeline",
    values="records_per_second",
    aggfunc="mean"
)

st.line_chart(throughput_chart)

st.caption(
    "Throughput measures the number of records processed per second."
)


# Records processed
st.subheader("3. Records Processed")

records_chart = filtered.pivot_table(
    index="dataset_size",
    columns="pipeline",
    values="records_processed",
    aggfunc="mean"
)

st.bar_chart(records_chart)


# Total amount
st.subheader("4. Total Order Amount")

amount_chart = filtered.pivot_table(
    index="dataset_size",
    columns="pipeline",
    values="total_amount",
    aggfunc="mean"
)

st.line_chart(amount_chart)


# Detailed results
st.subheader("5. Detailed Benchmark Results")

display_columns = [
    "dataset_size",
    "pipeline",
    "records_processed",
    "execution_time_seconds",
    "records_per_second",
    "total_amount"
]

st.dataframe(
    filtered[display_columns].sort_values(
        ["dataset_size", "pipeline"]
    ),
    use_container_width=True
)


# Automatic observations
st.subheader("6. Performance Observations")

for size in sorted(filtered["dataset_size"].unique()):

    subset = filtered[
        filtered["dataset_size"] == size
    ]

    if subset.empty:
        continue

    fastest = subset.loc[
        subset["execution_time_seconds"].idxmin()
    ]

    st.write(
        f"For {size:,} records, "
        f"{fastest['pipeline']} had the lowest measured "
        f"execution time of "
        f"{fastest['execution_time_seconds']:.4f} seconds."
    )


# Download filtered results
st.subheader("7. Download Benchmark Results")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Benchmark CSV",
    data=csv_data,
    file_name="flexflow_benchmark_results.csv",
    mime="text/csv"
)


st.divider()

st.success(
    "FlexFlow Advanced Performance Dashboard loaded successfully!"
)
