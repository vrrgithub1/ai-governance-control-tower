import os
import csv
import random
import logging
from datetime import datetime
import duckdb
from src.database_manager import DatabaseManager
from src.tracker_engine import GovernanceRunProcess

logger = logging.getLogger("AIGCT_Trade_Pipeline")

class TradeTransactionsPipeline:
    def __init__(self, db_manager: DatabaseManager, tracker: GovernanceRunProcess):
        self.db = db_manager
        self.tracker = tracker
        self.dataset_id = "DS_TRADE_TRANS"

    def _generate_mock_trade_file(self, target_path: str) -> int:
        """
        Simulates an upstream Bloomberg data extraction extraction layer.
        Generates a mix of valid rows and zero/negative trade amount anomalies.
        """
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "JPM", "GS"]
        side_options = ["BUY", "SELL"]
        
        # Scale dynamic daily transaction volume sizes
        record_count = random.randint(300, 500)
        
        with open(target_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["trade_id", "ticker", "side", "quantity", "trade_amount"])
            
            for i in range(record_count):
                t_id = f"TRD_{2026}{random.randint(100000, 999999)}"
                ticker = random.choice(tickers)
                side = random.choice(side_options)
                quantity = random.randint(10, 5000)
                
                # 💡 INTENTIONAL ANOMALY: Inject negative/zero values (~3% probability) 
                # to trigger your QR_TRADE_AMT_POSITIVE quality rule definition.
                if random.random() < 0.03:
                    trade_amount = random.choice([0.0, -150.50, -2500.0])
                else:
                    trade_amount = round(quantity * random.uniform(50.0, 400.0), 2)
                    
                writer.writerow([t_id, ticker, side, quantity, trade_amount])
                
        return record_count

    def run_pipeline(self, p_run_id: str, source_csv_path: str) -> bool:
        """Executes the sequential data ingestion flow for the Capital Markets payload."""
        logger.info(f"🚀 Kicking off ingestion sequence for dataset: {self.dataset_id}")
        
        # ---------------------------------------------------------------------------
        # PHASE 1: GENERATE EXPECTED ROADMAP (Option 1 Strategy)
        # ---------------------------------------------------------------------------
        steps_roadmap = {
            "DATA_SOURCE": {"name": "Simulate Bloomberg Extraction & Sourcing", "layer": "INGEST_SIM"},
            "BRONZE_LOAD": {"name": "Extract & Load Trade File to Bronze", "layer": "BRONZE"},
            "SILVER_VAL":  {"name": "Schema Enforcement & Silver Isolation", "layer": "SILVER"},
            "DQ_EVAL":     {"name": "Execute Trade Compliance Quality Rules", "layer": "SILVER"},
            "GOLD_PUB":    {"name": "Materialize Canonical Capital Markets Analytics", "layer": "GOLD"}
        }
        
        for step_key, step_info in steps_roadmap.items():
            steps_roadmap[step_key]["id"] = self.tracker.add_new_process_id(
                p_process_name=step_info["name"],
                p_run_id=p_run_id,
                p_dataset_id=self.dataset_id,
                p_layer_name=step_info["layer"],
                p_process_code=f"trade_transactions_pipeline.{step_key.lower()}()"
            )

        try:
            # ---------------------------------------------------------------------------
            # STEP 1: AUTOMATED DATA SOURCING GENERATION
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["DATA_SOURCE"]["id"]
            logger.info("⚡ Executing Automated Trade Sourcing Simulation...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")
            
            generated_lines = self._generate_mock_trade_file(source_csv_path)
            
            self.tracker.complete_process_id(step_id, p_read=generated_lines, p_passed=generated_lines, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "SOURCE_EXTRACT", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Sourcing extraction clear. Generated {generated_lines} mock market rows.")

            # ---------------------------------------------------------------------------
            # STEP 2: LOAD BRONZE LAYER
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["BRONZE_LOAD"]["id"]
            logger.info("⚡ Loading Raw File to Bronze relational store...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")
            
            with self.db.connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS aigct_bronze.trade_transactions (
                        record_number INT,
                        trade_id VARCHAR,
                        ticker VARCHAR,
                        side VARCHAR,
                        quantity INT,
                        trade_amount DOUBLE,
                        ingest_timestamp TIMESTAMP,
                        run_id VARCHAR
                    );
                """)
                
                load_query = """
                    INSERT INTO aigct_bronze.trade_transactions
                    SELECT 
                        nextval('main.record_number_seq') as record_number,
                        trade_id, ticker, side, quantity, trade_amount,
                        CURRENT_TIMESTAMP as ingest_timestamp,
                        ? as run_id
                    FROM read_csv_auto(?);
                """
                conn.execute(load_query, [p_run_id, source_csv_path])
                records_loaded = conn.execute("SELECT COUNT(*) FROM aigct_bronze.trade_transactions WHERE run_id = ?;", [p_run_id]).fetchone()[0]

            self.tracker.complete_process_id(step_id, p_read=records_loaded, p_passed=records_loaded, p_failed=0, p_status="Completed")
            self.tracker.log_audit_event(p_run_id, step_id, "DATA_INGEST", "Dataset", self.dataset_id, "PIPELINE_ENGINE", p_desc=f"Bronze conversion complete. Relational row count: {records_loaded}.")

            # ---------------------------------------------------------------------------
            # STEP 3: APPLY SILVER VALIDATION / QUARANTINE
            # ---------------------------------------------------------------------------
            step_id = steps_roadmap["SILVER_VAL"]["id"]
            logger.info("⚡ Running Structural Contract Schema Enforcement...")
            self.tracker.complete_process_id(step_id, p_status="In Progress")

            with self.db.connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_silver.trade_transactions AS SELECT * FROM aigct_bronze.trade_transactions WHERE 1=0;")
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_quarantine.trade_transactions AS SELECT * FROM aigct_bronze.trade_transactions WHERE 1=0;")

                # Foundational Contract: trade_id and ticker must be fully populated strings
                split_passed_query = """
                    INSERT INTO aigct_silver.trade_transactions
                    SELECT * FROM aigct_bronze.trade_transactions 
                    WHERE run_id = ? AND trade_id IS NOT NULL AND trade_id != '' AND ticker IS NOT NULL AND ticker != '';
                """
                split_failed_query = """
                    INSERT INTO aigct_quarantine.trade_transactions
                    SELECT * FROM aigct_bronze.trade_transactions 
                    WHERE run_id = ? AND (trade_id IS NULL OR trade_id = '' OR ticker IS NULL OR ticker = '');
                """
                conn.execute(split_passed_query, [p_run_id])
                conn.execute(split_failed_query, [p_run_id])

                passed_count = conn.execute("SELECT COUNT(*) FROM aigct_silver.trade_transactions WHERE run_id = ?;", [p_run_id]).fetchone()[0]
                failed_count = conn.execute("SELECT COUNT(*) FROM aigct_quarantine.trade_transactions WHERE run_id = ?;", [p_run_id]).fetchone()[0]

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
                    dq_eval_query = f"SELECT COUNT(*) FROM aigct_silver.trade_transactions WHERE run_id = ? AND ({r_expr});"
                    broken_rows = conn.execute(dq_eval_query, [p_run_id]).fetchone()[0]
                    
                    check_status = "FAIL" if broken_rows > 0 else "PASS"
                    
                    self.tracker.log_data_quality_result(
                        p_run_id=p_run_id, p_dataset_id=self.dataset_id, p_check_name=r_name,
                        p_type=r_type, p_status=check_status, p_expected="Positive Numerical Matrix",
                        p_actual=f"{broken_rows} Non-Positive Rows Found", p_severity=r_severity,
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
                conn.execute("CREATE TABLE IF NOT EXISTS aigct_gold.trade_transactions AS SELECT * FROM aigct_silver.trade_transactions WHERE 1=0;")
                publish_query = "INSERT INTO aigct_gold.trade_transactions SELECT * FROM aigct_silver.trade_transactions WHERE run_id = ?;"
                conn.execute(publish_query, [p_run_id])

            self.tracker.complete_process_id(step_id, p_read=passed_count, p_passed=passed_count, p_failed=0, p_status="Completed")
            logger.info(f"🎉 Trade pipeline run execution complete for token: {p_run_id}")
            return True

        except Exception as pipeline_error:
            logger.critical(f"💥 Trade pipeline crashed: {str(pipeline_error)}")
            for step_key, step_info in steps_roadmap.items():
                if "id" in step_info:
                    self.tracker.complete_process_id(step_info["id"], p_status="Failed")
            raise pipeline_error
        