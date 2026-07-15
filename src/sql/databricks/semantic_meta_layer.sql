CREATE OR REPLACE VIEW adb_governance_control.core_meta_rules.security_monitoring_gold AS
SELECT 
  event_time,
  -- 1. Masking the workspace id value for the slide deck presentation
  '74056****' AS presentation_workspace_id,
  
  -- 2. Dynamically masking real employee email IDs into clean domain placeholders
  CASE 
    WHEN identity_metadata.run_by LIKE 'vrajadur%' THEN 'vrajadur@corporate.com'
    ELSE 'analyst_team@corporate.com'
  END AS presentation_user_email,
  
  -- 3. Masking display names natively
  CASE 
    WHEN identity_metadata.run_by_display_name LIKE 'Venkatasamy%' THEN 'Venkatasamy Rajadurai (SecOps Admin)'
    ELSE 'Standard Business Analyst'
  END AS presentation_user_name,
  
  action_name,
  request_params.table_full_name AS accessed_table,
  response.status_code AS http_status,
  user_agent
FROM system.access.audit
WHERE request_params.table_full_name LIKE '%transactions%'
   OR request_params.table_full_name LIKE '%banking%';
   