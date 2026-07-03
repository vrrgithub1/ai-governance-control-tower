import os
from datetime import datetime
import json
from src.database import DatabaseManager

class GovernanceRunProcess:
    def __init__(self, db_manager: DatabaseManager):
        """Initializes the coordinator by injecting the centralized thread-safe connection manager."""
        self.db = db_manager

    # ====================================================================================
    # COMPLIANCE SYSTEM SEEDING UTILITIES
    # ====================================================================================
    def seed_infrastructure_defaults(self) -> None:
        """Seeds standard system assets to secure foreign key integrity for non-data task operations."""
        seed_query = """
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
        with self.db.connection() as conn:
            conn.execute(seed_query)

    # ====================================================================================
    # LIFECYCLE STAGE 1: GOVERNANCE_EXECUTION (Master Runs Tracking)
    # ====================================================================================
    def add_new_run_id(self, p_trigger_source: str, p_triggered_by: str) -> str:
        """Generates sequential tracking identifiers and boots a daily processing window token."""
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"RUN_{current_date_str}_%"
        
        source = p_trigger_source.strip().upper()
        actor = p_triggered_by.strip()

        with self.db.connection() as conn:
            query_find_max = "SELECT MAX(run_id) FROM aigct_core.governance_execution WHERE run_id LIKE ?;"
            result = conn.execute(query_find_max, [search_pattern]).fetchone()
            new_sequence = int(result[0].split("_")[-1]) + 1 if result and result[0] else 1
            new_run_id = f"RUN_{current_date_str}_{new_sequence:03d}"

            query_insert = """
                INSERT INTO aigct_core.governance_execution (
                    run_id, start_time, end_time, status, trigger_source, 
                    triggered_by, total_assets, total_models, overall_status, 
                    execution_time_seconds, total_processes
                ) VALUES (?, CURRENT_TIMESTAMP, NULL, 'In Progress', ?, ?, NULL, NULL, 'RUNNING', NULL, NULL);
            """
            conn.execute(query_insert, [new_run_id, source, actor])
            return new_run_id

    def complete_run_id(self, p_run_id: str, p_total_assets: int = None, p_total_models: int = None) -> bool:
        """Closes a run window, calculates run times, and evaluates total processing health."""
        with self.db.connection() as conn:
            # Aggregate task parameters dynamically from internal logging matrix tables
            metrics_query = """
                SELECT 
                    COUNT(process_id) as total_procs,
                    SUM(records_read) as total_read,
                    SUM(records_failed) as total_fail,
                    COUNT(CASE WHEN status = 'Failed' THEN 1 END) as crashed_procs
                FROM aigct_core.governance_execution_process
                WHERE run_id = ?;
            """
            metrics = conn.execute(metrics_query, [p_run_id]).fetchone()
            total_procs = metrics[0] or 0
            total_read = metrics[1] or 0
            total_fail = metrics[2] or 0
            crashed_procs = metrics[3] or 0

            # Compute payload health parameters
            if crashed_procs > 0:
                derived_overall = "FAILED"
            elif total_fail == 0 and total_read > 0:
                derived_overall = "PASSED"
            elif total_fail > 0:
                derived_overall = "PASSED WITH WARNINGS"
            else:
                derived_overall = "FAILED"

            query_complete = """
                UPDATE aigct_core.governance_execution
                SET 
                    end_time = CURRENT_TIMESTAMP,
                    status = 'Completed',
                    total_assets = COALESCE(?, total_assets),
                    total_models = COALESCE(?, total_models),
                    overall_status = ?,
                    total_processes = ?,
                    execution_time_seconds = EPOCH(CURRENT_TIMESTAMP - start_time)
                WHERE run_id = ?;
            """
            conn.execute(query_complete, [p_total_assets, p_total_models, derived_overall, total_procs, p_run_id])
            return True

    def fail_run_id(self, p_run_id: str) -> bool:
        """Emergency method to forcefully mark a master running context loop as crashed."""
        query_fail = """
            UPDATE aigct_core.governance_execution
            SET 
                end_time = CURRENT_TIMESTAMP,
                status = 'Failed',
                overall_status = 'FAILED',
                execution_time_seconds = EPOCH(CURRENT_TIMESTAMP - start_time)
            WHERE run_id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_fail, [p_run_id])
            return True

    # ====================================================================================
    # LIFECYCLE STAGE 2: GOVERNANCE_EXECUTION_PROCESS (Task Processes Engine)
    # ====================================================================================
    def add_new_process_id(self, p_process_name: str, p_run_id: str, p_dataset_id: str = None, 
                           p_layer_name: str = "INFRASTRUCTURE", p_process_code: str = None, 
                           p_params_dict: dict = None, p_parent_process_id: str = None) -> str:
        """Registers a unique sub-process tracking node. Defaults non-data work contexts to 'SYSTEM'."""
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"PRC_{current_date_str}_%"
        
        # Apply strict Option A architecture rule overrides
        dataset_target = p_dataset_id if p_dataset_id else "SYSTEM"
        params_json = json.dumps(p_params_dict) if p_params_dict else None

        with self.db.connection() as conn:
            query_find_max = "SELECT MAX(process_id) FROM aigct_core.governance_execution_process WHERE process_id LIKE ?;"
            result = conn.execute(query_find_max, [search_pattern]).fetchone()
            new_sequence = int(result[0].split("_")[-1]) + 1 if result and result[0] else 1
            new_process_id = f"PRC_{current_date_str}_{new_sequence:03d}"

            query_insert = """
                INSERT INTO aigct_core.governance_execution_process (
                    process_id, process_name, run_id, dataset_id, layer_name, 
                    status, records_read, records_passed, records_failed, 
                    start_time, end_time, run_time_seconds, process_code, 
                    process_parameters_json, parent_process_id
                ) VALUES (?, ?, ?, ?, ?, 'In Progress', NULL, NULL, NULL, CURRENT_TIMESTAMP, NULL, NULL, ?, ?, ?);
            """
            conn.execute(query_insert, [
                new_process_id, p_process_name, p_run_id, dataset_target, 
                p_layer_name, p_process_code, params_json, p_parent_process_id
            ])
            return new_process_id

    def complete_process_id(self, p_process_id: str, p_read: int = 0, p_passed: int = 0, p_failed: int = 0, p_status: str = "Completed") -> bool:
        """Concludes individual tasks and logs calculated runtime metadata parameters."""
        query_complete = """
            UPDATE aigct_core.governance_execution_process
            SET 
                status = ?,
                records_read = ?,
                records_passed = ?,
                records_failed = ?,
                end_time = CURRENT_TIMESTAMP,
                run_time_seconds = CAST(EPOCH(CURRENT_TIMESTAMP - start_time) AS SMALLINT)
            WHERE process_id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_complete, [p_status, p_read, p_passed, p_failed, p_process_id])
            return True

    # ====================================================================================
    # LIFECYCLE STAGE 3: LOGGING COMPLIANCE TELEMETRY (Audit & DQ Traces)
    # ====================================================================================
    def log_audit_event(self, p_run_id: str, p_process_id: str, p_event_type: str, 
                        p_entity_type: str, p_entity_id: str, p_user: str, 
                        p_prev: str = None, p_new: str = None, p_desc: str = None) -> str:
        """Creates formal regulatory audit markers across ingestion boundaries."""
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"EVT_{current_date_str}_%"

        with self.db.connection() as conn:
            query_find_max = "SELECT MAX(event_id) FROM aigct_core.audit_event WHERE event_id LIKE ?;"
            result = conn.execute(query_find_max, [search_pattern]).fetchone()
            new_sequence = int(result[0].split("_")[-1]) + 1 if result and result[0] else 1
            new_event_id = f"EVT_{current_date_str}_{new_sequence:03d}"

            query_insert = """
                INSERT INTO aigct_core.audit_event (
                    event_id, run_id, process_id, event_timestamp, event_type, 
                    entity_type, entity_id, performed_by, previous_value, 
                    new_value, event_description
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?);
            """
            conn.execute(query_insert, [
                new_event_id, p_run_id, p_process_id, p_event_type, 
                p_entity_type, p_entity_id, p_user, p_prev, p_new, p_desc
            ])
            return new_event_id

    def log_data_quality_result(self, p_run_id: str, p_dataset_id: str, p_check_name: str, 
                                p_type: str, p_status: str, p_expected: str, p_actual: str, 
                                p_severity: str, p_total: int, p_failed: int) -> bool:
        """Persists the outcome of data quality checks and computes structural asset quality metrics."""
        # Avoid zero-division anomalies
        failure_pct = (p_failed / p_total) * 100.0 if p_total > 0 else 0.0
        quality_score = 100.0 - failure_pct

        query_dq = """
            INSERT INTO aigct_core.data_quality_results (
                run_id, dataset_id, check_name, check_type, check_status, 
                expected_value, actual_value, quality_score, severity, 
                run_date, total_records, failed_records, failure_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?);
        """
        with self.db.connection() as conn:
            conn.execute(query_dq, [
                p_run_id, p_dataset_id, p_check_name, p_type, p_status, 
                p_expected, p_actual, quality_score, p_severity, p_total, p_failed, failure_pct
            ])
            return True
        