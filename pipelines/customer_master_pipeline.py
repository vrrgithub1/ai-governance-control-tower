import os
import csv
import random
import logging
from datetime import datetime
import duckdb
from src.database_manager import DatabaseManager
from src.tracker_engine import GovernanceRunProcess

logger = logging.getLogger("AIGCT_Customer_Pipeline")

class CustomerMasterPipeline:
    def __init__(self, db_manager: DatabaseManager, tracker: GovernanceRunProcess):
        self.db = db_manager
        self.tracker = tracker
        self.dataset_id = "DS_CUST_MASTER"

    def _generate_mock_landing_file(self, target_path: str) -> int:
        """
        Simulates an upstream extraction sourcing system.
        Generates a mix of valid records and intentional structural anomalies.
        """
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Sample distribution domains using standard professional business names
        first_names = ["Robert", "Sarah", "Michael", "Elena", "David", "Amina", "James", "Jonathan"]
        last_names = ["Sterling", "Vance", "Garrison", "Chen", "Barker", "Levin", "Yeddula", "Holt"]
        countries = ["United States", "United Kingdom", "India", "Tajikistan", "Pakistan"]
        
        # Determine a random file record size for this specific run window
        record_count = random.randint(100, 250)
        
        with open(target_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            # Write standard csv schema file headers
            writer.writerow(["customer_id", "customer_name", "email", "country"])
            
            for i in range(record_count):
                # 1. Generate an intentional NULL identifier anomaly (approx 5% of rows)
                if random.random() < 0.05:
                    c_id = ""
                else:
                    c_id = f"CUST_{2026}{random.randint(10000, 99999)}"
                
                # 2. Build out realistic corporate string fields
                f_name = random.choice(first_names)
                l_name = random.choice(last_names)
                c_name = f"{f_name} {l_name}"
                email = f"{f_name.lower()}.{l_name.lower()}@financial-tower.com"
                country = random.choice(countries)
                
                writer.writerow([c_id, c_name, email, country])
                
        return record_count

    def run_pipeline(self, p_run_id: str, source_csv_path: str) -> bool:
        """Executes the sequential data ingestion flow for the Customer Master payload."""
        logger.info(f"🚀 Kicking off ingestion sequence for dataset: {self.dataset_id}")
        
        # ---------------------------------------------------------------------------
        # PHASE 1: GENERATE EXPECTED ROADMAP (Updated with Sourcing Step)
        # ---------------------------------------------------------------------------
        steps_roadmap = {
            "DATA_SOURCE": {"name": "Simulate Upstream Data Extraction & Sourcing", "layer": "INGEST_SIM"},
            "BRONZE_LOAD": {"name": "Extract & Load Raw File to Bronze", "layer": "BRONZE"},
            "SILVER_VAL":  {"name": "Schema Enforcement & Silver Isolation", "layer": "SILVER"},
            "DQ_EVAL":     {"name": "Execute Deep Semantic Quality Rules", "layer": "SILVER"},
            "GOLD_PUB":    {"name": "Materialize Analytics Canonical Views", "layer": "GOLD"}
        }
        
        # Instantiate active tracking process tokens for each stage
        for step_key, step_info in steps_roadmap.items():
            steps_roadmap[step_key]["id"] = self.tracker.add_new_process_id(
                p_process_name=step_info["name"],
                p_run_id=p_run_id,
                p_dataset_id=self.dataset_id,
                p_layer_name=step_info["layer"],
                p_process_code=f"customer_master_pipeline.{step_key.lower()}()"
            )

        try:
            # ---------------------------------------------------------------------------
            # STEP 1: AUTOMATED DATA SOURCING GENERATION
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["DATA_SOURCE"]["id"]
            logger.info("⚡ Executing Automated Data Sourcing Step...")
            self.tracker.complete_process_id(step_id, p_read=0, p_passed=0, p_failed=0, p_status="In Progress")
            
            # Run the generator method directly to write to your data folder drop-zone
            generated_lines = self._generate_mock_landing_file(source_csv_path)
            
            self.tracker.complete_process_id(step_id, p_read=generated_lines, p_passed=generated_lines, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "SOURCE_EXTRACT", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Successfully extracted {generated_lines} rows from source database simulation.")

            # ---------------------------------------------------------------------------
            # STEP 2: LOAD BRONZE LAYER
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["BRONZE_LOAD"]["id"]
            logger.info("⚡ Executing Bronze Extraction Step...")
            self.tracker.complete_process_id(step_id, p_read=0, p_passed=0, p_failed=0, p_status="In Progress")
            
            with self.db.connection() as conn:
                # Ensure the record sequence counter object exists in main memory context
                conn.execute("CREATE SEQUENCE IF NOT EXISTS main.record_number_seq START 1;")
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS aigct_bronze.customer_master (
                        record_number INT,
                        customer_id VARCHAR,
                        customer_name VARCHAR,
                        email VARCHAR,
                        country VARCHAR,
                        ingest_timestamp TIMESTAMP,
                        run_id VARCHAR
                    );
                """)
                
                load_query = """
                    INSERT INTO aigct_bronze.customer_master
                    SELECT 
                        nextval('main.record_number_seq') as record_number,
                        customer_id, customer_name, email, country,
                        CURRENT_TIMESTAMP as ingest_timestamp,
                        ? as run_id
                    FROM read_csv_auto(?);
                """
                conn.execute(load_query, [p_run_id, source_csv_path])
                
                records_loaded = conn.execute(
                    "SELECT COUNT(*) FROM aigct_bronze.customer_master WHERE run_id = ?;", 
                    [p_run_id]
                ).fetchone()[0]

            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=records_loaded, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "DATA_INGEST", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Raw Bronze tier landing complete. Extracted {records_loaded} source lines.")

            # ---------------------------------------------------------------------------
            # STEP 3: APPLY SILVER VALIDATION / QUARANTINE
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["SILVER_VAL"]["id"]
            logger.info("⚡ Executing Silver Validation Split Step...")
            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=0, p_failed=0, p_status="In Progress")

            with self.db.connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_silver.customer_master AS SELECT * FROM aigct_bronze.customer_master WHERE 1=0;")
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_quarantine.customer_master AS SELECT * FROM aigct_bronze.customer_master WHERE 1=0;")

                split_passed_query = """
                    INSERT INTO aigct_silver.customer_master
                    SELECT * FROM aigct_bronze.customer_master 
                    WHERE run_id = ? AND customer_id IS NOT NULL AND customer_id != '';
                """
                split_failed_query = """
                    INSERT INTO aigct_quarantine.customer_master
                    SELECT * FROM aigct_bronze.customer_master 
                    WHERE run_id = ? AND (customer_id IS NULL OR customer_id = '');
                """
                conn.execute(split_passed_query, [p_run_id])
                conn.execute(split_failed_query, [p_run_id])

                passed_count = conn.execute("SELECT COUNT(*) FROM aigct_silver.customer_master WHERE run_id = ?;", [p_run_id]).fetchone()[0]
                failed_count = conn.execute("SELECT COUNT(*) FROM aigct_quarantine.customer_master WHERE run_id = ?;", [p_run_id]).fetchone()[0]

            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=passed_count, p_failed=failed_count, p_status="Completed")
            if failed_count > 0:
                self.tracker.log_audit_event(p_run_id, step_id, "SCHEMA_VARIANCE", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Structural contract anomalies isolated. Deflected {failed_count} lines to Quarantine storage.")

            # ---------------------------------------------------------------------------
            # STEP 4: EXECUTE METADATA-DRIVEN QUALITY RULES
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["DQ_EVAL"]["id"]
            logger.info("⚡ Running Deep Semantic Quality Evaluation Evaluators...")
            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=0, p_failed=0, p_status="In Progress")

            with self.db.connection() as conn:
                rules_query = "SELECT rule_id, rule_name, rule_type, rule_expression, severity FROM aigct_core.quality_rule_definition WHERE dataset_id = ? AND enabled_flag = TRUE;"
                active_rules = conn.execute(rules_query, [self.dataset_id]).fetchall()

                for rule in active_rules:
                    r_id, r_name, r_type, r_expr, r_severity = rule
                    dq_eval_query = f"SELECT COUNT(*) FROM aigct_silver.customer_master WHERE run_id = ? AND ({r_expr});"
                    broken_rows = conn.execute(dq_eval_query, [p_run_id]).fetchone()[0]
                    
                    check_status = "FAIL" if broken_rows > 0 else "PASS"
                    
                    self.tracker.log_data_quality_result(
                        p_run_id=p_run_id, p_dataset_id=self.dataset_id, p_check_name=r_name,
                        p_type=r_type, p_status=check_status, p_expected="0 Broken Rows",
                        p_actual=f"{broken_rows} Anomalous Rows", p_severity=r_severity,
                        p_total=passed_count, p_failed=broken_rows
                    )

            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=passed_count, p_failed=0, p_status="Completed")

            # ---------------------------------------------------------------------------
            # STEP 5: PUBLISH GOLD LAYER
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["GOLD_PUB"]["id"]
            logger.info("⚡ Materializing Canonical Business Reporting Tables...")
            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=0, p_failed=0, p_status="In Progress")

            with self.db.connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_gold.customer_master AS SELECT * FROM aigct_silver.customer_master WHERE 1=0;")
                publish_query = "INSERT INTO aigct_gold.customer_master SELECT * FROM aigct_silver.customer_master WHERE run_id = ?;"
                conn.execute(publish_query, [p_run_id])

            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=passed_count, p_failed=0, p_status="Completed")
            logger.info(f"🎉 Pipeline run execution successful for payload batch window: {p_run_id}")
            return True

        except Exception as pipeline_error:
            logger.critical(f"💥 Critical pipeline crash encountered during runtime loops: {str(pipeline_error)}")
            for step_key, step_info in steps_roadmap.items():
                if "id" in step_info:
                    self.tracker.complete_process_id(step_info["id"], p_read=0, p_passed=0, p_failed=0, p_status="Failed")
            raise pipeline_error