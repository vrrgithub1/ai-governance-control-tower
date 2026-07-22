# 04. Active Protection Engine

## Executive Summary

The **Active Protection Engine** is the primary inline defensive mechanism of the **AI Governance Control Tower (AIGCT)**. Built natively on **Databricks Unity Catalog**, it eliminates traditional governance anti-patterns—such as maintaining duplicate "sanitized" datasets or running external sidecar proxies that increase latency.

By leveraging **Dynamic Row-Level Filtering (RLS)** and **Column Masking**, AIGCT enforces fine-grained access control at the metastore execution layer. Security policy decisions are evaluated dynamically per-query based on the caller's **Microsoft Entra ID** identity and group membership, ensuring true Zero-Trust security across SQL, Python, and MLOps workloads.

---

## Architectural Principles

1. **Single Source of Truth (SSOT):** Storage of duplicate datasets (e.g., a masked copy vs. an unmasked copy) is prohibited. Data is stored once in Gold/Silver Delta Lake tables and dynamically filtered upon reading.
2. **Zero-Trust Policy Enforcement:** Access is denied by default. Entitlements are evaluated at the engine level regardless of whether access originates from an interactive SQL query, a Databricks notebook, or an automated ML pipeline.
3. **Decoupled Governance Logic:** Security policy SQL functions (`UDFs`) are maintained independently of underlying physical table definitions, allowing global policy updates without schema migrations.

---

## Architecture Topology

```mermaid
graph TD
    subgraph UC ["Unity Catalog Metastore (adb_governance_control)"]
        direction TB
        
        Entra["Microsoft Entra ID<br><i>(User / Service Principal Session Context)</i>"]
        
        subgraph PolicyLayer ["Policy & Function Layer"]
            RLS_UDF["Row-Level Filter UDF<br><code>udf_filter_by_region()</code>"]
            Mask_UDF["Column Masking UDF<br><code>udf_mask_pii_email()</code>"]
        end
        
        subgraph StorageLayer ["Gold Layer Delta Tables"]
            GoldTable["Customer Feature Store<br><code>gold.customer_360</code>"]
        end
        
        Entra --> PolicyLayer
        PolicyLayer --> GoldTable
    end

    User_Admin["Compliance Admin / ML Training SP"] -- "Full Unmasked Access" --> GoldTable
    User_Analyst["Standard Analyst / External Query"] -- "Filtered & Masked View" --> GoldTable

    classDef ucStyle fill:#0f172a,stroke:#3b82f6,color:#f8fafc;
    classDef policyStyle fill:#581c87,stroke:#a855f7,color:#f8fafc;
    classDef dataStyle fill:#064e3b,stroke:#10b981,color:#f8fafc;

    class Entra ucStyle;
    class RLS_UDF,Mask_UDF policyStyle;
    class GoldTable dataStyle;
```

## Technical Deep-Dive: Policy Implementation

### 1. Dynamic Column Masking (PII Protection)
Column masking functions dynamically transform or redact specific cell values based on the execution context of ⁠IS_ACCOUNT_GROUP_MEMBER()⁠.

#### SQL Definition: Email Redaction UDF

```SQL
CREATE OR REPLACE FUNCTION adb_governance_control.policies.mask_email(
    email STRING
)
RETURNS STRING
RETURN IF(
    IS_ACCOUNT_GROUP_MEMBER('pii_data_access_group') OR IS_ACCOUNT_GROUP_MEMBER('account admins'),
    email,
    REGEXP_REPLACE(email, '(^.).*(@.*$)', '$1***$2') -- Transforms 'john.doe@example.com' -> 'j***@example.com'
);
```

#### Binding Masking Function to Table Column

```SQL
ALTER TABLE adb_governance_control.gold.customer_features 
ALTER COLUMN email SET MASK adb_governance_control.policies.mask_email;
```

### 2. Dynamic Row-Level Security (Data Isolation)
Row filters evaluate condition predicates against every row returned by a query, restricting visibility based on geographical boundaries, organizational units, or business divisions.

#### SQL Definition: Region Boundary Filter UDF

```SQL
CREATE OR REPLACE FUNCTION adb_governance_control.policies.filter_by_region(
    region_code STRING
)
RETURNS BOOLEAN
RETURN 
    IS_ACCOUNT_GROUP_MEMBER('global_compliance_admins') 
    OR (IS_ACCOUNT_GROUP_MEMBER('eu_data_analysts') AND region_code = 'EU')
    OR (IS_ACCOUNT_GROUP_MEMBER('us_data_analysts') AND region_code = 'US');
```

#### Binding Filter Function to Table

```SQL
ALTER TABLE adb_governance_control.gold.customer_features 
SET ROW FILTER adb_governance_control.policies.filter_by_region ON (region_code);
```

## Query Execution Lifecycle
When a query is submitted to the Spark/Photon engine, Unity Catalog intercepts the logical plan before execution:

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Entra ID Identity (User / Service Principal)
    participant Engine as Spark / Photon Engine
    participant UC as Unity Catalog Metastore
    participant Delta as Delta Storage (ADLS Gen2)

    Caller->>Engine: Submit SQL Query (SELECT * FROM gold.customer_features)
    Engine->>UC: Request Execution Plan & Entitlements
    
    rect rgb(30, 41, 59)
        note over UC: Policy Evaluation Phase
        UC->>UC: Evaluate IS_ACCOUNT_GROUP_MEMBER()
        UC->>UC: Inject Dynamic Masking UDFs into Plan
        UC->>UC: Inject Row-Filter Predicates into Plan
    end

    UC-->>Engine: Optimized Plan with Applied Security Rules
    Engine->>Delta: Read Delta Parquet Footprint
    Delta-->>Engine: Raw Data Payload
    Engine->>Engine: Apply Inline Row Filters & Masking Transforms
    Engine-->>Caller: Filtered & Masked Result Set
```




