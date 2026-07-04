import os
import csv
import random
import logging
from datetime import datetime
from src.database_manager import DatabaseManager
from src.tracker_engine import GovernanceRunProcess

logger = logging.getLogger("AIGCT_Credit_Pipeline")

class CreditFeaturesPipeline:
    def __init__(self, db_manager: DatabaseManager, tracker: GovernanceRunProcess):
        self.db = db_manager
        self.tracker = tracker
        self.dataset_id = "DS_CREDIT_FEAT"

    def _generate_mock_credit_file(self, target_path: str) -> int:
        """
        Simulates an upstream machine learning feature store extraction layer.
        Generates a mix of valid records and intentional out-of-bounds credit scores.
        """
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Scale intermediate feature batch sizes
        record_count = random.randint(150, 300)
        
        with open(target_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["customer_id", "credit_score", "debt_to_income", "bankruptcy_indicator"])
            
            for i in range(record_count):
                c_id = f"CUST_2026{random.randint(10000, 99999)}"
                dti = round(random.uniform(0.05, 0.65), 4)
                bankruptcy = 1 if random.random() < 0.02 else 0
                
                # 💡 INTENTIONAL ANOMALY: Inject invalid FICO ranges (< 300 or > 850)
                # to test the QR_CRED_SCORE_RANGE evaluation rule flag.
                if random.random() < 0.04:
                    credit_score = random.choice([250, 890, 999, -10])
                else:
                    credit_score = random.randint(580, 820)
                    
                writer.writerow([c_id, credit_score, dti, bankruptcy])
                
        return record_count

    def run_pipeline(self, p_run_id: str, source_csv_path: str) -> bool:
        """Executes the sequential data ingestion flow for Risk Scoring Features."""
        logger.info(f"🚀 Kicking off ingestion sequence for dataset: {self.dataset_id}")
        
        # ---------------------------------------------------------------------------
        # PHASE 1: GENERATE EXPECTED ROADMAP (Option 1 Strategy)
        # ---------------------------------------------------------------------------
        steps_roadmap = {
            "DATA_SOURCE": {"name": "Simulate Feature Store Sourcing", "layer": "INGEST_SIM"},
            "BRONZE_LOAD": {"name": "Extract & Load Features to Bronze", "layer": "BRONZE"},
            "SILVER_VAL":  {"name": "Schema Enforcement & Silver Isolation", "layer": "SILVER"},
            "DQ_EVAL":     {"name": "Execute Credit Semantic Quality Rules", "layer": "SILVER"},
            "GOLD_PUB":    {"name": "Materialize Canonical Risk Scoring Analytics", "layer": "GOLD"}
        }
        
        for step_key, step_info in steps_roadmap.items():
            steps_roadmap[step_key]["id"] = self.tracker.add_new_process_id(
                p_process_name=step_info["name"],
                p_run_id=p_run_id,
                p_dataset_id=self.dataset_id,
                p_layer_name=step_info["layer"],
                p_process_code=f"credit_features_pipeline.{step_key.lower()}()"
            )

        try:
            # ---------------------------------------------------------------------------
            # STEP 1: AUTOMATED DATA SOURCING GENERATION
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["DATA_SOURCE"]["id"]
            logger.info("⚡ Executing Automated Credit Data Sourcing Simulation...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")
            
            generated_lines = self._generate_mock_credit_file(source_csv_path)
            
            self.tracker.complete_process_id(step_id, p_read=generated_lines, p_passed=generated_lines, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "SOURCE_EXTRACT", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Sourcing extraction clear. Generated {generated_lines} credit scoring rows.")

            # ---------------------------------------------------------------------------
            # STEP 2: LOAD BRONZE LAYER
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["BRONZE_LOAD"]["id"]
            logger.info("⚡ Loading Raw File to Bronze relational store...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")
            
            with self.db.connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS aigct_bronze.credit_features (
                        record_number INT,
                        customer_id VARCHAR,
                        credit_score INT,
                        debt_to_income DOUBLE,
                        bankruptcy_indicator INT,
                        ingest_timestamp TIMESTAMP,
                        run_id VARCHAR
                    );
                """)
                
                load_query = """
                    INSERT INTO aigct_bronze.credit_features
                    SELECT 
                        nextval('main.record_number_seq') as record_number,
                        customer_id, credit_score, debt_to_income, bankruptcy_indicator,
                        CURRENT_TIMESTAMP as ingest_timestamp,
                        ? as run_id
                    FROM read_csv_auto(?);
                """
                conn.execute(load_query, [p_run_id, source_csv_path])
                records_loaded = conn.execute("SELECT COUNT(*) FROM aigct_bronze.credit_features WHERE run_id = ?;", [p_run_id]).fetchone()[0]

            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=records_loaded, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "DATA_INGEST", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Bronze loading clear. Relational row count: {records_loaded}.")

            # ---------------------------------------------------------------------------
            # STEP 3: APPLY SILVER VALIDATION / QUARANTINE
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["SILVER_VAL"]["id"]
            logger.info("⚡ Running Structural Contract Schema Enforcement...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")

            with self.db.connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_silver.credit_features AS SELECT * FROM aigct_bronze.credit_features WHERE 1=0;")
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_quarantine.credit_features AS SELECT * FROM aigct_bronze.credit_features WHERE 1=0;")

                # Foundational Contract: customer_id must be present
                split_passed_query = """
                    INSERT INTO aigct_silver.credit_features
                    SELECT * FROM aigct_bronze.credit_features 
                    WHERE run_id = ? AND customer_id IS NOT NULL AND customer_id != '';
                """
                split_failed_query = """
                    INSERT INTO aigct_quarantine.credit_features
                    SELECT * FROM aigct_bronze.credit_features 
                    WHERE run_id = ? AND (customer_id IS NULL OR customer_id = '');
                """
                conn.execute(split_passed_query, [p_run_id])
                conn.execute(split_failed_query, [p_run_id])

                passed_count = conn.execute("SELECT COUNT(*) FROM aigct_silver.credit_features WHERE run_id = ?;", [p_run_id]).fetchone()[0]
                failed_count = conn.execute("SELECT COUNT(*) FROM aigct_quarantine.credit_features WHERE run_id = ?;", [p_run_id]).fetchone()[0]

            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=passed_count, p_failed=failed_count, p_status="Completed")
            if failed_count > 0:
                self.tracker.log_audit_event(p_run_id, step_id, "SCHEMA_VARIANCE", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Structural violations flagged. Isolated {failed_count} lines to Quarantine.")

            # ---------------------------------------------------------------------------
            # STEP 4: EXECUTE METADATA-DRIVEN QUALITY RULES
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["DQ_EVAL"]["id"]
            logger.info("⚡ Executing Business Semantic Data Quality Regulations...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")

            with self.db.connection() as conn:
                rules_query = "SELECT rule_id, rule_name, rule_type, rule_expression, severity FROM aigct_core.quality_rule_definition WHERE dataset_id = ? AND enabled_flag = TRUE;"
                active_rules = conn.execute(rules_query, [self.dataset_id]).fetchall()

                for rule in active_rules:
                    r_id, r_name, r_type, r_expr, r_severity = rule
                    dq_eval_query = f"SELECT COUNT(*) FROM aigct_silver.credit_features WHERE run_id = ? AND ({r_expr});"
                    broken_rows = conn.execute(dq_eval_query, [p_run_id]).fetchone()[0]
                    
                    check_status = "FAIL" if broken_rows > 0 else "PASS"
                    
                    self.tracker.log_data_quality_result(
                        p_run_id=p_run_id, p_dataset_id=self.dataset_id, p_check_name=r_name,
                        p_type=r_type, p_status=check_status, p_expected="FICO Standard Range (300-850)",
                        p_actual=f"{broken_rows} Out-of-Bounds Rows Found", p_severity=r_severity,
                        p_total=passed_count, p_failed=broken_rows
                    )

            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=passed_count, p_failed=0, p_status="Completed")

            # ---------------------------------------------------------------------------
            # STEP 5: PUBLISH GOLD LAYER
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["GOLD_PUB"]["id"]
            logger.info("⚡ Consolidating canonical Gold reporting ledger metrics...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")

            with self.db.connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_gold.credit_features AS SELECT * FROM aigct_silver.credit_features WHERE 1=0;")
                publish_query = "INSERT INTO aigct_gold.credit_features SELECT * FROM aigct_silver.credit_features WHERE run_id = ?;"
                conn.execute(publish_query, [p_run_id])

            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=passed_count, p_failed=0, p_status="Completed")
            logger.info(f"🎉 Credit feature pipeline run execution complete for token: {p_run_id}")
            return True

        except Exception as pipeline_error:
            logger.critical(f"💥 Credit pipeline crashed: {str(pipeline_error)}")
            for step_key, step_info in steps_roadmap.items():
                if "id" in step_info:
                    self.tracker.complete_process_id(step_info["id"], p_status="Failed")
            raise pipeline_error
        