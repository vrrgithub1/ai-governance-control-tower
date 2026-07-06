import os
import sys
import streamlit as st
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database_manager import DatabaseManager
from config import Settings

st.set_page_config(page_title="AIGCT - Control Tower", page_icon="🛡️", layout="wide")
st.title("🛡️ AI Governance Control Tower (AIGCT)")
st.markdown("---")

db = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=True)

def load_metadata(query: str, params: list = None) -> pd.DataFrame:
    with db.connection() as conn:
        return conn.execute(query, params if params else []).df()

# ---------------------------------------------------------------------------
# CORE SYSTEM SUMMARY METRICS
# ---------------------------------------------------------------------------
try:
    # 1. Total runs from the master execution log
    total_runs = load_metadata("SELECT COUNT(*) FROM aigct_core.governance_execution;").iloc[0, 0]
    
    # 2. Active assets directly matching your data asset repository status field
    active_assets = load_metadata("SELECT COUNT(*) FROM aigct_core.data_asset_inventory WHERE status = 'Active';").iloc[0, 0]
    
    # 3. Active production models monitored
    active_models = load_metadata("SELECT COUNT(*) FROM aigct_core.model_inventory WHERE status = 'Production';").iloc[0, 0]
    
    # 4. Active Risk Flags aligned to your exact column constraint (status='Open')
    open_risks = load_metadata("SELECT COUNT(*) FROM aigct_core.risk_register WHERE status = 'Open';").iloc[0, 0]
    
except Exception as e:
    # Diagnostic print behind the scenes to capture schema issues during testing
    print(f"Summary block tracking exception: {str(e)}")
    total_runs, active_assets, active_models, open_risks = 0, 0, 0, 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orchestration Runs", int(total_runs))
col2.metric("Active Assets Tracked", int(active_assets))
col3.metric("Active Models Monitored", int(active_models))
col4.metric("Active Risk Flags", int(open_risks), delta="-Issues" if open_risks==0 else f"+{open_risks}", delta_color="inverse")

# ---------------------------------------------------------------------------
# RESTRUCTURED TAB HIERARCHY
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Governance", 
    "📈 Execution", 
    "📂 Assets", 
    "🎯 Quality", 
    "🤖 Models", 
    "📋 Audit"
])

# ---- TAB 1: EXECUTIVE GOVERNANCE ----
with tab1:
    st.header("Executive Oversight Dashboard")
    st.markdown("Cross-domain platform health indexes and compliance tracking.")
    
    # Calculate a simple operational health score
    if total_runs > 0:
        avg_dq_score = load_metadata("SELECT AVG(quality_score) FROM aigct_core.data_quality_results;").iloc[0,0]
        avg_dq_score = round(avg_dq_score, 2) if pd.notnull(avg_dq_score) else 100.0
    else:
        avg_dq_score = 100.0
        
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 📈 Data Quality Compliance Index: `{avg_dq_score}%`")
        st.progress(int(avg_dq_score) if pd.notnull(avg_dq_score) else 100)
    with c2:
        st.markdown("### 🎛️ Governance Operational Status")
        if open_risks > 0:
            st.warning(f"⚠️ Action Required: {open_risks} active mitigation paths open.")
        else:
            st.success("🟢 Platform Stable: All assets and models matching compliance targets.")

    st.markdown("---")
    st.subheader("🚨 Active Risk & Mitigation Ledger")
    
    # Updated to match your specific constraints and table schema
    risk_df = load_metadata("""
        SELECT risk_id, risk_description, category, severity, status, owner, created_date, risk_owner_group
        FROM aigct_core.risk_register
        ORDER BY created_date DESC;
    """)
    if risk_df.empty:
        st.info("No active compliance risks flagged across the network.")
    else:
        st.dataframe(risk_df, use_container_width=True, hide_index=True)

# ---- TAB 2: EXECUTION ----
with tab2:
    st.header("Master Batch Ingestion Windows")
    runs_df = load_metadata("SELECT run_id, start_time, end_time, status, overall_status, trigger_source FROM aigct_core.governance_execution ORDER BY start_time DESC;")
    st.dataframe(runs_df, use_container_width=True, hide_index=True)
    if not runs_df.empty:
        st.markdown("---")
        selected_run = st.selectbox("Select Run ID to map process steps:", runs_df["run_id"])
        process_df = load_metadata("SELECT process_id, process_name, layer_name, status, records_read, records_passed, records_failed, run_time_seconds FROM aigct_core.governance_execution_process WHERE run_id = ? ORDER BY start_time ASC;", [selected_run])
        st.dataframe(process_df, use_container_width=True, hide_index=True)

# ---- TAB 3: ASSETS ----
with tab3:
    st.header("Global Corporate Data Asset Repository")
    st.dataframe(load_metadata("SELECT dataset_id, dataset_name, data_domain, source_system, classification, status FROM aigct_core.data_asset_inventory WHERE dataset_id != 'SYSTEM';"), use_container_width=True, hide_index=True)

# ---- TAB 4: QUALITY ----
with tab4:
    st.header("Granular Data Quality Evaluations Matrix")
    st.dataframe(load_metadata("SELECT run_id, dataset_id, check_name, check_type, check_status, expected_value, actual_value, quality_score FROM aigct_core.data_quality_results ORDER BY run_date DESC;"), use_container_width=True, hide_index=True)

# ---- TAB 5: MODELS ----
with tab5:
    st.header("Corporate AI Model Inventory Matrix")
    models_df = load_metadata("SELECT model_id, model_name, model_type, model_criticality, risk_tier, status, version, last_validation_date FROM aigct_core.model_inventory;")
    st.dataframe(models_df, use_container_width=True, hide_index=True)
    if not models_df.empty:
        st.markdown("---")
        selected_model = st.selectbox("Select Model ID to view history:", models_df["model_id"])
        st.dataframe(load_metadata("SELECT validation_id, run_id, validation_name, validator_name, validation_result, recommendation FROM aigct_core.model_validation WHERE model_id = ? ORDER BY created_date DESC;", [selected_model]), use_container_width=True, hide_index=True)

# ---- TAB 6: AUDIT ----
with tab6:
    st.header("Chronological Compliance History Log")
    st.dataframe(load_metadata("SELECT event_id, run_id, event_timestamp, event_type, entity_type, entity_id, event_description FROM aigct_core.audit_event ORDER BY event_timestamp DESC;"), use_container_width=True, hide_index=True)
