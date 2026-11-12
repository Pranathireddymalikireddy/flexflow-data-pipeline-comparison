
import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Dashboard Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="FlexFlow - Data Pipeline Comparison",
    page_icon="📊",
    layout="wide"
)

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"

st.title("📊 FlexFlow - Data Pipeline Comparison")

st.write(
    "Compare Full Refresh, Incremental Merge, and "
    "Partition Replacement using scalability and "
    "realistic incremental workload benchmarks."
)

st.divider()


# --------------------------------------------------
# Load Benchmark Reports
# --------------------------------------------------

@st.cache_data
def load_reports():

    scalability_path = REPORTS_DIR / "strategy_scalability.csv"
    incremental_path = REPORTS_DIR / "incremental_workload_comparison.csv"

    scalability = pd.read_csv(scalability_path)
    incremental = pd.read_csv(incremental_path)

    return scalability, incremental


try:
    scalability, incremental = load_reports()

except FileNotFoundError as error:
    st.error(f"Benchmark report not found: {error}")
    st.info(
        "Run both benchmark scripts first:\n"
        "- python -m src.scalability_benchmark\n"
        "- python -m src.incremental_workload_benchmark"
    )
    st.stop()


# --------------------------------------------------
# Validate Report Columns
# --------------------------------------------------

scalability_columns = [
    "dataset_size",
    "strategy",
    "runtime_seconds",
    "orders_loaded",
    "total_amount",
    "equivalent_to_full_refresh",
    "status"
]

incremental_columns = [
    "dataset_size",
    "strategy",
    "initial_orders",
    "delta_orders",
    "affected_partitions",
    "runtime_seconds",
    "final_orders",
    "total_amount",
    "equivalent_to_full_refresh",
    "status"
]

missing_scalability = [
    col for col in scalability_columns
    if col not in scalability.columns
]

missing_incremental = [
    col for col in incremental_columns
    if col not in incremental.columns
]

if missing_scalability or missing_incremental:
    st.error("Required columns are missing from benchmark reports.")
    st.write("Scalability report missing:", missing_scalability)
    st.write("Incremental report missing:", missing_incremental)
    st.stop()


# --------------------------------------------------
# Clean and Prepare Data
# --------------------------------------------------

def clean_benchmark_data(dataframe):

    dataframe["dataset_size"] = pd.to_numeric(
        dataframe["dataset_size"], errors="coerce"
    )

    dataframe["runtime_seconds"] = pd.to_numeric(
        dataframe["runtime_seconds"], errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=["dataset_size", "runtime_seconds"]
    ).copy()

    dataframe["dataset_size"] = dataframe["dataset_size"].astype(int)

    return dataframe


scalability = clean_benchmark_data(scalability)
incremental = clean_benchmark_data(incremental)

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

available_sizes = sorted(
    scalability["dataset_size"].dropna().unique()
)

selected_sizes = st.sidebar.multiselect(
    "Select Dataset Sizes",
    options=available_sizes,
    default=available_sizes
)

available_strategies = sorted(
    scalability["strategy"].dropna().unique()
)

selected_strategies = st.sidebar.multiselect(
    "Select Strategies",
    options=available_strategies,
    default=available_strategies
)

if not selected_sizes or not selected_strategies:
    st.warning("Select at least one dataset size and one strategy.")
    st.stop()


scalability_filtered = scalability[
    scalability["dataset_size"].isin(selected_sizes)
    & scalability["strategy"].isin(selected_strategies)
]

incremental_filtered = incremental[
    incremental["dataset_size"].isin(selected_sizes)
    & incremental["strategy"].isin(selected_strategies)
]


# --------------------------------------------------
# Overall Project Summary
# --------------------------------------------------

st.subheader("Project Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Strategies Compared",
    len(selected_strategies)
)

col2.metric(
    "Dataset Sizes",
    len(selected_sizes)
)

col3.metric(
    "Scalability Results",
    len(scalability_filtered)
)

col4.metric(
    "Incremental Results",
    len(incremental_filtered)
)

st.divider()


# --------------------------------------------------
# Benchmark Tabs
# --------------------------------------------------

tab1, tab2, tab3 = st.tabs([
    "Initial-Load Scalability",
    "Incremental Workload",
    "Detailed Results"
])


# ==================================================
# TAB 1: INITIAL-LOAD SCALABILITY
# ==================================================

with tab1:

    st.header("1. Initial-Load Scalability Benchmark")

    st.write(
        "This benchmark compares the time required by each "
        "strategy to load the complete dataset."
    )

    if scalability_filtered.empty:
        st.warning("No scalability results match the filters.")

    else:

        # Runtime Chart
        st.subheader("Execution Time Comparison")

        runtime_chart = scalability_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="runtime_seconds",
            aggfunc="mean"
        )

        st.line_chart(runtime_chart)

        st.caption(
            "Lower execution time indicates faster processing."
        )

        # Throughput Chart
        st.subheader("Processing Throughput")

        scalability_filtered = scalability_filtered.copy()

        scalability_filtered["records_per_second"] = (
            scalability_filtered["orders_loaded"]
            / scalability_filtered["runtime_seconds"].replace(0, float("nan"))
        )

        throughput_chart = scalability_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="records_per_second",
            aggfunc="mean"
        )

        st.line_chart(throughput_chart)

        st.caption(
            "Throughput represents orders loaded per second."
        )

        # Total Amount Chart
        st.subheader("Total Order Amount Validation")

        amount_chart = scalability_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="total_amount",
            aggfunc="mean"
        )

        st.line_chart(amount_chart)

        st.caption(
            "Matching totals help demonstrate equivalent output."
        )

        # Fastest Strategy
        st.subheader("Fastest Strategy by Dataset Size")

        for size in sorted(scalability_filtered["dataset_size"].unique()):

            subset = scalability_filtered[
                scalability_filtered["dataset_size"] == size
            ]

            if not subset.empty:

                fastest = subset.loc[
                    subset["runtime_seconds"].idxmin()
                ]

                st.write(
                    f"**{size:,} orders:** "
                    f"{fastest['strategy']} was fastest "
                    f"at {fastest['runtime_seconds']:.4f} seconds."
                )


# ==================================================
# TAB 2: REALISTIC INCREMENTAL WORKLOAD
# ==================================================

with tab2:

    st.header("2. Realistic Incremental Workload Benchmark")

    st.write(
        "This benchmark simulates an existing dataset receiving "
        "updates and new orders. Each strategy processes the "
        "appropriate input for its publishing method."
    )

    if incremental_filtered.empty:
        st.warning("No incremental results match the filters.")

    else:

        # Runtime Chart
        st.subheader("Execution Time Comparison")

        incremental_runtime_chart = incremental_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="runtime_seconds",
            aggfunc="mean"
        )

        st.line_chart(incremental_runtime_chart)

        st.caption(
            "Lower execution time indicates faster workload processing."
        )

        # Records Processed
        st.subheader("Records Submitted to Each Strategy")

        records_chart = incremental_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="delta_orders",
            aggfunc="mean"
        )

        st.bar_chart(records_chart)

        st.caption(
            "Full Refresh receives the complete final dataset, "
            "Incremental Merge receives changed and new orders, "
            "and Partition Replacement receives complete snapshots "
            "of affected partitions."
        )

        # Affected Partitions
        st.subheader("Affected Partitions")

        partition_chart = incremental_filtered.pivot_table(
            index="dataset_size",
            columns="strategy",
            values="affected_partitions",
            aggfunc="mean"
        )

        st.bar_chart(partition_chart)

        # Fastest Strategy
        st.subheader("Fastest Strategy by Dataset Size")

        for size in sorted(incremental_filtered["dataset_size"].unique()):

            subset = incremental_filtered[
                incremental_filtered["dataset_size"] == size
            ]

            if not subset.empty:

                fastest = subset.loc[
                    subset["runtime_seconds"].idxmin()
                ]

                st.write(
                    f"**{size:,} orders:** "
                    f"{fastest['strategy']} was fastest "
                    f"at {fastest['runtime_seconds']:.4f} seconds."
                )


# ==================================================
# TAB 3: DETAILED RESULTS AND VALIDATION
# ==================================================

with tab3:

    st.header("3. Detailed Benchmark Results")

    st.subheader("Initial-Load Results")

    st.dataframe(
        scalability_filtered.sort_values(
            ["dataset_size", "strategy"]
        ),
        width="stretch",
        hide_index=True
    )

    st.subheader("Incremental Workload Results")

    st.dataframe(
        incremental_filtered.sort_values(
            ["dataset_size", "strategy"]
        ),
        width="stretch",
        hide_index=True
    )

    st.divider()

    # Correctness Validation
    st.subheader("Correctness and Equivalence Validation")

    scalability_success = (
        scalability_filtered["status"].eq("SUCCESS")
        & scalability_filtered["equivalent_to_full_refresh"].eq(True)
    )

    incremental_success = (
        incremental_filtered["status"].eq("SUCCESS")
        & incremental_filtered["equivalent_to_full_refresh"].eq(True)
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Initial-Load Valid Results",
        f"{scalability_success.sum()} / {len(scalability_filtered)}"
    )

    col2.metric(
        "Incremental Valid Results",
        f"{incremental_success.sum()} / {len(incremental_filtered)}"
    )

    if scalability_success.all() and incremental_success.all():
        st.success(
            "All displayed benchmark results completed successfully "
            "and were equivalent to Full Refresh."
        )
    else:
        st.warning(
            "Some displayed benchmark results failed or were not "
            "equivalent to Full Refresh. Review the detailed tables."
        )


# --------------------------------------------------
# Download Reports
# --------------------------------------------------

st.divider()

st.header("4. Download Benchmark Reports")

col1, col2 = st.columns(2)

with col1:

    st.download_button(
        label="Download Scalability Results",
        data=scalability_filtered.to_csv(index=False).encode("utf-8"),
        file_name="strategy_scalability_results.csv",
        mime="text/csv"
    )

with col2:

    st.download_button(
        label="Download Incremental Workload Results",
        data=incremental_filtered.to_csv(index=False).encode("utf-8"),
        file_name="incremental_workload_results.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.success(
    "FlexFlow Data Pipeline Comparison Dashboard loaded successfully!"
)

st.caption(
    "Project: Full Refresh vs Incremental Merge vs Partition Replacement"
)
