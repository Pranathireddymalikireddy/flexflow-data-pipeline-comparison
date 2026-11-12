
from pathlib import Path

# Main project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data folders
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REJECTS_DIR = BASE_DIR / "data" / "rejects"

# Database folder
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "pipeline.db"

# Reports folder
REPORTS_DIR = BASE_DIR / "reports"

# Data generation settings
RANDOM_SEED = 42
DEFAULT_RECORDS = 1000

# Create folders if they do not exist
for directory in [
    RAW_DIR,
    PROCESSED_DIR,
    REJECTS_DIR,
    DATABASE_DIR,
    REPORTS_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)
