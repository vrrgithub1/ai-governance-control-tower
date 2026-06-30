import os
from datetime import datetime
import duckdb

class GovernanceRunProcess:
    def __init__(self, db_path: str = "database/ai_governance_control_tower.db"):
        """Initializes connection to the DuckDB instance and sets up execution schema."""
        self.db_path = db_path
        self._init_table()

    def _get_connection(self):
        """Returns a new connection context to DuckDB."""
        return duckdb.connect(self.db_path)

    def _init_table(self):
        """Ensures that the target metadata state collection table exists."""
        query = """
        CREATE TABLE IF NOT EXISTS main.governance_execution (
            Run_Id VARCHAR PRIMARY KEY,
            Start_Time TIMESTAMP,
            End_Time TIMESTAMP,
            Status VARCHAR,
            Trigger_Source VARCHAR,
            Triggered_By VARCHAR,
            Total_Datasets INTEGER,
            Total_Models INTEGER,
            Overall_Status VARCHAR
        );
        """
        with self._get_connection() as conn:
            conn.execute(query)

    def add_new_run_id(self, p_trigger_source: str, p_triggered_by: str) -> str:
        """
        Generates a custom sequence string token for the daily window matrix partition 
        and inserts a baseline orchestration record tracker.
        
        Format: RUN_YYYYMMDD_NNN
        """
        current_date_str = datetime.now().strftime("%Y%m%d")
        search_pattern = f"RUN_{current_date_str}_%"

        query_find_max_seq = """
            SELECT MAX(Run_Id) 
            FROM main.governance_execution 
            WHERE Run_Id LIKE ?;
        """

        with self._get_connection() as conn:
            # Discover highest sequence value allocated for the current date partition
            result = conn.execute(query_find_max_seq, [search_pattern]).fetchone()
            
            if result and result[0]:
                # Extract sequence value suffix, cast, increment, and repackage
                last_run_id = result[0]
                last_sequence = int(last_run_id.split("_")[-1])
                new_sequence = last_sequence + 1
            else:
                new_sequence = 1

            new_run_id = f"RUN_{current_date_str}_{new_sequence:03d}"

            # Hydrate orchestration log block
            query_insert = """
                INSERT INTO main.governance_execution (
                    Run_Id, Start_Time, End_Time, Status, Trigger_Source, 
                    Triggered_By, Total_Datasets, Total_Models, Overall_Status
                )
                VALUES (?, CURRENT_TIMESTAMP, NULL, 'In Progress', ?, ?, NULL, NULL, NULL);
            """
            conn.execute(query_insert, [new_run_id, p_trigger_source, p_triggered_by])
            return new_run_id

    def update_run_id(self, p_run_id: str, p_trigger_source: str = None, p_triggered_by: str = None, 
                      p_total_datasets: int = None, p_total_models: int = None, p_overall_status: str = None) -> bool:
        """Applies positional parameter overrides to the active target run identifier."""
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
        with self._get_connection() as conn:
            conn.execute(query_update, [p_trigger_source, p_triggered_by, p_total_datasets, p_total_models, p_overall_status, p_run_id])
            return True

    def complete_run_id(self, p_run_id: str, p_trigger_source: str = None, p_triggered_by: str = None, 
                        p_total_datasets: int = None, p_total_models: int = None, p_overall_status: str = None) -> bool:
        """Finalizes processing milestones and locks tracking state variables."""
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
        with self._get_connection() as conn:
            conn.execute(query_complete, [p_trigger_source, p_triggered_by, p_total_datasets, p_total_models, p_overall_status, p_run_id])
            return True

    def get_current_active_run_id(self) -> str:
        """Retrieves the most recent active processing run tracking reference identifier token."""
        query_get_active = """
            SELECT MAX(Run_Id)
            FROM main.governance_execution
            WHERE Status = 'In Progress';
        """
        with self._get_connection() as conn:
            result = conn.execute(query_get_active).fetchone()
            return result[0] if result else None

# ==========================================
# Verification Test Rig Logic Block
# ==========================================
if __name__ == "__main__":
    # Setup test matrix engine
    orchestration_manager = GovernanceRunProcess("database/ai_governance_control_tower.db")
    
    print("--- 1. Testing Run Creation Logic ---")
    first_run = orchestration_manager.add_new_run_id(p_trigger_source="Airflow", p_triggered_by="CI_CD_Service")
    print(f"Created First Execution Matrix Task: {first_run}")
    
    second_run = orchestration_manager.add_new_run_id(p_trigger_source="Manual_CLI", p_triggered_by="Admin_User")
    print(f"Created Second Execution Matrix Task (Verify Sequence Suffix): {second_run}")
    
    print("\n--- 2. Testing Active Status Target Filter Identification ---")
    active_id = orchestration_manager.get_current_active_run_id()
    print(f"Identified Active Task Stream Pointer: {active_id}")
    
    print("\n--- 3. Testing Intermediate Inline Payload Field Updates ---")
    orchestration_manager.update_run_id(
        p_run_id=first_run,
        p_total_datasets=14,
        p_total_models=4,
        p_overall_status="Processing Dimension Intersect Validation Gates"
    )
    print(f"Applied payload update variables to task trace reference: {first_run}")
    
    print("\n--- 4. Testing Completion Processing Protocol ---")
    orchestration_manager.complete_run_id(
        p_run_id=first_run,
        p_overall_status="Passed Verification Schema Checks"
    )
    print(f"Successfully finalized pipeline runtime for execution task reference: {first_run}")
