import duckdb

def setup_ai_risk_register():
    # Connect to the local DuckDB database file
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # 1. SQL query to create or replace the table
    create_table_query = """
    CREATE OR REPLACE TABLE ai_risk_register (
        Risk_ID VARCHAR PRIMARY KEY,
        Risk_Description VARCHAR NOT NULL,
        Category VARCHAR,                 -- Operational, Compliance, Regulatory, etc.
        Severity VARCHAR,                 -- High, Medium, Low
        Status VARCHAR,                   -- Open, Closed
        Owner VARCHAR,                    -- Responsible party
        Created_Date DATE DEFAULT CURRENT_DATE
    );
    """
    
    # 2. SQL query to insert the sample data you provided
    # USING 'INSERT OR REPLACE' ensures it won't crash on primary key conflicts if run multiple times
    insert_data_query = """
    INSERT OR REPLACE INTO ai_risk_register (Risk_ID, Risk_Description, Category, Severity, Status, Owner)
    VALUES 
        ('R001', 'Data Drift', 'Operational', 'High', 'Open', 'John Doe'),
        ('R002', 'Bias Detection Failure', 'Compliance', 'High', 'Open', 'Jane Smith'),
        ('R003', 'Missing Explainability', 'Regulatory', 'Medium', 'Closed', 'John Doe');
    """
    
    try:
        # Create/Replace the table
        conn.execute(create_table_query)
        print("Table 'ai_risk_register' has been successfully created or replaced.")
        
        # Insert the sample rows
        conn.execute(insert_data_query)
        print("Sample risk data successfully populated.")
        
        # Verify the contents
        print("\nCurrent Table Contents:")
        rows = conn.execute("SELECT * FROM ai_risk_register").fetchall()
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_ai_risk_register()
