-- 1. Create our unified core metadata and security rules schema
CREATE SCHEMA IF NOT EXISTS adb_governance_control.core_meta_rules;

-- 2. Deploy the Account ID masking rule into our new generic schema
CREATE OR REPLACE FUNCTION adb_governance_control.core_meta_rules.account_id_mask(account_id STRING)
RETURN CASE 
  WHEN is_account_group_member('banking_admin') THEN account_id
  ELSE CONCAT('XXXX-XXXX-XXXX-', RIGHT(account_id, 4))
END;

-- 3. Deploy the Financial Amount masking rule into our new generic schema
CREATE OR REPLACE FUNCTION adb_governance_control.core_meta_rules.financial_amount_mask(amount DOUBLE)
RETURN CASE 
  WHEN is_account_group_member('risk_auditors') THEN amount
  WHEN amount > 100000 THEN NULL
  ELSE amount
END;

-- Apply masks from our new core_meta_rules schema

ALTER TABLE adb_governance_control.dev_banking_silver.transactions
ALTER COLUMN account_id SET MASK adb_governance_control.core_meta_rules.account_id_mask;

ALTER TABLE adb_governance_control.dev_banking_silver.transactions;
ALTER COLUMN amount SET MASK adb_governance_control.core_meta_rules.financial_amount_mask;\

-- 1. Transfer ownership of the Bronze table to your user account
ALTER TABLE adb_governance_control.dev_banking_bronze.transactions 
SET OWNER TO `<your_user_account_id>`;  -- Replace <your_user_account_id> with your actual user account ID

-- 2. Transfer ownership of the Silver table to your user account
ALTER TABLE adb_governance_control.dev_banking_silver.transactions 
SET OWNER TO `<your_user_account_id>`;  -- Replace <your_user_account_id> with your actual user account ID


-- 1. Grant usage on the master catalog container
GRANT USE CATALOG ON CATALOG adb_governance_control TO `<your_user_account_id>`;  -- Replace <your_user_account_id> with your actual user account ID

-- 2. Grant usage on the Silver and Bronze schemas
GRANT USE SCHEMA ON SCHEMA adb_governance_control.dev_banking_silver TO `<your_user_account_id>`;
GRANT USE SCHEMA ON SCHEMA adb_governance_control.dev_banking_bronze TO `<your_user_account_id>`;

-- 3. Grant usage on your new core rules schema just to be safe
GRANT USE SCHEMA ON SCHEMA adb_governance_control.core_meta_rules TO `<your_user_account_id>`;


-- Take ownership of the tables
ALTER TABLE adb_governance_control.dev_banking_silver.transactions SET OWNER TO `<your_user_account_id>`;
ALTER TABLE adb_governance_control.dev_banking_bronze.transactions SET OWNER TO `<your_user_account_id>`;

-- Bind your masking functions from core_meta_rules
ALTER TABLE adb_governance_control.dev_banking_silver.transactions 
ALTER COLUMN account_id SET MASK adb_governance_control.core_meta_rules.account_id_mask;

ALTER TABLE adb_governance_control.dev_banking_silver.transactions 
ALTER COLUMN amount SET MASK adb_governance_control.core_meta_rules.financial_amount_mask;



SELECT *
FROM adb_governance_control.dev_banking_silver.transactions;
-- 1. Create our unified core metadata and security rules schema
CREATE SCHEMA IF NOT EXISTS adb_governance_control.core_meta_rules;

-- 2. Deploy the Account


-- 1. Insert an extreme high-value transaction row to trip the rule logic
INSERT INTO adb_governance_control.dev_banking_silver.transactions (
  account_id, 
  amount, 
  status, 
  transaction_id, 
  transaction_type, 
  transaction_timestamp
) VALUES (
  '9999888877776666', 
  250000.00,  -- This explicitly breaks our $100,000 policy barrier!
  'Pending', 
  'TXN_TEST_9999', 
  'Wire Transfer', 
  CURRENT_TIMESTAMP()
);

-- 2. Query the data layer to observe your rule enforcement
SELECT account_id, amount, status 
FROM adb_governance_control.dev_banking_silver.transactions
WHERE transaction_id = 'TXN_TEST_9999';


CREATE OR REPLACE FUNCTION adb_governance_control.core_meta_rules.transactions_mask()
RETURN
  IS_ACCOUNT_GROUP_MEMBER('risk_auditors')
;

ALTER TABLE adb_governance_control.dev_banking_silver.transactions 
SET ROW FILTER adb_governance_control.core_meta_rules.transactions_mask;

SELECT *
FROM adb_governance_control.dev_banking_silver.transactions


-- Create a security mapping table inside your core_meta_rules schema
CREATE TABLE IF NOT EXISTS adb_governance_control.core_meta_rules.security_localization_matrix (
  entitled_group STRING,
  allowed_status STRING
);

-- Populate the rules mapping
INSERT INTO adb_governance_control.core_meta_rules.security_localization_matrix 
VALUES 
  ('risk_auditors', 'Failed'),
  ('risk_auditors', 'Pending'),
  ('risk_auditors', 'Completed'),
  ('banking_analysts', 'Completed'); -- Standard analysts can only see Completed items


CREATE OR REPLACE FUNCTION adb_governance_control.core_meta_rules.transactions_dynamic_filter(status STRING)
RETURN EXISTS (
  SELECT 1 
  FROM adb_governance_control.core_meta_rules.security_localization_matrix
  WHERE is_account_group_member(entitled_group) 
    AND allowed_status = status
);


-- Remove the old filter
ALTER TABLE adb_governance_control.dev_banking_silver.transactions DROP ROW FILTER;

-- Bind the new dynamic status filter
ALTER TABLE adb_governance_control.dev_banking_silver.transactions 
SET ROW FILTER adb_governance_control.core_meta_rules.transactions_dynamic_filter ON (status);


SELECT 
  source_table_catalog,
  source_table_schema,
  source_table_name,
  target_table_name,
  event_time
FROM system.access.table_lineage
WHERE target_table_catalog = 'adb_governance_control'
ORDER BY event_time DESC;

