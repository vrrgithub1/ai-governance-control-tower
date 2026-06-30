import duckdb
# Assumes your database manager module resides in the same directory path tier
from src.database import DatabaseManager 

def setup_trade_transaction_schema(db_manager: DatabaseManager, rebuild: bool = False):
    print(f"Initializing unified build sequence for database target via DatabaseManager...\n")
    
    # 1. Consolidated Schema Definitions (Ordered by dependency)
    schemas = {
        "bronze_schema": """
            CREATE SCHEMA IF NOT EXISTS bronze;
        """,

        "silver_schema": """
            CREATE SCHEMA IF NOT EXISTS silver;
        """,

        "quarantine_schema": """
            CREATE SCHEMA IF NOT EXISTS quarantine;
        """,

        "gold_schema": """
            CREATE SCHEMA IF NOT EXISTS gold;
        """,

        "record_number_sequence": """
            CREATE SEQUENCE IF NOT EXISTS bronze.record_number_seq START WITH 1 INCREMENT BY 1;
        """,

        "bronze.trade_transactions": """
            CREATE TABLE IF NOT EXISTS bronze.trade_transactions (
                Record_Number INTEGER DEFAULT nextval('bronze.record_number_seq') PRIMARY KEY,
                Trade_ID VARCHAR,
                Trade_Date VARCHAR,
                Customer_ID VARCHAR,
                Counterparty_ID VARCHAR,
                Product_Type VARCHAR,
                Trade_Amount VARCHAR,
                Currency VARCHAR,
                Trade_Status VARCHAR,
                Feed_Date DATE DEFAULT CURRENT_DATE,
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                Ingestion_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Source_File_Name VARCHAR,
                Record_Hash VARCHAR,
                Is_Current BOOLEAN DEFAULT TRUE
            );
        """,

        "silver.trade_transactions": """
            CREATE TABLE IF NOT EXISTS silver.trade_transactions (
                Record_Number INTEGER,
                Trade_ID VARCHAR,
                Trade_Date DATE,         -- Formatted to strongly typed DATE
                Customer_ID VARCHAR,
                Counterparty_ID VARCHAR,
                Product_Type VARCHAR,
                Trade_Amount DOUBLE,     -- Formatted to strongly typed DOUBLE
                Currency VARCHAR,
                Trade_Status VARCHAR,
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                PRIMARY KEY (Trade_ID)
            );
        """,

        "quarantine.trade_transactions": """
            CREATE TABLE IF NOT EXISTS quarantine.trade_transactions (
                Record_Number INTEGER,
                Trade_ID VARCHAR,
                Trade_Date VARCHAR,
                Customer_ID VARCHAR,
                Counterparty_ID VARCHAR,
                Product_Type VARCHAR,
                Trade_Amount VARCHAR,
                Currency VARCHAR,
                Trade_Status VARCHAR,
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                Quarantine_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Quarantine_Reason VARCHAR
            );
        """
    }

    drop_objects = [
        "DROP TABLE IF EXISTS bronze.trade_transactions;",    
        "DROP TABLE IF EXISTS silver.trade_transactions;",    
        "DROP TABLE IF EXISTS quarantine.trade_transactions;",
    ]


    # Open a single context-managed workspace block
    with db_manager.connection() as conn:
        try:
            # Begin a transactional block to ensure all-or-nothing schema creation
            conn.execute("BEGIN TRANSACTION;")

            if rebuild:
                print("Rebuild flag detected. Dropping existing tables...")
                for drop_sql in drop_objects:
                    conn.execute(drop_sql)
                    print(f"✔ Executed: {drop_sql.strip()}")
                print("All specified tables dropped successfully.\n")

            # Build all fresh tables
            for table_name, schema_sql in schemas.items():
                conn.execute(schema_sql)
                print(f"✔ Table '{table_name}' built successfully.")
                
            print("\nPlacing static initialization assets...")
            
            conn.commit()
            print("\n🎉 Database build complete! All schema corrections applied safely.")
            
        except Exception as e:
            # Only rollback if the transaction was actually started
            try:
                conn.execute("ROLLBACK;")
                print(f"\n❌ Execution breakdown encountered! Schema variations rejected and transaction rolled back.")
            except duckdb.TransactionException:
                print(f"\n❌ Execution breakdown encountered before transaction started.")
            print(f"Details: {e}")

if __name__ == "__main__":
    # Standard baseline invocation initialization 
    from config import Settings
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    
    # Execute structural reset setup
    setup_trade_transaction_schema(db_manager=manager, rebuild=True)
