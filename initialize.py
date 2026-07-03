import os
import sys
from config import Settings  # Pointing to your global configuration
from src.database_manager import DatabaseManager
from src.schema_initializer import SchemaInitializer

def run_fresh_setup():
    print("🚀 Bootstrapping clean environmental runtime...")

    # Ensure the parent data directory layout exists on your machine before booting DuckDB
    db_directory = os.path.dirname(Settings.DATABASE_PATH)
    if db_directory and not os.path.exists(db_directory):
        os.makedirs(db_directory, exist_ok=True)
        print(f"📁 Created local binary storage destination path: {db_directory}")

    # Fire thread-safe database connection context manager
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    
    # Run the compiled blueprint
    initializer = SchemaInitializer(db_manager=manager)
    initializer.execute_ddl()
    
    print("\n✅ Verification complete. Your fresh DuckDB binary is baked and completely ready.")

if __name__ == "__main__":
    run_fresh_setup()
