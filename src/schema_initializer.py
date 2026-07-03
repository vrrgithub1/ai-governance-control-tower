import logging
from src.database_manager import DatabaseManager

logger = logging.getLogger("AIGCT_Initializer")

class SchemaInitializer:
    # 1. Define your bug-free, optimized v1.3 Medallion DDL layout blocks
    CORE_SCHEMAS_DDL = """
        CREATE SCHEMA IF NOT EXISTS aigct_core;
        CREATE SCHEMA IF NOT EXISTS aigct_bronze;
        CREATE SCHEMA IF NOT EXISTS aigct_silver;
        CREATE SCHEMA IF NOT EXISTS aigct_quarantine;
        CREATE SCHEMA IF NOT EXISTS aigct_gold;
    """

    GOVERNANCE_EXECUTION_TABLE = """
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
    """
    
    # ... Include definitions for governance_execution_process, data_asset_inventory, etc. ...

    SEED_SYSTEM_ASSET = """
        INSERT INTO aigct_core.data_asset_inventory (
            dataset_id, dataset_name, data_domain, source_system, data_owner, 
            data_steward, classification, contains_pii, contains_financial_data, 
            contains_critical_data_element, data_retention_period, quality_sla, 
            refresh_frequency, lineage_available, status, data_quality_score
        ) VALUES (
            'SYSTEM', 'Core Pipeline Infrastructure Services', 'Infrastructure', 
            'ORCHESTRATOR', 'Platform Engineering', 'Platform Engineering', 'Internal', 
            FALSE, FALSE, FALSE, 0, 100.0, 'Daily', FALSE, 'Active', 100.0
        ) ON CONFLICT (dataset_id) DO NOTHING;
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def initialize_database(self) -> None:
        """Executes DDL layouts sequentially and locks down referential seed properties."""
        logger.info("Initializing embedded DuckDB catalog namespaces...")
        with self.db.connection() as conn:
            # Execute Core structures
            conn.execute(self.CORE_SCHEMAS_DDL)
            conn.execute(self.GOVERNANCE_EXECUTION_TABLE)
            # ... execute other tables ...
            
            # Enforce option A referential integrity seed records
            conn.execute(self.SEED_SYSTEM_ASSET)
            
        logger.info("Database structural verification completed successfully.")
        