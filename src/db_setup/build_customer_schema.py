import duckdb
# Assumes your database manager module resides in the same directory path tier
from src.database import DatabaseManager 

def setup_customer_master_schema(db_manager: DatabaseManager, rebuild: bool = False):
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

        "stage.customer_master": """
            CREATE TABLE IF NOT EXISTS bronze.customer_master (
                Record_Number INTEGER DEFAULT nextval('bronze.record_number_seq') PRIMARY KEY,
                Customer_ID VARCHAR,
                Customer_Name VARCHAR,
                Country_Code VARCHAR,
                KYC_Status VARCHAR,
                Customer_Type VARCHAR,
                Onboarding_Date VARCHAR,
                Risk_Rating VARCHAR,
                Is_Active VARCHAR,
                Feed_Date DATE DEFAULT CURRENT_DATE,
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                Ingestion_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Source_File_Name VARCHAR,
                Record_Hash VARCHAR,
                Is_Current BOOLEAN DEFAULT TRUE
            );
        """,

        "silver.customer_master": """
            CREATE TABLE IF NOT EXISTS silver.customer_master (
                Record_Number INTEGER,
                Customer_ID VARCHAR,
                Customer_Name VARCHAR,
                Country_Code VARCHAR,
                KYC_Status VARCHAR,
                Customer_Type VARCHAR,
                Onboarding_Date DATE, -- Upgraded type evaluation
                Risk_Rating VARCHAR,
                Is_Active BOOLEAN,    -- Upgraded type evaluation
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                PRIMARY KEY (Customer_ID)
            );
        """,

        "quarantine.customer_master": """
            CREATE TABLE IF NOT EXISTS quarantine.customer_master (
                Record_Number INTEGER,
                Customer_ID VARCHAR,
                Customer_Name VARCHAR,
                Country_Code VARCHAR,
                KYC_Status VARCHAR,
                Customer_Type VARCHAR,
                Onboarding_Date VARCHAR,
                Risk_Rating VARCHAR,
                Is_Active VARCHAR,
                Run_Id VARCHAR,
                Process_Id VARCHAR,
                Quarantine_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Quarantine_Reason VARCHAR
            );
        """
    }

    drop_objects = [
        "DROP TABLE IF EXISTS bronze.customer_master;",    
        "DROP TABLE IF EXISTS silver.customer_master;",    
        "DROP TABLE IF EXISTS quarantine.customer_master;",
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
    setup_customer_master_schema(db_manager=manager, rebuild=True)
