import duckdb

def generate_database_schema():
    database_name = "database/ai_governance_control_tower.db"
    
    try:
        # Connect to the existing DuckDB database
        conn = duckdb.connect(database_name, read_only=True)
        
        # Query to fetch all user-defined tables
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main' AND table_type = 'BASE TABLE';
        """
        tables = [row[0] for row in conn.execute(tables_query).fetchall()]
        
        if not tables:
            print(f"No tables found in the 'main' schema of {database_name}.")
            return

        print(f"==================================================")
        print(f" SCHEMA DEFINITIONS FOR: {database_name}")
        print(f"==================================================\n")

        # Iterate through each table and reconstruct its CREATE TABLE statement
        for table in tables:
            print(f"--- Schema for table: {table} ---")
            
            # Fetch column metadata for the current table
            columns_query = f"PRAGMA table_info('{table}');"
            columns = conn.execute(columns_query).fetchall()
            
            # Construct the SQL string
            schema_sql = f"CREATE TABLE {table} (\n"
            column_definitions = []
            
            for col in columns:
                # col structure: (cid, name, type, notnull, dflt_value, pk)
                col_name = col[1]
                col_type = col[2]
                is_notnull = " NOT NULL" if col[3] == 1 else ""
                default_val = f" DEFAULT {col[4]}" if col[4] is not None else ""
                is_pk = " PRIMARY KEY" if col[5] == 1 else ""
                
                col_def = f"    {col_name} {col_type}{is_pk}{is_notnull}{default_val}"
                column_definitions.append(col_def)
            
            # Join all columns with commas and close the statement
            schema_sql += ",\n".join(column_definitions)
            schema_sql += "\n);\n"
            
            print(schema_sql)
            print("-" * 50 + "\n")
            
    except Exception as e:
        print(f"An error occurred while reading the database: {e}")
    finally:
        try:
            conn.close()
        except NameError:
            pass

if __name__ == "__main__":
    generate_database_schema()