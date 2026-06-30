import os
import duckdb
from src.database import DatabaseManager
from config import Settings
from src.utils.governance_run_process import GovernanceRunProcess

def run_customer_ingestion_pipeline(db_manager: DatabaseManager):
    source_file = "./data/customer_master.csv"
    if not os.path.exists(source_file):
        print(f"❌ Aborting pipeline run. Input target resource not found: {source_file}")
        return

    # 1. Instantiate the metadata orchestration management framework
    orchestrator = GovernanceRunProcess(db_manager=db_manager)
    
    # Check for or create an active master run context loop
    run_id = orchestrator.get_current_active_run_id()
    if not run_id:
        run_id = orchestrator.add_new_run_id(p_trigger_source="Python_ETL_Pipeline", p_triggered_by="Batch_Scheduler")
        run_id = orchestrator.get_current_active_run_id()  # Refresh to get the new run_id
        print(f"🚀 Started fresh parent governance execution context: {run_id}")
    else:
        print(f"🔗 Re-using active parent execution context lifecycle pointer: {run_id}")

    # 2. Register and spin up a new internal sub-process key tracking token
    file_name_only = os.path.basename(source_file)
    process_id = orchestrator.add_new_process_id(
        p_process_name=f"Ingest and Validate {file_name_only}",
        p_run_id=run_id,
        p_dataset_id="D001", # Customer Master Dataset ID matching your inventory
        p_layer="Bronze->Silver/Quarantine"
    )
    print(f"⚙ Started task execution tracking block: {process_id}")

    with db_manager.connection() as conn:
        try:
            conn.execute("BEGIN TRANSACTION;")
            
            # ------------------------------------------------------------------------------------
            # STEP 1: Transient Cleanse of Stage & Dynamic COPY Ingestion with MD5 Record Hashes
            # ------------------------------------------------------------------------------------
            conn.execute("TRUNCATE bronze.customer_master;")
            
            # Using DuckDB's fast internal copy mechanics while dynamically computing row hashes
            ingest_query = f"""
                INSERT INTO bronze.customer_master (
                    Customer_ID, Customer_Name, Country_Code, KYC_Status, Customer_Type, 
                    Onboarding_Date, Risk_Rating, Is_Active, Run_Id, Process_Id, 
                    Source_File_Name, Record_Hash, Is_Current
                )
                SELECT 
                    Customer_ID, Customer_Name, Country_Code, KYC_Status, Customer_Type, 
                    Onboarding_Date, Risk_Rating, Is_Active,
                    '{run_id}' as Run_Id,
                    '{process_id}' as Process_Id,
                    '{file_name_only}' as Source_File_Name,
                    md5(concat_ws('||', Customer_ID, Customer_Name, Country_Code, KYC_Status, Customer_Type, Onboarding_Date, Risk_Rating, Is_Active)) as Record_Hash,
                    TRUE as Is_Current
                FROM read_csv_auto('{source_file}');
            """
            conn.execute(ingest_query)
            
            records_read = conn.execute("SELECT COUNT(*) FROM bronze.customer_master;").fetchone()[0]
            print(f"📊 Staged {records_read} landing entries from file buffer layer.")

            # ------------------------------------------------------------------------------------
            # NEW: Dynamic Metadata Rule Fetch
            # ------------------------------------------------------------------------------------
            # Extract active rules defined specifically for the Customer Master Dataset ('D001')
            rules_query = """
                SELECT Rule_ID, Rule_Name, Column_Name, Rule_Expression, Severity 
                FROM main.quality_rule_definition 
                WHERE Dataset_ID = 'D001' AND Enabled_Flag = TRUE;
            """
            active_rules = conn.execute(rules_query).fetchall()
            
            # ------------------------------------------------------------------------------------
            # STEP 2: Metadata-Driven Quarantine Routing Engine
            # ------------------------------------------------------------------------------------
            # Dynamically build a single nested SQL CASE WHEN block from database metadata rows
            case_conditions = []
            where_conditions = []
            
            for rule_id, rule_name, col_name, expr, severity in active_rules:
                # Compile descriptive failure tracking logs
                case_conditions.append(f"WHEN {expr} THEN '{rule_id}: {rule_name}'")
                where_conditions.append(f"({expr})")
            
            # Combine individual expressions with SQL logical separators
            compiled_case_statement = "CASE " + " ".join(case_conditions) + " ELSE 'UNKNOWN_ANOMALY' END"
            compiled_where_statement = " OR ".join(where_conditions)

            quarantine_query = f"""
                INSERT INTO quarantine.customer_master (
                    Record_Number, Customer_ID, Customer_Name, Country_Code, KYC_Status, 
                    Customer_Type, Onboarding_Date, Risk_Rating, Is_Active, Run_Id, Process_Id, Quarantine_Reason
                )
                SELECT 
                    Record_Number, Customer_ID, Customer_Name, Country_Code, KYC_Status, 
                    Customer_Type, Onboarding_Date, Risk_Rating, Is_Active, Run_Id, Process_Id,
                    {compiled_case_statement} as Quarantine_Reason
                FROM bronze.customer_master
                WHERE {compiled_where_statement};
            """
            conn.execute(quarantine_query)
            
            # Count isolated validation anomalies
            records_failed = conn.execute(
                "SELECT COUNT(*) FROM quarantine.customer_master WHERE Process_Id = ?;", [process_id]
            ).fetchone()[0]

            # ------------------------------------------------------------------------------------
            # STEP 3: Route Clean Passing Data to the Silver Layer
            # ------------------------------------------------------------------------------------
            # Valid data is simply the inverse logic of the compiled where clause constraints
            silver_query = f"""
                INSERT INTO silver.customer_master (
                    Record_Number, Customer_ID, Customer_Name, Country_Code, KYC_Status, 
                    Customer_Type, Onboarding_Date, Risk_Rating, Is_Active, Run_Id, Process_Id
                )
                SELECT 
                    Record_Number, Customer_ID, Customer_Name, Country_Code, KYC_Status, 
                    Customer_Type, 
                    CAST(Onboarding_Date AS DATE), 
                    Risk_Rating, 
                    CASE WHEN Is_Active = 'Y' THEN TRUE ELSE FALSE END,
                    Run_Id, Process_Id
                FROM bronze.customer_master
                WHERE NOT ({compiled_where_statement})
                ON CONFLICT (Customer_ID) DO UPDATE SET
                    Record_Number = EXCLUDED.Record_Number,
                    Customer_Name = EXCLUDED.Customer_Name,
                    Country_Code = EXCLUDED.Country_Code,
                    KYC_Status = EXCLUDED.KYC_Status,
                    Customer_Type = EXCLUDED.Customer_Type,
                    Onboarding_Date = EXCLUDED.Onboarding_Date,
                    Risk_Rating = EXCLUDED.Risk_Rating,
                    Is_Active = EXCLUDED.Is_Active,
                    Run_Id = EXCLUDED.Run_Id,
                    Process_Id = EXCLUDED.Process_Id;
            """
            conn.execute(silver_query)
            records_passed = records_read - records_failed

            # ------------------------------------------------------------------------------------
            # BONUS: Hydrate your main.data_quality_results Table Natively
            # ------------------------------------------------------------------------------------
            # For comprehensive enterprise dashboards, log exact failures per rule id
            for rule_id, rule_name, col_name, expr, severity in active_rules:
                log_dq_metric_query = f"""
                    INSERT OR REPLACE INTO main.data_quality_results (
                        Run_ID, Dataset_ID, Check_Name, Check_Type, Check_Status, Actual_Value, Severity
                    )
                    SELECT 
                        '{run_id}', 'D001', '{rule_name}', 'METADATA_DRIVEN',
                        CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END,
                        COUNT(*)::VARCHAR, '{severity}'
                    FROM bronze.customer_master
                    WHERE {expr};
                """
                conn.execute(log_dq_metric_query)

            # Commit changes to disk
            conn.commit()
            
            # 4. Finalize individual step process tracking records
            orchestrator.complete_process_id(
                p_process_id=process_id,
                p_records_read=records_read,
                p_records_passed=records_passed,
                p_records_failed=records_failed,
                p_status="Completed" if records_failed == 0 else "Completed With Quarantines"
            )
            
            print("\n🎉 Pipeline Execution Success Summary:")
            print(f"   ├─ Process Tracking Token : {process_id}")
            print(f"   ├─ Raw Records Digested   : {records_read}")
            print(f"   ├─ Silver Layer Promoted  : {records_passed}")
            print(f"   └─ Quarantine Restricted  : {records_failed}")

        except Exception as pipeline_error:
            try:
                conn.execute("ROLLBACK;")
                print("\n❌ Pipeline Error! Database changes rolled back cleanly.")
            except duckdb.TransactionException:
                pass
            
            orchestrator.complete_process_id(p_process_id=process_id, p_status="Failed")
            print(f"Details: {pipeline_error}")

if __name__ == "__main__":
    # Setup connection profile wireframes
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    run_customer_ingestion_pipeline(db_manager=manager)