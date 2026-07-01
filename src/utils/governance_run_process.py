import os
from datetime import datetime
import duckdb
from src.database import DatabaseManager  
from config import Settings

class GovernanceRunProcess:
    def __init__(self, db_manager: DatabaseManager):
        """Initializes the coordinator by injecting the central thread-safe database manager."""
        self.db = db_manager

    # ====================================================================================
    # MASTER RUN MANAGERS (main.governance_execution)
    # ====================================================================================

    def add_new_run_id(self, p_trigger_source: str, p_triggered_by: str) -> str:
        """
        Generates a unique date-sequenced master Run_Id (RUN_YYYYMMDD_NNN),
        sets initial status trackers, and starts the global daily batch window.
        """
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"RUN_{current_date_str}_%"

        query_find_max_seq = """
            SELECT MAX(Run_Id) FROM main.governance_execution WHERE Run_Id LIKE ?;
        """

        # Enforce strict audit formatting constraints on invocation triggers
        source = p_trigger_source.strip().upper()
        actor = p_triggered_by.strip()
        
        VALID_SOURCES = {'SCHEDULER', 'EVENT_DRIVEN', 'MANUAL_CLI', 'WEB_UI', 'CI_CD_PIPELINE', 'API_WEBHOOK'}
        if source not in VALID_SOURCES:
            raise ValueError(f"❌ Audit Violation: Invalid Trigger_Source '{p_trigger_source}'. Must be one of {list(VALID_SOURCES)}")
        if not actor or len(actor) < 4:
            raise ValueError(f"❌ Audit Violation: 'p_triggered_by' context is too vague. Provided: '{p_triggered_by}'.")

        with self.db.connection() as conn:
            result = conn.execute(query_find_max_seq, [search_pattern]).fetchone()
            new_sequence = int(result[0].split("_")[-1]) + 1 if result and result[0] else 1
            new_run_id = f"RUN_{current_date_str}_{new_sequence:03d}"

            query_insert = """
                INSERT INTO main.governance_execution (
                    Run_Id, Start_Time, End_Time, Status, Trigger_Source, 
                    Triggered_By, Total_Datasets, Total_Models, Overall_Status
                )
                VALUES (?, CURRENT_TIMESTAMP, NULL, 'In Progress', ?, ?, NULL, NULL, 'RUNNING')
                ON CONFLICT (Run_Id) DO NOTHING; 
            """
            conn.execute(query_insert, [new_run_id, source, actor])
            return new_run_id

    def update_run_id(self, p_run_id: str, p_trigger_source: str = None, p_triggered_by: str = None, 
                      p_total_datasets: int = None, p_total_models: int = None, p_overall_status: str = None) -> bool:
        """Applies inline operational overrides to an active parent batch window."""
        query_update = """
            UPDATE main.governance_execution
            SET 
                Trigger_Source = COALESCE(?, Trigger_Source),
                Triggered_By = COALESCE(?, Triggered_By),
                Total_Datasets = COALESCE(?, Total_Datasets),
                Total_Models = COALESCE(?, Total_Models),
                Overall_Status = COALESCE(?, Overall_Status)
            WHERE Run_Id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_update, [p_trigger_source, p_triggered_by, p_total_datasets, p_total_models, p_overall_status, p_run_id])
            return True

    def complete_run_id(self, p_run_id: str, p_trigger_source: str = None, p_triggered_by: str = None, 
                        p_total_datasets: int = None, p_total_models: int = None, p_overall_status: str = None) -> bool:
        """Finalizes master run execution milestones, aggregates sub-task data quality health, and seals timestamps."""
        with self.db.connection() as conn:
            # If no manual status override is passed, dynamically compute it from task metrics
            if p_overall_status is None:
                metrics_query = """
                    SELECT 
                        SUM(Records_read) as total_read,
                        SUM(Records_failed) as total_failed,
                        COUNT(CASE WHEN Status = 'Failed' THEN 1 END) as failed_tasks
                    FROM main.governance_run_process
                    WHERE Run_Id = ?;
                """
                metrics = conn.execute(metrics_query, [p_run_id]).fetchone()
                total_read = metrics[0] or 0
                total_failed = metrics[1] or 0
                failed_tasks = metrics[2] or 0
                
                if failed_tasks > 0:
                    p_overall_status = "FAILED"
                elif total_failed == 0 and total_read > 0:
                    p_overall_status = "PASSED"
                elif total_failed > 0:
                    p_overall_status = "PASSED WITH WARNINGS"
                else:
                    p_overall_status = "FAILED" # Safety fallback if no tasks ran successfully

            query_complete = """
                UPDATE main.governance_execution
                SET 
                    Trigger_Source = COALESCE(?, Trigger_Source),
                    Triggered_By = COALESCE(?, Triggered_By),
                    Total_Datasets = COALESCE(?, Total_Datasets),
                    Total_Models = COALESCE(?, Total_Models),
                    Overall_Status = COALESCE(?, Overall_Status),
                    End_Time = CURRENT_TIMESTAMP,
                    Status = 'Completed'
                WHERE Run_Id = ?;
            """
            conn.execute(query_complete, [p_trigger_source, p_triggered_by, p_total_datasets, p_total_models, p_overall_status, p_run_id])
            return True

    def fail_run_id(self, p_run_id: str, p_overall_status_note: str = None) -> bool:
        """Emergency execution breaker. Forces the execution status to 'Completed' and stamps data state as 'FAILED'."""
        query_fail = """
            UPDATE main.governance_execution
            SET 
                End_Time = CURRENT_TIMESTAMP,
                Status = 'Completed',
                Overall_Status = COALESCE(?, 'FAILED - Critical Operational Exception Encountered')
            WHERE Run_Id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_fail, [p_overall_status_note, p_run_id])
            return True

    def get_current_active_run_id(self) -> str:
        """Retrieves the most recent active processing run tracking reference identifier token."""
        query_get_active = """
            SELECT MAX(Run_Id) FROM main.governance_execution WHERE Status = 'In Progress';
        """
        with self.db.connection() as conn:
            result = conn.execute(query_get_active).fetchone()
            return result[0] if result else None

    # ====================================================================================
    # INGESTION PIPELINE PROCESS MANAGERS (main.governance_run_process)
    # ====================================================================================

    def add_new_process_id(self, p_process_name: str, p_run_id: str, p_dataset_id: str = None, p_layer: str = None) -> str:
        """Generates a custom sequence process token (PRC_YYYYMMDD_NNN) for an individual data feed task."""
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"PRC_{current_date_str}_%"

        query_find_max_seq = """
            SELECT MAX(Process_Id) FROM main.governance_run_process WHERE Process_Id LIKE ?;
        """

        with self.db.connection() as conn:
            result = conn.execute(query_find_max_seq, [search_pattern]).fetchone()
            new_sequence = int(result[0].split("_")[-1]) + 1 if result and result[0] else 1
            new_process_id = f"PRC_{current_date_str}_{new_sequence:03d}"

            query_insert = """
                INSERT INTO main.governance_run_process (
                    Process_Id, Process_Name, Run_Id, Dataset_ID, Layer, 
                    Status, Records_read, Records_passed, Records_failed, Start_Time, End_Time
                )
                VALUES (?, ?, ?, ?, ?, 'In Progress', NULL, NULL, NULL, CURRENT_TIMESTAMP, NULL);
            """
            conn.execute(query_insert, [new_process_id, p_process_name, p_run_id, p_dataset_id, p_layer])
            return new_process_id

    def update_process_id(self, p_process_id: str, p_records_read: int = None, 
                          p_records_passed: int = None, p_records_failed: int = None, p_status: str = None) -> bool:
        """Applies intermediate operational metrics updates to an active step in the workflow process."""
        query_update = """
            UPDATE main.governance_run_process
            SET
                Records_read = COALESCE(?, Records_read),
                Records_passed = COALESCE(?, Records_passed),
                Records_failed = COALESCE(?, Records_failed),
                Status = COALESCE(?, Status)
            WHERE Process_Id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_update, [p_records_read, p_records_passed, p_records_failed, p_status, p_process_id])
            return True

    def complete_process_id(self, p_process_id: str, p_records_read: int = None, 
                            p_records_passed: int = None, p_records_failed: int = None, p_status: str = 'Completed') -> bool:
        """Logs completion metrics and seals timestamps for an individual pipeline step."""
        query_complete = """
            UPDATE main.governance_run_process
            SET
                Records_read = COALESCE(?, Records_read),
                Records_passed = COALESCE(?, Records_passed),
                Records_failed = COALESCE(?, Records_failed),
                Status = ?,
                End_Time = CURRENT_TIMESTAMP
            WHERE Process_Id = ?;
        """
        with self.db.connection() as conn:
            conn.execute(query_complete, [p_records_read, p_records_passed, p_records_failed, p_status, p_process_id])
            return True


# ====================================================================================
# Verification Test Rig Logic Block
# ====================================================================================
if __name__ == "__main__":
    from config import Settings
    # Build shared database configuration coordinator context
    db_manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)
    orchestration_engine = GovernanceRunProcess(db_manager=db_manager)
    
    print("--- 1. Generating Orchestration Run Context ---")
    active_run = orchestration_engine.add_new_run_id(p_trigger_source="MANUAL_CLI", p_triggered_by="ETL_Service_Account")
    print(f"Parent Run Established: {active_run}")

    print("\n--- 2. Starting Medallion Layer Sub-Processes ---")
    bronze_proc = orchestration_engine.add_new_process_id(
        p_process_name="Ingest Customer Data", 
        p_run_id=active_run, 
        p_dataset_id="D001", 
        p_layer="Bronze"
    )
    print(f"Launched Staging Process Context: {bronze_proc}")

    print("\n--- 3. Pushing Operational Metrics Real-Time ---")
    orchestration_engine.update_process_id(
        p_process_id=bronze_proc,
        p_records_read=10000,
        p_status="Validating Isolation Constraints"
    )
    print("Applied records parsed updates to active trace.")

    print("\n--- 4. Concluding Pipeline Phase Milestone ---")
    orchestration_engine.complete_process_id(
        p_process_id=bronze_proc,
        p_records_read=10000,
        p_records_passed=9850,
        p_records_failed=150,
        p_status="Completed With Quarantines"
    )
    print(f"Finalized Step: {bronze_proc}")

    # Finally, close parent workflow wrapper
    orchestration_engine.complete_run_id(p_run_id=active_run, p_total_datasets=1, p_total_models=0, p_overall_status="Success")
    print(f"\n🎉 Verification loop complete. Pipeline states preserved cleanly.")
    