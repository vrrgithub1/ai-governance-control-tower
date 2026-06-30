import duckdb
from src.database import DatabaseManager
from config import Settings

def setup_country_reference_table(db_manager: DatabaseManager):
    print("Initializing reference lookup table setup: gold.country_ref...")
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS gold.country_ref (
        Country_Code VARCHAR PRIMARY KEY,
        Country_Name VARCHAR NOT NULL,
        Region VARCHAR NOT NULL
    );
    """
    
    seed_data_query = """
    INSERT OR REPLACE INTO gold.country_ref (Country_Code, Country_Name, Region)
    VALUES 
        ('US', 'United States', 'AMER'),
        ('CA', 'Canada', 'AMER'),
        ('GB', 'United Kingdom', 'EMEA'),
        ('DE', 'Germany', 'EMEA'),
        ('FR', 'France', 'EMEA'),
        ('CH', 'Switzerland', 'EMEA'),
        ('JP', 'Japan', 'APAC'),
        ('AU', 'Australia', 'APAC'),
        ('SG', 'Singapore', 'APAC'),
        ('HK', 'Hong Kong', 'APAC'),
        ('BR', 'Brazil', 'LATAM'),
        ('MX', 'Mexico', 'LATAM');
    """

    with db_manager.connection() as conn:
        try:
            # Open transactional safety gate
            conn.execute("BEGIN TRANSACTION;")
            
            # Ensure the gold schema context namespace is available
            conn.execute("CREATE SCHEMA IF NOT EXISTS gold;")
            
            # Build and populate
            conn.execute(create_table_query)
            conn.execute(seed_data_query)
            
            conn.commit()
            print("🎉 Success! gold.country_ref built and populated seamlessly.")
            
            # Visual inspection summary print block
            total_count = conn.execute("SELECT COUNT(*) FROM gold.country_ref;").fetchone()[0]
            print(f"Total reference rows available: {total_count}")
            
        except Exception as e:
            try:
                conn.execute("ROLLBACK;")
                print("\n❌ Build failed! Transaction rolled back cleanly.")
            except duckdb.TransactionException:
                pass
            print(f"Details: {e}")

if __name__ == "__main__":
    # Standard configuration initialization wireframes
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    setup_country_reference_table(db_manager=manager)
