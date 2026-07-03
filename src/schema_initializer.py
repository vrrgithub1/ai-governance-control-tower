import os
import logging
from src.database_manager import DatabaseManager  # Retained from your backup

logger = logging.getLogger("AIGCT_Initializer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SchemaInitializer:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def execute_ddl(self) -> None:
        """Sequential execution of the pristine v1.3 core metadata schema architecture."""
        
        # 1. Namespace Layers Creation
        schemas_ddl = """
            CREATE SCHEMA IF NOT EXISTS aigct_core;
            CREATE SCHEMA IF NOT EXISTS aigct_bronze;
            CREATE SCHEMA IF NOT EXISTS aigct_silver;
            CREATE SCHEMA IF NOT EXISTS aigct_quarantine;
            CREATE SCHEMA IF NOT EXISTS aigct_gold;
        """

        # 2. Complete Core Tables (v1.3 layout matching pgModeler)
        tables_ddl = [
            """
            CREATE TABLE IF NOT EXISTS aigct_core.governance_execution (
                run_id VARCHAR NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status VARCHAR NOT NULL,
                trigger_source VARCHAR NOT NULL,
                triggered_by VARCHAR NOT NULL,
                total_assets SMALLINT,
                total_models SMALLINT,
                overall_status VARCHAR,
                execution_time_seconds INTEGER,
                total_processes SMALLINT,
                CONSTRAINT governance_execution_pk PRIMARY KEY (run_id),
                CONSTRAINT ge_check_cons_1 CHECK (status IN ('In Progress', 'Failed', 'Completed')),
                CONSTRAINT ge_check_cons_2 CHECK (trigger_source IN ('SCHEDULER', 'EVENT_DRIVEN', 'MANUAL_CLI', 'WEB_UI', 'CI_CD_PIPELINE', 'API_WEBHOOK')),
                CONSTRAINT ge_check_cons_3 CHECK (total_assets IS NULL OR total_assets >= 0),
                CONSTRAINT ge_check_cons_4 CHECK (total_models IS NULL OR total_models >= 0),
                CONSTRAINT ge_check_cons_5 CHECK (overall_status IN ('RUNNING', 'PASSED', 'PASSED WITH WARNINGS', 'FAILED')),
                CONSTRAINT ge_check_cons6 CHECK (execution_time_seconds IS NULL OR execution_time_seconds >= 0)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.governance_policy (
                policy_id VARCHAR NOT NULL,
                policy_name VARCHAR NOT NULL,
                version SMALLINT,
                owner VARCHAR,
                review_date DATE,
                policy_status VARCHAR NOT NULL,
                approved_by VARCHAR,
                created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                policy_category VARCHAR NOT NULL,
                effective_date DATE,
                expiration_date DATE,
                CONSTRAINT gp_pk1 PRIMARY KEY (policy_id),
                CONSTRAINT gp_check_cons_1 CHECK (policy_status IN ('Draft', 'Approved', 'Retired'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.data_asset_inventory (
                dataset_id VARCHAR NOT NULL,
                dataset_name VARCHAR NOT NULL,
                data_domain VARCHAR,
                source_system VARCHAR,
                data_owner VARCHAR,
                data_steward VARCHAR,
                classification VARCHAR,
                contains_pii BOOLEAN NOT NULL DEFAULT TRUE,
                contains_financial_data BOOLEAN NOT NULL DEFAULT TRUE,
                contains_critical_data_element BOOLEAN NOT NULL DEFAULT TRUE,
                data_retention_period INTEGER NOT NULL DEFAULT 10,
                quality_sla DOUBLE,
                refresh_frequency VARCHAR NOT NULL,
                lineage_available BOOLEAN NOT NULL,
                status VARCHAR NOT NULL,
                data_quality_score DOUBLE,
                created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                bronze_table VARCHAR,
                silver_table VARCHAR,
                gold_table VARCHAR,
                quarantine_table VARCHAR,
                CONSTRAINT dai_pk1 PRIMARY KEY (dataset_id),
                CONSTRAINT dai_check_cons_1 CHECK (classification IN ('Public', 'Internal', 'Confidential')),
                CONSTRAINT dai_check_cons_2 CHECK (refresh_frequency IN ('Daily', 'Near Real-Time')),
                CONSTRAINT dai_check_cons_3 CHECK (status IN ('Active', 'Retired'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.governance_execution_process (
                process_id VARCHAR NOT NULL,
                process_name VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                dataset_id VARCHAR,
                layer_name VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                records_read INTEGER,
                records_passed INTEGER,
                records_failed INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                run_time_seconds SMALLINT,
                process_code VARCHAR,
                process_parameters_json VARCHAR,
                parent_process_id VARCHAR,
                CONSTRAINT gep_pk1 PRIMARY KEY (process_id),
                CONSTRAINT gep_check_status CHECK (status IN ('In Progress', 'Failed', 'Completed')),
                CONSTRAINT gep_fk1 FOREIGN KEY (run_id) REFERENCES aigct_core.governance_execution (run_id),
                CONSTRAINT gep_fk2 FOREIGN KEY (dataset_id) REFERENCES aigct_core.data_asset_inventory (dataset_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.quality_rule_definition (
                rule_id VARCHAR NOT NULL,
                rule_name VARCHAR NOT NULL,
                dataset_id VARCHAR NOT NULL,
                column_name VARCHAR NOT NULL,
                rule_type VARCHAR NOT NULL,
                rule_expression VARCHAR NOT NULL,
                severity VARCHAR NOT NULL,
                enabled_flag BOOLEAN NOT NULL DEFAULT TRUE,
                rule_category VARCHAR NOT NULL,
                CONSTRAINT qrd_pk PRIMARY KEY (rule_id),
                CONSTRAINT qrd_check_cons_1 CHECK (severity IN ('High', 'Medium', 'Low')),
                CONSTRAINT qrd_check_cons_2 CHECK (rule_category IN ('Completeness', 'Validity', 'Uniqueness', 'Consistency', 'Accuracy', 'Timeliness', 'Freshness', 'Referential Integrity', 'Conformity')),
                CONSTRAINT qrd_fk1 FOREIGN KEY (dataset_id) REFERENCES aigct_core.data_asset_inventory (dataset_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.risk_register (
                risk_id VARCHAR NOT NULL,
                risk_description VARCHAR NOT NULL,
                category VARCHAR,
                severity VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                owner VARCHAR NOT NULL,
                created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                target_resolution_date DATE,
                risk_owner_group VARCHAR,
                related_policy_id VARCHAR,
                likelihood VARCHAR,
                impact VARCHAR,
                risk_score DOUBLE,
                CONSTRAINT rr_pk PRIMARY KEY (risk_id),
                CONSTRAINT rr_check_cons_1 CHECK (severity IN ('High', 'Medium', 'Low')),
                CONSTRAINT rr_check_cons_2 CHECK (status IN ('Open', 'Closed')),
                CONSTRAINT rr_fk1 FOREIGN KEY (related_policy_id) REFERENCES aigct_core.governance_policy (policy_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.model_inventory (
                model_id VARCHAR NOT NULL,
                model_name VARCHAR NOT NULL,
                model_type VARCHAR NOT NULL,
                model_criticality VARCHAR NOT NULL,
                business_function VARCHAR NOT NULL,
                model_owner VARCHAR NOT NULL,
                risk_tier VARCHAR NOT NULL,
                regulatory_impact VARCHAR,
                data_sensitivity VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                version VARCHAR NOT NULL,
                approval_status VARCHAR NOT NULL,
                last_validation_date DATE,
                next_review_date DATE,
                explainability_required BOOLEAN NOT NULL,
                human_oversight_required BOOLEAN NOT NULL,
                created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                model_framework VARCHAR,
                training_dataset VARCHAR,
                deployment_environment VARCHAR,
                endpoint_url VARCHAR,
                CONSTRAINT mi_pk PRIMARY KEY (model_id),
                CONSTRAINT mi_check_cons_1 CHECK (model_criticality IN ('Mission Critical', 'High', 'Medium', 'Low')),
                CONSTRAINT mi_check_cons_2 CHECK (risk_tier IN ('High', 'Medium', 'Low')),
                CONSTRAINT mi_check_cons_3 CHECK (data_sensitivity IN ('Public', 'Internal', 'Confidential')),
                CONSTRAINT mi_check_cons_4 CHECK (status IN ('Development', 'Testing', 'Production', 'Retired')),
                CONSTRAINT mi_check_cons_5 CHECK (approval_status IN ('Pending', 'Approved', 'Rejected'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.model_validation (
                validation_id VARCHAR NOT NULL,
                model_id VARCHAR NOT NULL,
                validation_type VARCHAR,
                validation_name VARCHAR,
                validator_name VARCHAR,
                validation_result VARCHAR,
                findings_count VARCHAR,
                recommendation VARCHAR,
                approval_status VARCHAR,
                next_review_date DATE,
                created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                run_id VARCHAR NOT NULL,
                CONSTRAINT mv_pk PRIMARY KEY (validation_id),
                CONSTRAINT mv_fk1 FOREIGN KEY (model_id) REFERENCES aigct_core.model_inventory (model_id),
                CONSTRAINT mv_fk2 FOREIGN KEY (run_id) REFERENCES aigct_core.governance_execution (run_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.audit_event (
                event_id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                process_id VARCHAR NOT NULL,
                event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                event_type VARCHAR,
                entity_type VARCHAR,
                entity_id VARCHAR,
                performed_by VARCHAR NOT NULL,
                previous_value VARCHAR,
                new_value VARCHAR,
                event_description VARCHAR,
                CONSTRAINT ae_pk PRIMARY KEY (event_id),
                CONSTRAINT ae_fk1 FOREIGN KEY (run_id) REFERENCES aigct_core.governance_execution (run_id),
                CONSTRAINT ae_fk2 FOREIGN KEY (process_id) REFERENCES aigct_core.governance_execution_process (process_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.data_quality_results (
                run_id VARCHAR NOT NULL,
                dataset_id VARCHAR NOT NULL,
                check_name VARCHAR NOT NULL,
                check_type VARCHAR,
                check_status VARCHAR,
                expected_value VARCHAR,
                actual_value VARCHAR,
                quality_score DOUBLE,
                severity VARCHAR,
                run_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_records INTEGER,
                failed_records INTEGER,
                failure_percentage DOUBLE,
                CONSTRAINT dar_pk PRIMARY KEY (run_id, dataset_id, check_name)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS aigct_core.governance_metrics (
                run_id VARCHAR NOT NULL,
                metric_name VARCHAR NOT NULL,
                metric_value DOUBLE,
                metric_unit VARCHAR,
                metric_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metric_category VARCHAR,
                CONSTRAINT gm_pk PRIMARY KEY (run_id, metric_name)
            );
            """
        ]

        # 3. Secure Option A Referencing Infrastructure Placeholder Row
        seed_system_asset = """
            INSERT INTO aigct_core.data_asset_inventory (
                dataset_id, dataset_name, data_domain, source_system, data_owner, 
                data_steward, classification, contains_pii, contains_financial_data, 
                contains_critical_data_element, data_retention_period, quality_sla, 
                refresh_frequency, lineage_available, status, data_quality_score,
                bronze_table, silver_table, gold_table, quarantine_table
            ) VALUES (
                'SYSTEM', 'Core Pipeline Infrastructure Services', 'Infrastructure', 
                'ORCHESTRATOR', 'Platform Engineering', 'Platform Engineering', 'Internal', 
                FALSE, FALSE, FALSE, 0, 100.0, 'Daily', FALSE, 'Active', 100.0,
                'N/A', 'N/A', 'N/A', 'N/A'
            ) ON CONFLICT (dataset_id) DO NOTHING;
        """

        logger.info("Executing fresh DDL compilation routines against target file...")
        with self.db.connection() as conn:
            # Create schemas
            conn.execute(schemas_ddl)
            # Create tables
            for ddl in tables_ddl:
                conn.execute(ddl)
            # Seed infrastructure token
            conn.execute(seed_system_asset)
            
        logger.info("🎉 Fresh AIGCT control tower relational meta model successfully mounted.")
