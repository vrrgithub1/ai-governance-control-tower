import os
import logging
import random
from datetime import datetime, timedelta
from src.database_manager import DatabaseManager
from src.tracker_engine import GovernanceRunProcess

logger = logging.getLogger("AIGCT_Model_Pipeline")

class ModelValidationPipeline:
    def __init__(self, db_manager: DatabaseManager, tracker: GovernanceRunProcess):
        self.db = db_manager
        self.tracker = tracker

    def run_model_validations(self, p_run_id: str) -> bool:
        """Fetches active production models and logs their validation audit metrics."""
        logger.info("🤖 Kicking off automated model validation compliance suites...")
        
        # Define trackable process step for the dashboard
        process_id = self.tracker.add_new_process_id(
            p_process_name="Execute AI Model Risk & Validation Suite",
            p_run_id=p_run_id,
            p_dataset_id="SYSTEM",  # Infrastructure process tier
            p_layer_name="MODEL_VAL",
            p_process_code="model_validation_pipeline.run_model_validations()"
        )
        
        self.tracker.complete_process_id(process_id, p_status="In Progress")

        try:
            # 1. Query the database to find out which models currently need monitoring
            with self.db.connection() as conn:
                models = conn.execute("""
                    SELECT model_id, model_name, version, explainability_required 
                    FROM aigct_core.model_inventory 
                    WHERE status = 'Production';
                """).fetchall()

            if not models:
                logger.warning("⚠️ No active production models found in registry inventory.")
                self.tracker.complete_process_id(process_id, p_read=0, p_passed=0, p_failed=0, p_status="Completed")
                return True

            total_checked = len(models)
            findings_logged = 0

            # 2. Iterate through models and evaluate their metrics
            with self.db.connection() as conn:
                for idx, model_row in enumerate(models):
                    m_id, m_name, m_ver, exp_req = model_row
                    
                    validation_id = f"VAL_2026{random.randint(10000, 99999)}"
                    next_review = (datetime.now() + timedelta(days=180)).date()
                    
                    # Simulate dynamic validation findings
                    # Let's say the Credit Net occasionally flags an explainability warning
                    if m_id == "MDL_CREDIT_NET" and random.random() < 0.4:
                        v_result = "PASSED WITH WARNINGS"
                        v_findings = "1"
                        v_rec = "Monitor SHAP feature convergence variance in next cycle."
                        v_status = "Approved"
                        findings_logged += 1
                    else:
                        v_result = "PASSED"
                        v_findings = "0"
                        v_rec = "Model parameters stable. Continual production deployment recommended."
                        v_status = "Approved"

                    # 3. Insert results into the model_validation table
                    insert_query = """
                        INSERT INTO aigct_core.model_validation (
                            validation_id, model_id, validation_type, validation_name,
                            validator_name, validation_result, findings_count, recommendation,
                            approval_status, next_review_date, run_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """
                    conn.execute(insert_query, [
                        validation_id, m_id, "PERFORMANCE_AND_BIAS", 
                        f"Quarterly Performance Review v{m_ver}", "Model Risk Management Group",
                        v_result, v_findings, v_rec, v_status, next_review, p_run_id
                    ])
                    
                    # Update the master repository model inventory with the last validation date
                    conn.execute("""
                        UPDATE aigct_core.model_inventory
                        SET last_validation_date = CURRENT_DATE,
                            next_review_date = ?
                        WHERE model_id = ?;
                    """, [next_review, m_id])

            # 4. Finalize tracking process metrics
            self.tracker.complete_process_id(
                process_id, 
                p_read=total_checked, 
                p_passed=total_checked - findings_logged, 
                p_failed=findings_logged, 
                p_status="Completed"
            )
            
            self.tracker.log_audit_event(
                p_run_id=p_run_id, p_process_id=process_id, p_event_type="MODEL_AUDIT",
                p_entity_type="Model", p_entity_id="MULTIPLEX_MODEL_RUN", p_user="MODEL_RISK_ENGINE",
                p_desc=f"Completed verification loops for {total_checked} production models. Warnings found: {findings_logged}."
            )
            
            return True

        except Exception as model_err:
            logger.error(f"💥 Model validation suite crashed: {str(model_err)}")
            self.tracker.complete_process_id(process_id, p_status="Failed")
            raise model_err
        