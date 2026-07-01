from config import Settings
from src.database import DatabaseManager
from src.utils.governance_run_process import GovernanceRunProcess
from src.ingest_customer_pipeline import run_customer_ingestion_pipeline
from src.ingest_trade_pipeline import run_trade_ingestion_pipeline

def execute_daily_batch():
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    orchestrator = GovernanceRunProcess(db_manager=manager)
    
    # 1. Initialize the global run window token context
    run_id = orchestrator.add_new_run_id(p_trigger_source="SCHEDULER", p_triggered_by="airflow:daily_batch_dag")
    print(f"🚀 Initialized global batch execution window: {run_id} (Data status: RUNNING)")
    
    try:
        # 2. Sequentially run your data feeds inside the protected tracking envelope
        run_customer_ingestion_pipeline(db_manager=manager)
        run_trade_ingestion_pipeline(db_manager=manager)
        
        # 3. If everything completes with clean transactions, close the run with automation rules
        orchestrator.complete_run_id(p_run_id=run_id, p_total_datasets=2, p_total_models=0)
        print(f"🏁 Run {run_id} finalized successfully.")
        
    except Exception as batch_exception:
        # 4. EMERGENCY CATCH: Capture any crash, print details, and log the system failure state
        error_msg = f"FAILED - Exception: {str(batch_exception)[:100]}"
        print(f"\n❌ Critical Pipeline Failure Detected! Marking run {run_id} as FAILED.")
        
        orchestrator.fail_run_id(p_run_id=run_id, p_overall_status_note=error_msg)
        
        # Re-raise or handle based on your Airflow notification rules
        raise batch_exception

if __name__ == "__main__":
    execute_daily_batch()
