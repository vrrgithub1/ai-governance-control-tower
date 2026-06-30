import os
import duckdb
from src.database import DatabaseManager
from config import Settings
from src.utils.governance_run_process import GovernanceRunProcess

def run_trade_ingestion_pipeline(db_manager: DatabaseManager):
    source_file = "./data/trade_transactions.csv"
    if not os.path.exists(source_file):
        print(f"❌ Ingestion stopped. Source resource target missing: {source_file}")
        return

    # 1. Coordinate Orchestration Context Hooks
    orchestrator = GovernanceRunProcess(db_manager=db_manager)
    run_id = orchestrator.get_current_active_run_id()
    if not run_id:
        run_id = orchestrator.add_new_run_id(p_trigger_source="Python_ETL_Pipeline", p_triggered_by="Batch_Scheduler")
        print(f"🚀 Initialized new execution run instance: {run_id}")
    else:
        print(f"🔗 Attaching workflow execution to running context: {run_id}")

    file_name_only = os.path.basename(source_file)
    process_id = orchestrator.add_new_process_id(
        p_process_name=f"Process {file_name_only}",
        p_run_id=run_id,
        p_dataset_id="D003", 
        p_layer="Bronze->Silver/Quarantine"
    )
    print(f"⚙ Started task execution tracking block: {process_id}")

    with db_manager.connection() as conn:
        try:
            conn.execute("BEGIN TRANSACTION;")
            
            # Reset today's global counter sequence boundary
            # conn.execute("ALTER SEQUENCE bronze.record_number_seq RESTART WITH 1;")
            
            # STEP 1: Clear out the previous run in the bronze landing zone
            conn.execute("TRUNCATE bronze.trade_transactions;")
            
            ingest_query = f"""
                INSERT INTO bronze.trade_transactions (
                    Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, Product_Type, 
                    Trade_Amount, Currency, Trade_Status, Run_Id, Process_Id, 
                    Source_File_Name, Record_Hash
                )
                SELECT 
                    Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, Product_Type, 
                    Trade_Amount, Currency, Trade_Status,
                    '{run_id}' as Run_Id, '{process_id}' as Process_Id, '{file_name_only}' as Source_File_Name,
                    md5(concat_ws('||', Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, Product_Type, Trade_Amount, Currency, Trade_Status)) as Record_Hash
                FROM read_csv_auto('{source_file}');
            """
            conn.execute(ingest_query)
            records_read = conn.execute("SELECT COUNT(*) FROM bronze.trade_transactions;").fetchone()[0]

            # 2. Dynamic Rules Assembly Phase
            rules_query = """
                SELECT Rule_ID, Rule_Name, Column_Name, Rule_Expression, Severity 
                FROM main.quality_rule_definition 
                WHERE Dataset_ID = 'D003' AND Enabled_Flag = TRUE;
            """
            active_rules = conn.execute(rules_query).fetchall()
            
            case_conditions = []
            where_conditions = []
            for rule_id, rule_name, col_name, expr, severity in active_rules:
                case_conditions.append(f"WHEN {expr} THEN '{rule_id}: {rule_name}'")
                where_conditions.append(f"({expr})")
                
            compiled_case_statement = "CASE " + " ".join(case_conditions) + " ELSE 'UNKNOWN_DATA_ANOMALY' END"
            compiled_where_statement = " OR ".join(where_conditions)

            # STEP 2: Isolate Failed Bronze Records to Quarantine
            quarantine_query = f"""
                INSERT INTO quarantine.trade_transactions (
                    Record_Number, Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, 
                    Product_Type, Trade_Amount, Currency, Trade_Status, Run_Id, Process_Id, Quarantine_Reason
                )
                SELECT 
                    Record_Number, Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, 
                    Product_Type, Trade_Amount, Currency, Trade_Status, Run_Id, Process_Id,
                    {compiled_case_statement} as Quarantine_Reason
                FROM bronze.trade_transactions
                WHERE {compiled_where_statement};
            """
            conn.execute(quarantine_query)
            records_failed = conn.execute("SELECT COUNT(*) FROM quarantine.trade_transactions WHERE Process_Id = ?;", [process_id]).fetchone()[0]

            # STEP 3: Promote Valid Clean Bronze Records to Silver Layer via Upsert
            silver_query = f"""
                INSERT INTO silver.trade_transactions (
                    Record_Number, Trade_ID, Trade_Date, Customer_ID, Counterparty_ID, 
                    Product_Type, Trade_Amount, Currency, Trade_Status, Run_Id, Process_Id
                )
                SELECT 
                    Record_Number, Trade_ID, 
                    CAST(Trade_Date AS DATE), 
                    Customer_ID, Counterparty_ID, Product_Type, 
                    CAST(Trade_Amount AS DOUBLE), 
                    Currency, Trade_Status, Run_Id, Process_Id
                FROM bronze.trade_transactions
                WHERE NOT ({compiled_where_statement})
                ON CONFLICT (Trade_ID) DO UPDATE SET
                    Record_Number = EXCLUDED.Record_Number,
                    Trade_Date = EXCLUDED.Trade_Date,
                    Customer_ID = EXCLUDED.Customer_ID,
                    Counterparty_ID = EXCLUDED.Counterparty_ID,
                    Product_Type = EXCLUDED.Product_Type,
                    Trade_Amount = EXCLUDED.Trade_Amount,
                    Currency = EXCLUDED.Currency,
                    Trade_Status = EXCLUDED.Trade_Status,
                    Run_Id = EXCLUDED.Run_Id,
                    Process_Id = EXCLUDED.Process_Id;
            """
            conn.execute(silver_query)
            records_passed = records_read - records_failed

            # STEP 4: Write Metrics Log Summaries into Composite-Indexed main.data_quality_results
            for rule_id, rule_name, col_name, expr, severity in active_rules:
                log_dq_metric_query = f"""
                    INSERT OR REPLACE INTO main.data_quality_results (
                        Run_ID, Dataset_ID, Check_Name, Check_Type, Check_Status, Actual_Value, Severity
                    )
                    SELECT 
                        '{run_id}', 'D003', '{rule_name}', 'METADATA_DRIVEN',
                        CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END,
                        COUNT(*)::VARCHAR, '{severity}'
                    FROM bronze.trade_transactions
                    WHERE {expr};
                """
                conn.execute(log_dq_metric_query)

            conn.commit()
            
            # Finalize Orchestration Task Status
            orchestrator.complete_process_id(
                p_process_id=process_id,
                p_records_read=records_read,
                p_records_passed=records_passed,
                p_records_failed=records_failed,
                p_status="Completed" if records_failed == 0 else "Completed With Quarantines"
            )
            
            print(f"\n🎉 Trade Bronze Ingestion Phase Complete:")
            print(f"   ├─ Extracted Records  : {records_read}")
            print(f"   ├─ Promoted to Silver : {records_passed}")
            print(f"   └─ Quarantined Counts : {records_failed}")

        except Exception as e:
            try:
                conn.execute("ROLLBACK;")
                print("\n❌ Transaction Aborted! Pipeline modifications successfully rolled back.")
            except duckdb.TransactionException:
                pass
            orchestrator.complete_process_id(p_process_id=process_id, p_status="Failed")
            print(f"Details: {e}")

if __name__ == "__main__":
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    run_trade_ingestion_pipeline(db_manager=manager)
