import duckdb

def setup_data_asset_inventory():
    # Connect to the local DuckDB database file
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # SQL query to create or replace the table
    create_table_query = """
    CREATE OR REPLACE TABLE data_asset_inventory (
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
        Data_Quality_Score DOUBLE,          -- Percentage (e.g., 98.5)
        Created_Date DATE DEFAULT CURRENT_DATE
    );
    """
    
    try:
        # Execute the query
        conn.execute(create_table_query)
        print("Table 'data_asset_inventory' has been successfully created or replaced.")
        
        # Verify the table structure
        print("\nTable Structure:")
        info = conn.execute("PRAGMA table_info('data_asset_inventory');").fetchall()
        for column in info:
            print(f"Column: {column[1]} | Type: {column[2]}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_data_asset_inventory()
    