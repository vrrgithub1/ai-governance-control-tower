import duckdb

def setup_model_validation():
    # Connect to the local DuckDB database file
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # SQL query to create or replace the table based on your script
    create_table_query = """
    CREATE OR REPLACE TABLE model_validation (
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
        Created_Date DATE DEFAULT CURRENT_DATE
    );
    """
    
    try:
        # Execute the query to create/replace the table
        conn.execute(create_table_query)
        print("Table 'model_validation' has been successfully created or replaced.")
        
        # Verify the table structure
        print("\nTable Structure:")
        info = conn.execute("PRAGMA table_info('model_validation');").fetchall()
        for column in info:
            print(f"Column: {column[1]} | Type: {column[2]}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_model_validation()
    