import logging
from src.database_manager import DatabaseManager

logger = logging.getLogger("AIGCT_Risk_Engine")

class AutomatedRiskEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def evaluate_run_risk(self, p_run_id: str):
        """Analyzes recent pipeline runs and registers issues using your exact table DDL constraints."""
        logger.info(f"🚨 Running automated risk assessment for run: {p_run_id}")
        
        with self.db.connection() as conn:
            # 1. Evaluate Data Quality Degradation (Score < 98)
            failed_rules = conn.execute("""
                SELECT dataset_id, check_name, quality_score, failed_records, severity
                FROM aigct_core.data_quality_results
                WHERE run_id = ? AND check_status = 'FAIL';
            """, [p_run_id]).fetchall()
            
            for dataset_id, check_name, score, failed_count, r_severity in failed_rules:
                if score < 98.0:
                    risk_id = f"RSK_{p_run_id[-6:]}_{dataset_id[-4:]}"
                    description = f"Degraded Quality: {check_name} on {dataset_id}. Isolated count: {failed_count} records."
                    
                    conn.execute("""
                        INSERT INTO aigct_core.risk_register (
                            risk_id, risk_description, category, severity, status, owner, risk_owner_group
                        ) VALUES (?, ?, 'DATA_QUALITY', ?, 'Open', 'AUTOMATED_AGENT', 'DATA_ENGINEERING')
                        ON CONFLICT (risk_id) DO UPDATE SET risk_description = EXCLUDED.risk_description;
                    """, [risk_id, description, r_severity])

            # 2. Evaluate Model Validation Anomalies
            failed_models = conn.execute("""
                SELECT model_id, validation_name, recommendation
                FROM aigct_core.model_validation
                WHERE run_id = ? AND validation_result = 'PASSED WITH WARNINGS';
            """, [p_run_id]).fetchall()
            
            for model_id, val_name, recommendation in failed_models:
                risk_id = f"RSK_{p_run_id[-6:]}_{model_id[-4:]}"
                description = f"Model Drift/Bias Alert: {val_name} on {model_id}. Action Required: {recommendation}"
                
                conn.execute("""
                    INSERT INTO aigct_core.risk_register (
                        risk_id, risk_description, category, severity, status, owner, risk_owner_group
                    ) VALUES (?, ?, 'MODEL_RISK', 'High', 'Open', 'MODEL_RISK_AGENT', 'RISK_MANAGEMENT')
                    ON CONFLICT (risk_id) DO UPDATE SET risk_description = EXCLUDED.risk_description;
                """, [risk_id, description])
                
        logger.info("✅ Risk assessment ledger update complete.")
