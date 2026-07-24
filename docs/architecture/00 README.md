# AI Governance Control Tower (AIGCT) Architecture

Welcome to the **AI Governance Control Tower (AIGCT)** architectural specification suite. This repository houses the end-to-end technical, operational, and compliance designs for governed AI on Azure Databricks.

## System Architecture Blueprint

```text
+--------------------------------------------------------------------------------------+
|                        AI GOVERNANCE CONTROL TOWER (AIGCT)                           |
+--------------------------------------------------------------------------------------+
|  01 Vision & 02 Business Problem                                                     |
|  03 Architecture Overview (SSOT & Unity Catalog Engine)                              |
+--------------------------------------------------------------------------------------+
|  LAYER 1: Active Protection Engine          --> [04 Active Protection Engine.md]     |
|  LAYER 2: Data Quality Ingestion Gate       --> [05 Data Quality Ingestion Gate.md]. |
|  LAYER 3: Observability & ML Monitoring     --> [06 Observability Engine.md]         |
|  LAYER 4: Telemetry & Audit Readiness       --> [07 Telemetry & Audit Engine.md]     |
|  LAYER 5: Dashboards & Continuous Control   --> [09 Databricks Dashboard Arch.md]    |
+--------------------------------------------------------------------------------------+
|  OPERATIONS & COMPLIANCE                                                             |
|  Continuous Governance & CI/CD              --> [08 Continuous Governance Engine.md] |
|  Risk Matrix & Compliance Alignment         --> [10 Risk Matrix Alignment.md]        |
+--------------------------------------------------------------------------------------+
```

## Architecture Document Index

### Core Foundations
* **[01 Vision](./01%20Vision.md):** Executive motivation, strategic imperatives, and high-level outcomes.
* **[02 Business Problem](./02%20Business%20Problem.md):** Core risks, compliance penalties, and technical gaps targeted by AIGCT.
* **[03 Architecture Overview](./03%20Architecture%20Overview.md):** End-to-end multi-layer architectural design, tech stack, and ecosystem integration.

### Core Governance Engines (Layers 1–5)
* **[04 Active Protection Engine](./04%20Active%20Protection%20Engine.md):** Zero-Trust security, dynamic Row-Level Security (RLS), and Column Masking via Unity Catalog.
* **[05 Data Quality Ingestion Gate](./05%20Data%20Quality%20Ingestion%20Gate.md):** Automated circuit breakers and data health validation using Great Expectations.
* **[06 Observability and ML Monitoring Engine](./06%20Observability%20and%20ML%20Monitoring%20Engine.md):** Continuous concept/data drift monitoring and SHAP feature explainability using Evidently AI.
* **[07 Telemetry and Audit Readiness Engine](./07%20Telemetry%20and%20Audit%20Readiness%20Engine.md):** Immutable Delta Lake audit ledgers and unified lineage tracking.
* **[09 Databricks Lakehouse Dashboard Architecture](./09%20Databricks%20Lakehouse%20Dashboard%20Architecture.md):** Dashboards-as-Code (`.lvdash.json`) providing operational health and compliance reporting.

### Operations & Regulatory Alignment
* **[08 Continuous Governance and CI CD Engine](./08%20Continuous%20Governance%20and%20CI%20CD%20Engine.md):** Governance-as-Code pipeline automated via Databricks Asset Bundles (DABs) and GitHub Actions.
* **[10 Risk Matrix and Compliance Alignment](./10%20Risk%20Matrix%20and%20Compliance%20Alignment.md):** Direct control mapping to EU AI Act, NIST AI RMF, GDPR, and residual risk mitigations.

## How to Navigate This Documentation Suite

1. **For Security & Compliance Auditors:** Start with `01 Vision`, `04 Active Protection`, and jump directly to `10 Risk Matrix`.
2. **For MLOps & Data Engineers:** Focus on `03 Architecture Overview`, `05 Ingestion Gate`, `06 Observability`, and `08 Continuous Governance`.
3. **For Executive Leadership:** Review `01 Vision`, `02 Business Problem`, and `09 Lakehouse Dashboards`.

