import os
import sys
import logging
from src.database_manager import DatabaseManager
from src.tracker_engine import GovernanceRunProcess
from pipelines.customer_master_pipeline import CustomerMasterPipeline
from pipelines.trade_transactions_pipeline import TradeTransactionsPipeline
from pipelines.credit_features_pipeline import CreditFeaturesPipeline
from pipelines.model_validation_pipeline import ModelValidationPipeline
from config import Settings
from src.risk_engine import AutomatedRiskEngine

logger = logging.getLogger("AIGCT_Orchestrator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def execute_daily_batch():
    db = DatabaseManager(db_path=Settings.DATABASE_PATH)
    tracker = GovernanceRunProcess(db_manager=db)
    
    # 1. Open the master orchestration tracking token immediately
    current_run = tracker.add_new_run_id(p_trigger_source="MANUAL_CLI", p_triggered_by="Venkatasamy Rajadurai")
    logger.info(f"🆔 Comprehensive Data & Model Run Started. Token: {current_run}")
    
    cust_csv = "data/source_landing/customers_daily.csv"
    trade_csv = "data/source_landing/trades_daily.csv"
    credit_csv = "data/source_landing/credit_daily.csv"
    
    try:
        # ===================================================================
        # HARDENED INITIALIZATION GUARDRAILS
        # ===================================================================
        if not os.path.exists(os.path.dirname(cust_csv)):
            raise FileNotFoundError(f"Landing baseline environment directory root missing: {os.path.dirname(cust_csv)}")

        # 2. RUN DATA ENGINEERING LAYER PIPELINES
        cust_pipeline = CustomerMasterPipeline(db_manager=db, tracker=tracker)
        cust_success = cust_pipeline.run_pipeline(p_run_id=current_run, source_csv_path=cust_csv)
        
        # 3. RUN PIPELINE 2: TRADE TRANSACTIONS
        trade_pipeline = TradeTransactionsPipeline(db_manager=db, tracker=tracker)
        trade_success = trade_pipeline.run_pipeline(p_run_id=current_run, source_csv_path=trade_csv)
        
        # 4. RUN PIPELINE 3: CREDIT SCORING FEATURES
        credit_pipeline = CreditFeaturesPipeline(db_manager=db, tracker=tracker)
        credit_success = credit_pipeline.run_pipeline(p_run_id=current_run, source_csv_path=credit_csv)
        
        # 5. RUN MACHINE LEARNING MODEL VALIDATION LAYER
        if cust_success and trade_success and credit_success:
            model_pipeline = ModelValidationPipeline(db_manager=db, tracker=tracker)
            model_success = model_pipeline.run_model_validations(p_run_id=current_run)
            
            # 6. MASTER UNIFIED CLOSE OUT
            if model_success:
                automated_risk_engine = AutomatedRiskEngine(db_manager=db)
                automated_risk_engine.evaluate_run_risk(p_run_id=current_run)
                tracker.complete_run_id(p_run_id=current_run, p_total_assets=3, p_total_models=2)
                logger.info(f"✅ Full Data & Model Control Loop {current_run} marked as COMPLETED.")
            
    except Exception as initialization_or_runtime_error:
        # ===================================================================
        # AUTOMATED SYSTEM FAILURE RESCUE BOUNDARY
        # ===================================================================
        logger.error(f"💥 Critical platform failure captured: {str(initialization_or_runtime_error)}")
        
        # Force-update master run state to Failed in the database
        tracker.fail_run_id(p_run_id=current_run)
        
        # Write an emergency audit trail event using our standard Option A fallback token
        try:
            tracker.log_audit_event(
                p_run_id=current_run,
                p_process_id="SYSTEM",  
                p_event_type="CRITICAL_CRASH",
                p_entity_type="Dataset",
                p_entity_id="TRIPLE_RUN_NODE",
                p_user="ORCHESTRATOR",
                p_desc=f"Aborted run setup sequence. Trace: {str(initialization_or_runtime_error)[:150]}"
            )
        except Exception as logging_error:
            logger.error(f"Failed to log system audit event: {str(logging_error)}")
            
        logger.info(f"❌ Batch run {current_run} successfully updated to FAILED status.")

if __name__ == "__main__":
    execute_daily_batch()
