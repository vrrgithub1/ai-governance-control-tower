import logging
from src.database_manager import DatabaseManager

logger = logging.getLogger("AIGCT_Seeder")

class ReferenceDataSeeder:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def seed_all_reference_data(self) -> None:
        """Seeds standard banking datasets, DQ validation rules, and baseline models."""
        logger.info("🌱 Beginning reference data registration for core catalog fields...")
        
        self.seed_data_asset_inventory()
        self.seed_quality_rule_definitions()
        self.seed_model_inventory()
        
        logger.info("✅ Reference data seeding completed successfully.")

    def seed_data_asset_inventory(self) -> None:
        """Registers the initial core corporate financial data assets."""
        query = """
            INSERT INTO aigct_core.data_asset_inventory (
                dataset_id, dataset_name, data_domain, source_system, data_owner, 
                data_steward, classification, contains_pii, contains_financial_data, 
                contains_critical_data_element, data_retention_period, quality_sla, 
                refresh_frequency, lineage_available, status, data_quality_score,
                bronze_table, silver_table, gold_table, quarantine_table
            ) VALUES 
            (
                'DS_CUST_MASTER', 'Customer Master Profile', 'Customer', 'SALESFORCE', 
                'Retail Banking Group', 'Data Management Team', 'Confidential', 
                TRUE, FALSE, TRUE, 7, 99.5, 'Daily', TRUE, 'Active', NULL,
                'aigct_bronze.customer_master', 'aigct_silver.customer_master', 
                'aigct_gold.customer_master', 'aigct_quarantine.customer_master'
            ),
            (
                'DS_TRADE_TRANS', 'Trade Transactions Log', 'Trade', 'BLOOMBERG', 
                'Capital Markets Operations', 'Trade Control Group', 'Confidential', 
                FALSE, TRUE, TRUE, 10, 99.9, 'Daily', TRUE, 'Active', NULL,
                'aigct_bronze.trade_transactions', 'aigct_silver.trade_transactions', 
                'aigct_gold.trade_transactions', 'aigct_quarantine.trade_transactions'
            ),
            (
                'DS_CREDIT_FEAT', 'Credit Risk Scoring Features', 'Risk', 'INTERNAL_MODELS', 
                'Risk Analytics Squad', 'Risk Governance Team', 'Internal', 
                FALSE, TRUE, FALSE, 5, 98.0, 'Daily', TRUE, 'Active', NULL,
                'aigct_bronze.credit_features', 'aigct_silver.credit_features', 
                'aigct_gold.credit_features', 'aigct_quarantine.credit_features'
            )
            ON CONFLICT (dataset_id) DO UPDATE SET
                dataset_name = EXCLUDED.dataset_name,
                classification = EXCLUDED.classification,
                status = EXCLUDED.status;
        """
        with self.db.connection() as conn:
            conn.execute(query)
        logger.info("  └─ Registered core banking data assets.")

    def seed_quality_rule_definitions(self) -> None:
        """Maps default compliance execution rules for the ingestion engine to evaluate."""
        query = """
            INSERT INTO aigct_core.quality_rule_definition (
                rule_id, rule_name, dataset_id, column_name, rule_type, 
                rule_expression, severity, enabled_flag, rule_category
            ) VALUES 
            (
                'QR_CUST_ID_NOT_NULL', 'Verify Customer ID Presence', 'DS_CUST_MASTER', 
                'customer_id', 'NOT_NULL', 'customer_id IS NULL', 'High', TRUE, 'Validity'
            ),
            (
                'QR_TRADE_AMT_POSITIVE', 'Validate Positive Trade Value', 'DS_TRADE_TRANS', 
                'trade_amount', 'VALUE_CHECK', 'trade_amount <= 0', 'High', TRUE, 'Conformity'
            ),
            (
                'QR_CRED_SCORE_RANGE', 'Enforce FICO Range Limits', 'DS_CREDIT_FEAT', 
                'credit_score', 'RANGE_CHECK', 'credit_score < 300 OR credit_score > 850', 'Medium', TRUE, 'Validity'
            )
            ON CONFLICT (rule_id) DO UPDATE SET
                rule_expression = EXCLUDED.rule_expression,
                enabled_flag = EXCLUDED.enabled_flag;
        """
        with self.db.connection() as conn:
            conn.execute(query)
        logger.info("  └─ Configured target data quality rule expectations.")

    def seed_model_inventory(self) -> None:
        """Populates the AI model registry matrix."""
        query = """
            INSERT INTO aigct_core.model_inventory (
                model_id, model_name, model_type, model_criticality, business_function, 
                model_owner, risk_tier, regulatory_impact, data_sensitivity, status, 
                version, approval_status, last_validation_date, next_review_date, 
                explainability_required, human_oversight_required, created_date,
                model_framework, training_dataset, deployment_environment, endpoint_url
            ) VALUES 
            (
                'MDL_CREDIT_NET', 'Credit Default Neural Network', 'Classification', 'High', 
                'Retail Lending Division', 'Risk Modeling Squad', 'High', 'SR11-7 / EU AI Act', 
                'Confidential', 'Production', '1.4.0', 'Approved', '2026-05-12', '2027-05-12', 
                TRUE, TRUE, CURRENT_TIMESTAMP, 'PyTorch', 'DS_CREDIT_FEAT', 'AWS_EKS_PROD', 
                'https://api.risk.bank.internal/v1/predict-default'
            ),
            (
                'MDL_TRADE_ANOMALY', 'Capital Markets Fraud Guard', 'Isolation Forest', 'Mission Critical', 
                'Institutional Compliance', 'Global Security Team', 'High', 'SEC Rule 17a-4', 
                'Confidential', 'Production', '2.1.0', 'Approved', '2026-06-01', '2027-06-01', 
                FALSE, TRUE, CURRENT_TIMESTAMP, 'Scikit-Learn', 'DS_TRADE_TRANS', 'AZURE_AKS_PROD', 
                'https://fraud-guard.compliance.bank.internal/v2/evaluate'
            )
            ON CONFLICT (model_id) DO UPDATE SET
                status = EXCLUDED.status,
                version = EXCLUDED.version,
                approval_status = EXCLUDED.approval_status;
        """
        with self.db.connection() as conn:
            conn.execute(query)
        logger.info("  └─ Populated global production AI model registries.")
