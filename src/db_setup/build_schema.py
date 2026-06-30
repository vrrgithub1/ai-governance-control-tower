import duckdb

def setup_complete_governance_schema(rebuild: bool = False):
    db_file = "database/ai_governance_control_tower.db"
    conn = duckdb.connect(db_file)
    
    print(f"Initializing unified build sequence for database: {db_file}\n")
    
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
                Start_Time TIMESTAMP,
                End_Time TIMESTAMP,
                Status VARCHAR,
                Trigger_Source VARCHAR,
                Triggered_By VARCHAR,
                Total_Datasets INTEGER,
                Total_Models INTEGER,
                Overall_Status VARCHAR
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
                Created_Date DATE DEFAULT CURRENT_DATE
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
                Run_ID VARCHAR PRIMARY KEY,
                Dataset_ID VARCHAR NOT NULL,
                Check_Name VARCHAR NOT NULL,
                Check_Type VARCHAR,
                Check_Status VARCHAR,
                Expected_Value VARCHAR,
                Actual_Value VARCHAR,
                Quality_Score DOUBLE,
                Severity VARCHAR,
                Run_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    }

    drop_objects = [
        "DROP TABLE IF EXISTS main.governance_run_process;",    
        "DROP TABLE IF EXISTS main.governance_execution;",    
        "DROP TABLE IF EXISTS main.governance_policy;",
        "DROP TABLE IF EXISTS main.data_asset_inventory;",
        "DROP TABLE IF EXISTS main.risk_register;",
        "DROP TABLE IF EXISTS main.model_validation;",
        "DROP TABLE IF EXISTS main.model_inventory;",
        "DROP TABLE IF EXISTS main.audit_event;",
        "DROP TABLE IF EXISTS main.data_quality_results;"
    ]

    # 2. Consolidated Seed Insert Scripts
    seed_data = {
        "risk_register": """
            INSERT OR REPLACE INTO main.risk_register (Risk_ID, Risk_Description, Category, Severity, Status, Owner)
            VALUES 
                ('R001', 'Data Drift', 'Operational', 'High', 'Open', 'John Doe'),
                ('R002', 'Bias Detection Failure', 'Compliance', 'High', 'Open', 'Jane Smith'),
                ('R003', 'Missing Explainability', 'Regulatory', 'Medium', 'Closed', 'John Doe');
        """,
        "governance_policy": """
            INSERT OR REPLACE INTO main.governance_policy (Policy_ID, Policy_Name, Version, Owner, Review_Date, Policy_Status, Approved_By)
            VALUES 
                ('P001', 'AI Governance Policy', '1.0', 'Governance Team', '2026-12-31', 'Approved', 'John Doe');
        """,
        "model_inventory": """
            INSERT OR REPLACE INTO main.model_inventory (Model_ID, Model_Name, Risk_Tier, Model_Criticality)
            VALUES 
                ('M001', 'AML Monitoring', 'High', 'Mission Critical'),
                ('M002', 'Marketing Churn', 'Medium', 'Low');
        """
    }

    try:
        # REMOVED: conn.execute("SET foreign_keys = true;") -> DuckDB enforces them by default!
        
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
        
        # Hydrate target seed registries
        for target_table, insert_sql in seed_data.items():
            conn.execute(insert_sql)
            print(f"✔ Initial data for '{target_table}' seeded successfully.")
            
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
    finally:
        conn.close()

if __name__ == "__main__":
    setup_complete_governance_schema(rebuild=True)  # Set rebuild to True to drop and recreate tables

