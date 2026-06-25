import duckdb

def setup_governance_policies():
    # Connect to the local DuckDB database file
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # 1. SQL query to create or replace the table
    create_table_query = """
    CREATE OR REPLACE TABLE governance_policies (
        Policy_ID VARCHAR PRIMARY KEY,
        Policy_Name VARCHAR NOT NULL,
        Version VARCHAR,                 -- e.g., '1.0', '2.1'
        Owner VARCHAR,                   -- e.g., 'Governance Team'
        Review_Date DATE,                -- Scheduled compliance review date
        Policy_Status VARCHAR,                -- Draft, Approved, Retired
        Approved_By VARCHAR,                -- Name of the approver
        Created_Date DATE DEFAULT CURRENT_DATE
    );
    """
    
    # 2. SQL query to insert the sample data you provided
    insert_data_query = """
    INSERT OR REPLACE INTO governance_policies (Policy_ID, Policy_Name, Version, Owner, Review_Date, Policy_Status, Approved_By)

    VALUES 
        ('P001', 'AI Governance Policy', '1.0', 'Governance Team', '2026-12-31', 'Approved', 'John Doe');
    """
    
    try:
        # Create/Replace the table
        conn.execute(create_table_query)
        print("Table 'governance_policies' has been successfully created or replaced.")
        
        # Insert the sample row
        conn.execute(insert_data_query)
        print("Sample policy data successfully populated.")
        
        # Verify the contents
        print("\nCurrent Table Contents:")
        rows = conn.execute("SELECT * FROM governance_policies").fetchall()
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_governance_policies()
