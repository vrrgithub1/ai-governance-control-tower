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

    %% Layer 1: Ingestion & In-Flight
    subgraph L1 ["1. Ingestion & In-Flight Isolation Layer"]
        direction TB
        RawData["Raw Landing Zone<br><i>(Blob / ADLS Gen2)</i>"]
        GE_Gate["Great Expectations Validation<br><i>(Data Quality Gate)</i>"]
        Quarantine["Quarantine Storage<br><i>(Non-compliant payloads)</i>"]
        
        RawData --> GE_Gate
        GE_Gate -- "Fails Validation" --> Quarantine
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

    %% Cross-Layer Flows
    GE_Gate -- "Passes Validation" --> Medallion
    Medallion --> Evidently
    Medallion --> SHAP
    Medallion --> SysSchema

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

