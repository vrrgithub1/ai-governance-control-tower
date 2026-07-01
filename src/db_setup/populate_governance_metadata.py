import duckdb
from src.database import DatabaseManager 

def populate_governance_data(db_manager: DatabaseManager):
    
    # Combined production-grade seed scripts
    insert_queries = [
        # 1. Model Inventory Seed
        """
        INSERT OR REPLACE INTO main.model_inventory (
            Model_ID, Model_Name, Model_Type, Model_Criticality, Business_Function, 
            Business_Owner, Model_Owner, Risk_Tier, Regulatory_Impact, Data_Sensitivity, 
            Status, Version, Approval_Status, Last_Validation_Date, Next_Review_Date, 
            Explainability_Required, Human_Oversight_Required
        )
        VALUES 
            ('M001', 'Retail Credit Score Model', 'Classification', 'High', 'Credit Risk', 'Sarah Jenkins (Head of Retail Lending)', 'David Chen (Lead Data Scientist)', 'High', 'SR11-7, Basel III', 'Confidential', 'Production', '2.4.1', 'Approved', '2026-01-15', '2027-01-15', True, True),
            ('M002', 'AML Transaction Monitoring', 'Classification', 'Mission Critical', 'AML', 'Marcus Vance (Chief Compliance Officer)', 'Elena Rostova (AML Engineering Lead)', 'High', 'BSA/AML, FinCEN Directives', 'Confidential', 'Production', '4.1.0', 'Approved', '2025-11-10', '2026-11-10', True, True),
            ('M003', 'Trade Surveillance Model', 'NLP', 'High', 'Market Risk', 'Robert Zhang (Head of Market Surveillance)', 'Amit Patel (Quantitative Developer)', 'Medium', 'MiFID II, MAR', 'Confidential', 'Testing', '1.0.0-RC2', 'Pending', NULL, '2026-09-01', True, False),
            ('M004', 'Liquidity Forecast Model', 'Regression', 'Mission Critical', 'Market Risk', 'Amanda Ross (Treasurer)', 'Simon de Wit (Risk Architecture Lead)', 'High', 'SR11-7, Regulation WW', 'Internal', 'Development', '0.8.5', 'Pending', NULL, '2026-12-31', False, True);
        """,
        
        # 2. Data Asset Inventory Seed
        """
        INSERT OR REPLACE INTO main.data_asset_inventory (
            Dataset_ID, Dataset_Name, Domain, Source_System, Data_Owner, 
            Data_Steward, Classification, Contains_PII, Contains_Financial_Data, 
            Critical_Data_Element, Retention_Period, Quality_SLA, Refresh_Frequency, 
            Lineage_Available, Status, Data_Quality_Score
        )
        VALUES 
            ('D001', 'Customer Master', 'Customer', 'Salesforce CRM', 'Sarah Jenkins (Head of Retail Lending)', 'Alice Wong (Data Governance Analyst)', 'Confidential', True, False, True, 7, 99.90, 'Daily', True, 'Active', 99.42),
            ('D002', 'KYC Repository', 'Customer', 'Pega KYC Portal', 'Marcus Vance (Chief Compliance Officer)', 'Brian Miller (Compliance Steward)', 'Confidential', True, False, True, 10, 99.50, 'Real-Time', True, 'Active', 98.15),
            ('D003', 'Trade Transactions', 'Trade', 'Murex Trading Engine', 'Robert Zhang (Head of Market Surveillance)', 'David K. (Core Infrastructure Lead)', 'Confidential', False, True, True, 5, 99.99, 'Real-Time', True, 'Active', 99.97),
            ('D004', 'General Ledger', 'Risk', 'SAP ERP Financials', 'Amanda Ross (Treasurer)', 'Clara Diaz (Financial Systems Admin)', 'Internal', False, True, True, 15, 100.00, 'Daily', True, 'Active', 100.00),
            ('D005', 'Market Risk Positions', 'Risk', 'Bloomberg Terminal API', 'Simon de Wit (Risk Architecture Lead)', 'Evan Wright (Quantitative Analyst)', 'Internal', False, True, False, 3, 99.00, 'Real-Time', False, 'Active', 97.60);
        """,
        
        # 3. Governance Policies Seed
        """
        INSERT OR REPLACE INTO main.governance_policy (
            Policy_ID, Policy_Name, Version, Owner, Review_Date, Policy_Status, Approved_By
        )
        VALUES 
            ('P001', 'AI Governance Policy', '1.0.0', 'Enterprise Governance Team', '2026-12-31', 'Approved', 'Marcus Vance (Chief Compliance Officer)'),
            ('P002', 'Model Validation Standard', '2.1.0', 'Model Risk Management (MRM)', '2026-10-15', 'Approved', 'Amanda Ross (Treasurer)'),
            ('P003', 'Data Retention Policy', '3.0.2', 'Data Governance Committee', '2027-04-01', 'Approved', 'Sarah Jenkins (Head of Retail Lending)'),
            ('P004', 'Explainability Policy', '0.4.5', 'AI Ethics & Responsible AI Council', '2026-09-30', 'Draft', NULL);
        """,

        # 4. Risk Register Seed
        """
        INSERT OR REPLACE INTO main.risk_register (Risk_ID, Risk_Description, Category, Severity, Status, Owner)
        VALUES 
            ('R001', 'Data Drift', 'Operational', 'High', 'Open', 'John Doe'),
            ('R002', 'Bias Detection Failure', 'Compliance', 'High', 'Open', 'Jane Smith'),
            ('R003', 'Missing Explainability', 'Regulatory', 'Medium', 'Closed', 'John Doe');
        """

        # 5. Quality Rule Definition Seed
        """
        INSERT OR REPLACE INTO main.quality_rule_definition 
            (Rule_ID, Rule_Name, Dataset_ID, Column_Name, Rule_Type, Rule_Expression, Severity, Enabled_Flag)
        VALUES 
            ('DQ001', 'Customer_ID Not Null', 'D001', 'Customer_ID', 'NOT_NULL', 
            'Customer_ID IS NULL OR Customer_ID = '''' ', 'High', True),
            ('DQ002', 'Customer_ID Unique', 'D001', 'Customer_ID', 'UNIQUE', 
            'Customer_ID IN (SELECT Customer_ID FROM bronze.customer_master GROUP BY Customer_ID HAVING COUNT(*) > 1)', 'High', True),
            ('DQ003', 'KYC_Status Not Null', 'D001', 'KYC_Status', 'NOT_NULL', 
            'KYC_Status IS NULL OR KYC_Status = '''' ', 'High', True),
            ('DQ004', 'Valid Country Code', 'D001', 'Country_Code', 'REFERENCE', 
            'Country_Code NOT IN (SELECT Country_Code FROM gold.country_ref)', 'High', True),
            ('DQ005', 'Valid Risk Rating Profile', 'D001', 'Risk_Rating', 'ENUM', 
            'Risk_Rating NOT IN (''Low'', ''Medium'', ''High'')', 'Medium', True),
            ('DQ101', 'Trade_ID Not Null', 'D003', 'Trade_ID', 'MANDATORY', 
            'Trade_ID IS NULL OR Trade_ID = '''' ', 'High', True),
            ('DQ102', 'Trade_ID Unique', 'D003', 'Trade_ID', 'PRIMARY_KEY', 
            'Trade_ID IN (SELECT Trade_ID FROM bronze.trade_transactions GROUP BY Trade_ID HAVING COUNT(*) > 1)', 'High', True),
            ('DQ103', 'Trade_Date Not Null', 'D003', 'Trade_Date', 'MANDATORY', 
            'Trade_Date IS NULL OR Trade_Date = '''' ', 'High', True),
            ('DQ104', 'Customer_ID Not Null', 'D003', 'Customer_ID', 'MANDATORY', 
            'Customer_ID IS NULL OR Customer_ID = '''' ', 'High', True),
            ('DQ105', 'Positive Trade Amount', 'D003', 'Trade_Amount', 'VALUE_CHECK', 
            'TRY_CAST(Trade_Amount AS DOUBLE) IS NULL OR TRY_CAST(Trade_Amount AS DOUBLE) <= 0', 'High', True),
            ('DQ106', 'Valid Fiat Currency ISO', 'D003', 'Currency', 'ENUM_CHECK', 
            'Currency NOT IN (''USD'', ''EUR'', ''GBP'', ''CAD'', ''JPY'', ''SGD'', ''HKD'')', 'Medium', True),
            ('DQ_GOV_001', 'Valid Ingestion Trigger Source', 'ORCHESTRATION_MASTER', 'Trigger_Source', 'ENUM_CHECK', 
            'Trigger_Source NOT IN (''SCHEDULER'', ''EVENT_DRIVEN'', ''MANUAL_CLI'', ''WEB_UI'', ''CI_CD_PIPELINE'', ''API_WEBHOOK'')', 'High', True);
        """
    ]

    with db_manager.connection() as conn:
        try:
            # Open transaction block
            conn.execute("BEGIN TRANSACTION;")
            
            # Sequentially execute insertion batches
            for index, query in enumerate(insert_queries, 1):
                conn.execute(query)
                print(f"✔ Batch #{index} seed statements executed successfully.")
                
            # Commit changes to disk
            conn.commit()
            print("\n🎉 Success! Database tables hydrated with updated sample data profiles.")
            
            # Verify and display current state counts
            print("\n--- Summary Verification ---")
            for table in ["model_inventory", "data_asset_inventory", "governance_policy", "risk_register", "quality_rule_definition"]:
                count = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                print(f"Table: {table.ljust(22)} | Total Rows: {count}")
                
        except Exception as e:
            # Safe transaction rollback protocol
            try:
                conn.execute("ROLLBACK;")
                print("\n❌ Insert failed! Safe rollback triggered to protect relational states.")
            except duckdb.TransactionException:
                pass
            print(f"Details: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    # Standard baseline invocation initialization 
    from config import Settings
    manager = DatabaseManager(db_path=Settings.DATABASE_PATH, read_only=False)

    populate_governance_data(db_manager=manager)
    