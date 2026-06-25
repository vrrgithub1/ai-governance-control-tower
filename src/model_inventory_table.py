import duckdb

def setup_model_inventory():
    # Connect to a local DuckDB database file (or use ':memory:' for an in-memory db)
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # SQL query to create or replace the table
    create_table_query = """
    CREATE OR REPLACE TABLE model_inventory (
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
    """

    # 2. SQL query to insert the sample data you provided
    insert_data_query = """
    INSERT OR REPLACE INTO model_inventory (Model_ID, Model_Name, Risk_Tier, Model_Criticality )
    VALUES 
        ('M001', 'AML Monitoring', 'High', 'Mission Critical'),
        ('M002', 'Marketing Churn', 'Medium', 'Low');
    """


    try:
        # Execute the query
        conn.execute(create_table_query)
        print("Table 'model_inventory' has been successfully created or replaced.")
        
        # Verify the table structure
        print("\nTable Structure:")
        info = conn.execute("PRAGMA table_info('model_inventory');").fetchall()
        for column in info:
            print(f"Column: {column[1]} | Type: {column[2]}")

        # Insert the sample row
        conn.execute(insert_data_query)
        print("Sample model data successfully populated.")
        
        # Verify the contents
        print("\nCurrent Table Contents:")
        rows = conn.execute("SELECT * FROM model_inventory").fetchall()
        for row in rows:
            print(row)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_model_inventory()
    