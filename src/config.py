
from pathlib import Path

# Main project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTS_DIR = DATA_DIR / "rejects"

# Database configuration
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "pipeline.db"

# Reports directory
REPORTS_DIR = BASE_DIR / "reports"

# Documentation directory
DOCS_DIR = BASE_DIR / "docs"

# Data generation settings
RANDOM_SEED = 42
DEFAULT_RECORDS = 1000

# Supported benchmark sizes
BENCHMARK_SIZES = [1000, 10000, 50000, 100000]

# Dataset configuration
CUSTOMER_FILE = RAW_DIR / "customers.csv"
ORDER_FILE = RAW_DIR / "orders.csv"

CLEAN_CUSTOMER_FILE = PROCESSED_DIR / "customers_clean.csv"
CLEAN_ORDER_FILE = PROCESSED_DIR / "orders_clean.csv"

REJECTED_CUSTOMER_FILE = REJECTS_DIR / "customers_rejected.csv"
REJECTED_ORDER_FILE = REJECTS_DIR / "orders_rejected.csv"

# Database table names
CUSTOMER_TABLE = "customers"
ORDER_TABLE = "orders"
RUN_HISTORY_TABLE = "pipeline_runs"
REJECT_TABLE = "rejected_records"

# Primary keys
CUSTOMER_PRIMARY_KEY = "customer_id"
ORDER_PRIMARY_KEY = "order_id"

# Business rules
ALLOWED_ORDER_STATUSES = [
    "Pending",
    "Shipped",
    "Delivered",
    "Cancelled"
]

MIN_ORDER_AMOUNT = 0

# Date partition column
PARTITION_COLUMN = "order_date"

# Pipeline names
FULL_REFRESH = "full_refresh"
INCREMENTAL_MERGE = "incremental_merge"
PARTITION_REPLACEMENT = "partition_replacement"

# Create required directories
DIRECTORIES = [
    RAW_DIR,
    PROCESSED_DIR,
    REJECTS_DIR,
    DATABASE_DIR,
    REPORTS_DIR,
    DOCS_DIR
]

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)
