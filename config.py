import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

# Resolve absolute path to the database file
DEFAULT_DB_PATH = PROJECT_ROOT / os.getenv("DUCKDB_DATABASE_PATH", "data/database/ai_governance_control_tower.db")

# Ensure the parent directory (e.g., data/) exists before connecting
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class Settings:
    DATABASE_PATH: str = str(DEFAULT_DB_PATH)
    READ_ONLY: bool = os.getenv("DUCKDB_READ_ONLY", "False").lower() == "true"
