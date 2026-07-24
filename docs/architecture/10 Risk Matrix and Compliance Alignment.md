# 10. Risk Matrix and Compliance Alignment

## Executive Summary

The **Risk Matrix and Compliance Alignment** document serves as the regulatory bridge for the **AI Governance Control Tower (AIGCT)**. While technical engines enforce access control, data quality, drift detection, and telemetry, this document maps those technical controls directly to global AI regulations and compliance standards—including the **EU AI Act**, **NIST AI Risk Management Framework (AI RMF)**, **GDPR**, and **CCPA/CPRA**.

This framework transforms complex legal and ethical mandates into verifiable, code-enforced technical controls within the Databricks Lakehouse ecosystem.

---

## Architectural Principles

1. **Governance by Design:** Regulatory compliance is built directly into data pipelines, ML workflows, and storage layers, rather than treated as a manual post-hoc audit.
2. **Traceable Control Mapping:** Every compliance requirement maps directly to a specific technical control, automated job, or telemetry log within the AIGCT architecture.
3. **Continuous Compliance Verification:** Compliance is validated programmatically at every step of the CI/CD and data ingestion lifecycle, preventing non-compliant models or data from reaching production.

---

## Risk Assessment Framework

AIGCT categorizes AI assets and data assets into four distinct risk tiers, aligned with the **EU AI Act** classification system:

| Risk Tier | Description | Examples | Required AIGCT Controls |
| :--- | :--- | :--- | :--- |
| **Unacceptable Risk** | Applications violating fundamental human rights or safety. | Social scoring, subliminal manipulation. | **Blocked at Architecture Level** (Forbidden deployments). |
| **High Risk** | Critical infrastructure, HR/recruitment, credit scoring, legal AI. | Automated resume screening, loan approval ML models. | **Full AIGCT Suite Required:** Row/Column Masking, Circuit Breakers, Continuous Drift Monitoring, Immutable Auditing. |
| **Limited Risk** | Systems with specific transparency requirements. | Chatbots, AI-generated content, recommendation engines. | **Telemetry & Transparency:** Usage logging, provenance tracking via Unity Catalog. |
| **Minimal / No Risk** | Standard operational utilities. | Spam filters, internal search optimization. | **Base Governance:** Standard Unity Catalog access controls. |

---

## Technical Control Matrix (Capabilities to Frameworks)

The following matrix maps AIGCT's core technical components across Layers 1–5 to standard compliance frameworks:

```mermaid
graph LR
    subgraph RegulatoryFrameworks ["Regulatory Frameworks"]
        EU["EU AI Act"]
        NIST["NIST AI RMF"]
        GDPR["GDPR / CCPA"]
    end

    subgraph AIGCTControls ["AIGCT Technical Controls"]
        UC["Active Protection Engine<br><i>(Unity Catalog RLS/Column Masking)</i>"]
        GX["Data Quality Ingestion Gate<br><i>(Great Expectations Circuit Breakers)</i>"]
        Evident["Observability Engine<br><i>(Evidently AI & SHAP Drift/Explainability)</i>"]
        Audit["Telemetry Engine<br><i>(Delta Lake Audit Ledger & Lineage)</i>"]
    end

    UC --> GDPR
    UC --> EU
    GX --> NIST
    Evident --> EU
    Evident --> NIST
    Audit --> EU
    Audit --> GDPR
    Audit --> NIST

    classDef regStyle fill:#1e293b,stroke:#3b82f6,color:#f8fafc;
    classDef ctrlStyle fill:#064e3b,stroke:#10b981,color:#f8fafc;

    class EU,NIST,GDPR regStyle;
    class UC,GX,Evident,Audit ctrlStyle;
```

