import duckdb

def setup_audit_event():
    # Connect to the local DuckDB database file
    conn = duckdb.connect("ai_governance_control_tower.db")
    
    # SQL query to create or replace the audit log table
    create_table_query = """
    CREATE OR REPLACE TABLE audit_event (
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
    """
    
    try:
        # Execute the query to create/replace the table
        conn.execute(create_table_query)
        print("Table 'audit_event' has been successfully created or replaced.")
        
        # Verify the table structure
        print("\nTable Structure:")
        info = conn.execute("PRAGMA table_info('audit_event');").fetchall()
        for column in info:
            print(f"Column: {column[1]} | Type: {column[2]}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    setup_audit_event()