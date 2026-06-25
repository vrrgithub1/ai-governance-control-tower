# AI Governance Control Tower

AI Governance Control Tower is an open-source governance platform for managing AI systems in regulated environments. The platform aligns with NIST AI RMF, SR 11-7, BCBS239, and EU AI Act principles through model inventory management, governance controls, risk classification, auditability, and continuous monitoring.

### Target Audience

**Business**

- CRO
- Chief
     Data Officer
- Chief
     AI Officer
- Model
     Risk Management

**Technology**

- Data
     Architects
- Data
     Engineers
- MLOps
     Teams

**Risk & Compliance**

- Internal
     Audit
- Regulatory
     Reporting
- Compliance

### Regulatory Alignment

**NIST AI RMF**

- Govern
- Map
- Measure
- Manage

**SR 11-7**

- Model
     Risk Management

**EU AI Act**

- Transparency
- Human
     Oversight
- Monitoring

**BCBS239**

- Data
     Quality
- Lineage
- Controls

### High-Level Architecture

```mermaid
graph TD;
    classDef process fill:#2196F3,stroke:#0D47A1,stroke-width:2px,color:#fff;
    classDef entity fill:#4CAF50,stroke:#1B5E20,stroke-width:2px,color:#fff;
    
    Dash[Governance Dashboard Streamlit]:::entity --> DQ[Data Quality]:::entity;
    Dash[Governance Dashboard Streamlit]:::entity --> MRM[Model Risk Monitoring]:::entity;
    Dash[Governance Dashboard Streamlit]:::entity --> AIGR[AI Governance Reporting]:::entity;

    DQ[Data Quality]:::entity --> GEV(Great Expectations Validation):::process;
    MRM[Model Risk Monitoring]:::entity --> EADD(Evidently AI Drift Detection):::process;
    AIGR[AI Governance Reporting]:::entity --> AEES(Audit Engine Evidence Store):::process;
    GEV(Great Expectations Validation):::process --> FSDB(Feature Store DuckDB):::process;
    EADD(Evidently AI Drift Detection):::process --> FSDB(Feature Store DuckDB):::process;
    AEES(Audit Engine Evidence Store):::process --> FSDB(Feature Store DuckDB):::process;

    FSDB(Feature Store DuckDB):::process --> MLM("ML Models (XGBoost/LightGBM)"):::process;

```
