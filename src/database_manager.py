import duckdb
from contextlib import contextmanager
from config import Settings

class DatabaseManager:
    def __init__(self, db_path: str = Settings.DATABASE_PATH, read_only: bool = Settings.READ_ONLY):
        self.db_path = db_path
        self.read_only = read_only

    @contextmanager
    def connection(self):
        """
        Context manager that yields a clean database connection 
        and guarantees closure when execution finishes.
        """
        conn = duckdb.connect(database=self.db_path, read_only=self.read_only)
        try:
            yield conn
        finally:
            conn.close()