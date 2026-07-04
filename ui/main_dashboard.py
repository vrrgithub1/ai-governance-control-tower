import os
import sys
import streamlit as st
import pandas as pd

# 💡 FIX: Force Python to recognize the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database_manager import DatabaseManager
from config import Settings

# ---------------------------------------------------------------------------
# INITIAL SETUP & CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AIGCT - Core Control Tower",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ AI Governance Control Tower (AIGCT)")
st.subheader("Core Metadata Layer Operational Monitoring Framework")
st.markdown("---")

# Initialize database access
db = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=True)

# ---------------------------------------------------------------------------
# METADATA EXTRACTION UTILITIES
# ---------------------------------------------------------------------------
def load_metadata(query: str, params: list = None) -> pd.DataFrame:
    """Executes search path queries safely and returns standard pandas DataFrames."""
    with db.connection() as conn:
        # PRAGMA is automatically handled by your updated database.py class!
        result = conn.execute(query, params if params else [])
        return result.df()

# ---------------------------------------------------------------------------
# MAIN KPI BANNER TILES
# ---------------------------------------------------------------------------
st.sidebar.header("🎯 System Settings")
st.sidebar.markdown("Navigate through different metadata monitoring registers.")

# Fetch top-level counts for our system tile overview metrics
try:
    exec_summary = load_metadata("""
        SELECT 
            COUNT(run_id) as total_runs,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as success_runs,
            COUNT(CASE WHEN status = 'Failed' THEN 1 END) as crashed_runs
        FROM aigct_core.governance_execution;
    """).iloc[0]

# 💡 NEW: Dynamically count active registered data assets from your inventory catalog
    asset_summary = load_metadata("""
        SELECT COUNT(DISTINCT dataset_id) as active_assets 
        FROM aigct_core.data_asset_inventory 
        WHERE status = 'Active';
    """).iloc[0]
    
except Exception:
    exec_summary = {"total_runs": 0, "success_runs": 0, "crashed_runs": 0}
    asset_summary = {"active_assets": 0}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orchestration Runs", int(exec_summary["total_runs"]))
col2.metric("Successful Batches", int(exec_summary["success_runs"]))
col3.metric("System Pipeline Crashes", int(exec_summary["crashed_runs"]), delta_color="inverse")
col4.metric("Active Assets Tracked", int(asset_summary["active_assets"])) # 💡 Now dynamic!

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CORE VIEWING MONITOR TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Master Ingestion Runs", 
    "📂 Active Data Asset Inventory", 
    "🎯 Data Quality Registers", 
    "🤖 Model Governance Registry",  # 💡 NEW
    "📋 Compliance Audit Logs"
])


# ---- TAB 1: MASTER INGESTION RUNS (ORCHESTRATOR VISIBILITY) ----
with tab1:
    st.header("Master Batch Execution Windows")
    st.markdown("Chronological tracking log for global platform run states.")
    
    runs_df = load_metadata("""
        SELECT run_id, start_time, end_time, status, overall_status, trigger_source, total_processes 
        FROM aigct_core.governance_execution 
        ORDER BY start_time DESC;
    """)
    st.dataframe(runs_df, use_container_width=True, hide_index=True)
    
    if not runs_df.empty:
        st.markdown("---")
        st.subheader("🔍 Deep Drill-Down: Process Step Linear Mapping")
        selected_run = st.selectbox("Select a Run ID to map sub-task states:", runs_df["run_id"])
        
        # Pull process step components dynamically based on your Option 1 design
        process_df = load_metadata("""
            SELECT process_id, process_name, layer_name, status, records_read, records_passed, records_failed, run_time_seconds, parent_process_id
            FROM aigct_core.governance_execution_process
            WHERE run_id = ?
            ORDER BY start_time ASC;
        """, [selected_run])
        
        st.dataframe(process_df, use_container_width=True, hide_index=True)

# ---- TAB 2: ACTIVE DATA ASSET INVENTORY (METADATA CATALOG) ----
with tab2:
    st.header("Global Corporate Data Asset Repository")
    st.markdown("Global reference configuration boundaries for active production tables.")
    
    assets_df = load_metadata("""
        SELECT dataset_id, dataset_name, data_domain, source_system, classification, 
               contains_pii, contains_financial_data, data_retention_period, refresh_frequency, status
        FROM aigct_core.data_asset_inventory
        WHERE dataset_id != 'SYSTEM';
    """)
    st.dataframe(assets_df, use_container_width=True, hide_index=True)

# ---- TAB 3: DATA QUALITY REGISTERS (ANALYTICS TELEMETRY) ----
with tab3:
    st.header("Granular Data Quality Evaluations Matrix")
    st.markdown("Granular tracking scores parsed dynamically from registered validation rules.")
    
    dq_df = load_metadata("""
        SELECT run_id, dataset_id, check_name, check_type, check_status, expected_value, actual_value, quality_score, total_records, failed_records, run_date
        FROM aigct_core.data_quality_results
        ORDER BY run_date DESC;
    """)
    st.dataframe(dq_df, use_container_width=True, hide_index=True)

# ---- 💡 NEW TAB 4: MODEL GOVERNANCE REGISTRY ----
with tab4:
    st.header("Corporate AI Model Inventory Matrix")
    st.markdown("Regulatory compliance risk boundaries for productionized predictive systems.")
    
    models_df = load_metadata("""
        SELECT model_id, model_name, model_type, model_criticality, risk_tier, 
               regulatory_impact, status, version, approval_status, last_validation_date, next_review_date
        FROM aigct_core.model_inventory;
    """)
    st.dataframe(models_df, use_container_width=True, hide_index=True)
    
    if not models_df.empty:
        st.markdown("---")
        st.subheader("🔍 Deep Drill-Down: Independent Validation History Trail")
        selected_model = st.selectbox("Select a Model ID to inspect rigorous evaluation logs:", models_df["model_id"])
        
        val_history_df = load_metadata("""
            SELECT validation_id, run_id, validation_name, validator_name, validation_result, findings_count, recommendation, approval_status, created_date
            FROM aigct_core.model_validation
            WHERE model_id = ?
            ORDER BY created_date DESC;
        """, [selected_model])
        
        st.dataframe(val_history_df, use_container_width=True, hide_index=True)

# ---- TAB 5: COMPLIANCE AUDIT LOGS (REGULATORY TRACE) ----
with tab5:
    st.header("Chronological Compliance History Log")
    st.markdown("Immutable operational markers tracking data mutations, schema variances, and critical pipeline exceptions.")
    
    audit_df = load_metadata("""
        SELECT event_id, run_id, process_id, event_timestamp, event_type, entity_type, entity_id, performed_by, event_description
        FROM aigct_core.audit_event
        ORDER BY event_timestamp DESC;
    """)
    st.dataframe(audit_df, use_container_width=True, hide_index=True)
