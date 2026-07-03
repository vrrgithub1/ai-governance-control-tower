import duckdb
# Assumes your database manager module resides in the same directory path tier
from src.database import DatabaseManager 

def setup_complete_governance_schema(db_manager: DatabaseManager, rebuild: bool = False):
    print(f"Initializing unified build sequence for database target via DatabaseManager...\n")
    
    # 1. Consolidated Schema Definitions (Ordered by dependency)
    schemas = {
        "main_schema": """
            CREATE SCHEMA IF NOT EXISTS main;
        """,

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

        "drop_governance_run_process": """
            DROP TABLE IF EXISTS main.governance_run_process;
        """,

        "governance_execution": """
            CREATE TABLE IF NOT EXISTS main.governance_execution (
                Run_Id VARCHAR PRIMARY KEY,
                Start_Time TIMESTAMP NOT NULL,
                End_Time TIMESTAMP, -- Allowed to be null during execution lifecycle
                Status VARCHAR NOT NULL 
                    CHECK (Status IN ('In Progress', 'Completed')),
                Trigger_Source VARCHAR NOT NULL 
                    CHECK (Trigger_Source IN ('SCHEDULER', 'EVENT_DRIVEN', 'MANUAL_CLI', 'WEB_UI', 'CI_CD_PIPELINE', 'API_WEBHOOK')),
                Triggered_By VARCHAR NOT NULL,
                Total_Datasets INTEGER 
                    CHECK (Total_Datasets IS NULL OR Total_Datasets >= 0),
                Total_Models INTEGER 
                    CHECK (Total_Models IS NULL OR Total_Models >= 0),
                Overall_Status VARCHAR NOT NULL,
                Execution_Time_Seconds INTEGER
                    CHECK (Execution_Time_Seconds IS NULL OR Execution_Time_Seconds >= 0)
            );
        """,

        "governance_run_process": """
            CREATE TABLE IF NOT EXISTS main.governance_run_process (
                Process_Id VARCHAR PRIMARY KEY,
                Process_Name VARCHAR NOT NULL,
                Run_Id VARCHAR NOT NULL,
                Dataset_ID VARCHAR,
                Layer VARCHAR,                     -- Bronze/Silver/Gold
                Status VARCHAR,
                Records_read INTEGER,
                Records_passed INTEGER,
                Records_failed INTEGER,
                Start_Time TIMESTAMP,
                End_Time TIMESTAMP,
                FOREIGN KEY (Run_Id) REFERENCES governance_execution (Run_Id)
            );
        """,

        "governance_policy": """
            CREATE TABLE IF NOT EXISTS main.governance_policy (
                Policy_ID VARCHAR PRIMARY KEY,
                Policy_Name VARCHAR NOT NULL,
                Version VARCHAR,                 -- e.g., '1.0', '2.1'
                Owner VARCHAR,                   -- e.g., 'Governance Team'
                Review_Date DATE,                -- Scheduled compliance review date
                Policy_Status VARCHAR,           -- Draft, Approved, Retired
                Approved_By VARCHAR,             -- Name of the approver
                Created_Date DATE DEFAULT CURRENT_DATE
            );
        """,
        
        "data_asset_inventory": """
            CREATE TABLE IF NOT EXISTS main.data_asset_inventory (
                Dataset_ID VARCHAR PRIMARY KEY,
                Dataset_Name VARCHAR NOT NULL,
                Domain VARCHAR,                 -- Customer, Trade, Risk
                Source_System VARCHAR,          -- Salesforce, Bloomberg, etc
                Data_Owner VARCHAR,             -- Business owner
                Data_Steward VARCHAR,           -- Steward
                Classification VARCHAR,         -- Public/Internal/Confidential
                Contains_PII BOOLEAN,           -- True/False (mapped from Yes/No)
                Contains_Financial_Data BOOLEAN,-- True/False (mapped from Yes/No)
                Critical_Data_Element BOOLEAN,  -- True/False (mapped from Yes/No)
                Retention_Period INTEGER,       -- Stored in years
                Quality_SLA DOUBLE,             -- Percentage (e.g., 99.95)
                Refresh_Frequency VARCHAR,      -- Daily/Real-Time
                Lineage_Available BOOLEAN,      -- True/False (mapped from Yes/No)
                Status VARCHAR,                 -- Active/Retired
                Data_Quality_Score DOUBLE,      -- Percentage (e.g., 98.5)
                Created_Date DATE DEFAULT CURRENT_DATE,
                Bronze_Table_Name VARCHAR,             -- e.g., 'bronze.customer_master'
                Silver_Table_Name VARCHAR,             -- e.g., 'silver.customer_master'
                Gold_Table_Name VARCHAR,               -- e.g., 'gold.customer_master'
                Quarantine_Table_Name VARCHAR,          -- e.g., 'quarantine.customer_master'
                Data_Retention_Policy VARCHAR             -- e.g., '7 years', 'Indefinite'
            );
        """,
        
        "risk_register": """
            CREATE TABLE IF NOT EXISTS main.risk_register (
                Risk_ID VARCHAR PRIMARY KEY,
                Risk_Description VARCHAR NOT NULL,
                Category VARCHAR,                 -- Operational, Compliance, Regulatory, etc.
                Severity VARCHAR,                 -- High, Medium, Low
                Status VARCHAR,                   -- Open, Closed
                Owner VARCHAR,                    -- Responsible party
                Created_Date DATE DEFAULT CURRENT_DATE
            );
        """,
        
        "model_inventory": """
            CREATE TABLE IF NOT EXISTS main.model_inventory (
                Model_ID VARCHAR PRIMARY KEY,
                Model_Name VARCHAR NOT NULL,
                Model_Type VARCHAR,              -- Classification, Regression, LLM, NLP
                Model_Criticality VARCHAR,       -- High, Medium, Low, Mission Critical
                Business_Function VARCHAR,       -- Credit Risk, AML, Market Risk
                Business_Owner VARCHAR,          -- Accountable executive
                Model_Owner VARCHAR,             -- Technical owner
                Risk_Tier VARCHAR,               -- High / Medium / Low
                Regulatory_Impact VARCHAR,       -- SR11-7, EU AI Act, etc
                Data_Sensitivity VARCHAR,        -- Public/Internal/Confidential
                Status VARCHAR,                  -- Development/Testing/Production/Retired
                Version VARCHAR,                 -- Model version
                Approval_Status VARCHAR,         -- Pending/Approved/Rejected
                Last_Validation_Date DATE,       -- Validation date
                Next_Review_Date DATE,           -- Scheduled review
                Explainability_Required BOOLEAN, -- True/False (mapped from Y/N)
                Human_Oversight_Required BOOLEAN,-- True/False (mapped from Y/N)
                Created_Date DATE DEFAULT CURRENT_DATE
            );
        """,
        
        "model_validation": """
            CREATE TABLE IF NOT EXISTS main.model_validation (
                Validation_ID VARCHAR PRIMARY KEY,
                Model_ID VARCHAR NOT NULL,
                Validation_Type VARCHAR,
                Validator_Name VARCHAR,
                Validation_Date DATE,
                Validation_Result VARCHAR,
                Findings_Count INTEGER,
                Recommendation VARCHAR,
                Approval_Status VARCHAR,
                Next_Review_Date DATE,
                Created_Date DATE DEFAULT CURRENT_DATE,
                
                -- Global table reference tracking constraint
                FOREIGN KEY (Model_ID) REFERENCES model_inventory (Model_ID)
            );
        """,
        
        "audit_event": """
            CREATE TABLE IF NOT EXISTS main.audit_event (
                Event_ID VARCHAR PRIMARY KEY,
                Event_Timestamp TIMESTAMP,
                Event_Type VARCHAR,
                Entity_Type VARCHAR,
                Entity_ID VARCHAR,
                Performed_By VARCHAR,
                Previous_Value VARCHAR,
                New_Value VARCHAR,
                Event_Description VARCHAR
            );
        """,

        "data_quality_results": """
            CREATE TABLE IF NOT EXISTS main.data_quality_results (
                Run_ID VARCHAR NOT NULL,
                Dataset_ID VARCHAR NOT NULL,
                Check_Name VARCHAR NOT NULL,
                Check_Type VARCHAR,
                Check_Status VARCHAR,
                Expected_Value VARCHAR,
                Actual_Value VARCHAR,
                Quality_Score DOUBLE,
                Severity VARCHAR,
                Run_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Dynamic multi-rule logging constraint
                PRIMARY KEY (Run_ID, Dataset_ID, Check_Name)                
            );
        """,

        "quality_rule_definition": """
            CREATE TABLE IF NOT EXISTS main.quality_rule_definition (
                Rule_ID VARCHAR PRIMARY KEY,
                Rule_Name VARCHAR NOT NULL,
                Dataset_ID VARCHAR NOT NULL,       -- e.g., 'D001' (Customer Master)
                Column_Name VARCHAR NOT NULL,
                Rule_Type VARCHAR NOT NULL,        -- NOT_NULL, UNIQUE, REFERENCE, ENUM
                Rule_Expression VARCHAR NOT NULL,  -- Standard SQL clause that evaluates to TRUE if INVALID
                Severity VARCHAR NOT NULL,         -- High, Medium, Low
                Enabled_Flag BOOLEAN DEFAULT TRUE,
                Rule_Category VARCHAR                  -- Completeness, Validity, Uniqueness, Consistency, Accuracy, Timeliness, Freshness, Referential Integrity, Conformity
            );
        """,

        "governance_metrics": """
            CREATE TABLE IF NOT EXISTS main.governance_metrics (
                Run_ID VARCHAR NOT NULL,
                Metric_Name VARCHAR NOT NULL,
                Metric_Value DOUBLE,
                Metric_Unit VARCHAR,
                Metric_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (Run_ID, Metric_Name)
            );
        """
    }

    drop_objects = [
        "DROP TABLE IF EXISTS main.governance_run_process;",    
        "DROP TABLE IF EXISTS main.governance_execution;",    
        "DROP TABLE IF EXISTS main.governance_policy;",
        "DROP TABLE IF EXISTS main.governance_metrics;",
        "DROP TABLE IF EXISTS main.data_asset_inventory;",
        "DROP TABLE IF EXISTS main.risk_register;",
        "DROP TABLE IF EXISTS main.model_validation;",
        "DROP TABLE IF EXISTS main.model_inventory;",
        "DROP TABLE IF EXISTS main.audit_event;",
        "DROP TABLE IF EXISTS main.data_quality_results;",
        "DROP TABLE IF EXISTS main.quality_rule_definition;"
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
    setup_complete_governance_schema(db_manager=manager, rebuild=True)
