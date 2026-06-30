import duckdb

def populate_governance_data():
    db_file = "database/ai_governance_control_tower.db"
    conn = duckdb.connect(db_file)
    
    print(f"Connecting to database '{db_file}' to execute sample insertions...\n")
    
    # Combined production-grade seed scripts
    insert_queries = [
        # 1. Model Inventory Seed
        """
        INSERT OR REPLACE INTO model_inventory (
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
        INSERT OR REPLACE INTO data_asset_inventory (
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
        INSERT OR REPLACE INTO governance_policies (
            Policy_ID, Policy_Name, Version, Owner, Review_Date, Policy_Status, Approved_By
        )
        VALUES 
            ('P001', 'AI Governance Policy', '1.0.0', 'Enterprise Governance Team', '2026-12-31', 'Approved', 'Marcus Vance (Chief Compliance Officer)'),
            ('P002', 'Model Validation Standard', '2.1.0', 'Model Risk Management (MRM)', '2026-10-15', 'Approved', 'Amanda Ross (Treasurer)'),
            ('P003', 'Data Retention Policy', '3.0.2', 'Data Governance Committee', '2027-04-01', 'Approved', 'Sarah Jenkins (Head of Retail Lending)'),
            ('P004', 'Explainability Policy', '0.4.5', 'AI Ethics & Responsible AI Council', '2026-09-30', 'Draft', NULL);
        """
    ]

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
        for table in ["model_inventory", "data_asset_inventory", "governance_policies"]:
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
    populate_governance_data()
    