# 03. Architecture Overview

## Executive Summary

The **AI Governance Control Tower (AIGCT)** is a modular, event-driven governance and observability architecture built natively on **Azure Databricks** and **Unity Catalog**. 

Rather than relying on external sidecars or gateway proxies that introduce latency and administrative bloat, AIGCT operates directly within the Lakehouse execution layer. It leverages Unity Catalog's unified metastore, system schemas, dynamic data masking routines, and delta telemetry to enforce continuous, zero-trust governance across data assets, feature stores, and MLOps/LLM workloads.

---

## High-Level System Topology

The AIGCT ecosystem is partitioned into four primary functional layers: **Ingestion & In-Flight Control**, **Unity Catalog Storage & Policy Engine**, **Continuous Governance & Observability Engine**, and **Telemetry & Consumption Layer**.

```mermaid
graph TD
    %% Main Layout Direction
    direction TB

    %% Layer 1: Ingestion
    subgraph L1 ["1. Ingestion & In-Flight Isolation Layer"]
        direction TB
        RawData["Raw Landing Zone<br><i>(Blob / ADLS Gen2)</i>"]
        GE_Gate["Great Expectations Validation<br><i>(Data Quality Gate)</i>"]
        Quarantine["Quarantine Storage<br><i>(Non-compliant payloads)</i>"]
        
        RawData --> GE_Gate
        GE_Gate -- "Fails Assertions" --> Quarantine
    end

    %% Layer 2: Unity Catalog Core
    subgraph L2 ["2. Unity Catalog Core & Security Engine"]
        direction TB
        Medallion["Medallion Architecture<br><i>(Bronze ➔ Silver ➔ Gold)</i>"]
        RLS_Masking["Dynamic Access Control<br><i>(Row-Level Filtering & Column Masking)</i>"]
        EntraID["Microsoft Entra ID<br><i>(RBAC & Attribute-Based Access)</i>"]
        
        EntraID <--> RLS_Masking
        Medallion <--> RLS_Masking
    end

    %% Layer 3: Observability Engine
    subgraph L3 ["3. Continuous Governance & Observability Engine"]
        direction TB
        Evidently["Evidently AI<br><i>(Feature & Statistical Drift)</i>"]
        SHAP["SHAP & MLflow<br><i>(Model Explainability & Lineage)</i>"]
        Alerts["Automated Remediation<br><i>(Retraining / Isolation Trigger)</i>"]
        
        Evidently --> Alerts
        SHAP --> Alerts
    end

    %% Layer 4: Telemetry & Consumption
    subgraph L4 ["4. Telemetry & Consumption Layer"]
        direction TB
        SysSchema["Unity Catalog System Schemas<br><i>(system.access.audit / table_lineage)</i>"]
        Dashboards["Lakeview Dashboards-as-Code<br><i>(.lvdash.json)</i>"]
        CI_CD["GitHub Actions GitOps Pipeline"]

        SysSchema --> Dashboards
        CI_CD --> Dashboards
    end

    %% Clear Inter-Layer Dependencies (Layer-to-Layer Flows)
    L1 -- "Clean Data Payload" --> L2
    L2 -- "Feature & Inference Data" --> L3
    L2 -- "Audit Logs & Lineage Telemetry" --> L4

    %% Styling
    classDef l1Style fill:#1e293b,stroke:#3b82f6,color:#f8fafc;
    classDef l2Style fill:#064e3b,stroke:#10b981,color:#f8fafc;
    classDef l3Style fill:#581c87,stroke:#a855f7,color:#f8fafc;
    classDef l4Style fill:#7c2d12,stroke:#f97316,color:#f8fafc;

    class RawData,GE_Gate,Quarantine l1Style;
    class Medallion,RLS_Masking,EntraID l2Style;
    class Evidently,SHAP,Alerts l3Style;
    class SysSchema,Dashboards,CI_CD l4Style;
```

## Core Architectural Layers

### 1. Ingestion & Active Isolation Layer

- **Great Expectations In-Flight Quality Gates:** Raw data entering the Lakehouse passes through automated expectation suites. Any payload failing schemas or business assertions is automatically diverted to a isolated Quarantine Lakehouse for review, preventing downstream model contamination.

#### 2. Unity Catalog Security Engine (Active Protection)

- **Identity-Centric Entitlements:** Integrated directly with Microsoft Entra ID service principals and user groups.
- **Dynamic Row-Level Filtering (RLS) & Column Masking:** Policy functions are applied at the metastore level. Users querying `⁠Gold`⁠ layer tables dynamically receive masked PII/SPI attributes based on their session context without creating duplicate physical datasets.

### 3. Continuous Governance & Observability Engine

- **Statistical Feature & Model Drift:** Evidently AI evaluates production feature distributions against baseline training sets to detect covariance shift and feature degradation.
- **Explainability (SHAP) & MLflow Registry:** Every production prediction is tracked alongside model lineage and SHAP feature importance values in MLflow.

### 4. Telemetry & GitOps CI/CD Layer

- **Native Audit Logging:** Extracts raw access records and table-level lineage directly from Unity Catalog metastore system schemas (⁠`system.access.audit`⁠, `⁠system.access.table_lineage`⁠).
- **Dashboards-as-Code:** Telemetry is exposed via declarative Lakeview Dashboards (⁠`.lvdash.json`⁠), fully deployed and versioned using GitHub Actions.


## Data & Telemetry Lifecycle Flow

The flow below illustrates how raw data transitions into audited insights while enforcing all 4 AIGCT pillars:

```mermaid
sequenceDiagram
    autonumber
    actor User/Model as Entra ID User / Pipeline
    participant Ingest as Data Ingestion Gate
    participant UC as Unity Catalog Metastore
    participant SysLog as System Audit Schemas
    participant Obs as Evidently & SHAP Engine
    participant Dash as Lakeview Dashboard

    User/Model->>Ingest: Push Data Payload
    Ingest->>Ingest: Validate via Great Expectations
    alt Quality Gate Fails
        Ingest-->>User/Model: Route to Quarantine & Alert
    else Quality Gate Passes
        Ingest->>UC: Write to Delta Lake (Silver/Gold)
    end

    User/Model->>UC: Execute SQL / Model Inference
    UC->>UC: Apply Dynamic Row Filters & Column Masks
    UC->>SysLog: Emit Audit Telemetry (system.access)
    
    UC->>Obs: Run Scheduled Drift & Explainability Check
    Obs-->>User/Model: Trigger Alert if Drift Threshold Exceeded
    
    SysLog->>Dash: Refresh System Audit & Compliance Telemetry
```

## Technical Stack Reference

| Component | Technology/Tool | Architectural Purpose |
| :--- | :--- | :--- |
| Compute / Lakehouse | Azure Databricks (Photon Runtime) | Scalable engine for ETL, streaming, and model inference. |
| Governance Engine | Databricks Unity Catalog | Metastore-level access control, lineage, and audit schemas. |
| Identity Management | Microsoft Entra ID (Azure AD) | Unified SSO, group-based access (RBAC/ABAC), and service principals. |
| Data Quality Gate | Great Expectations | Active pre-ingestion validation and quarantine routing. |
| Observability / Drift | Evidently AI + SHAP | Statistical drift tracking, data distribution shifts, and ML explainability. |
| Experiment Tracking | MLflow | Model versioning, lineage tracking, and artifact registry. |
| CI/CD & Automation | GitHub Actions + Databricks CLI | GitOps deployment of dashboards (`.lvdash.json`) and notebooks. |

