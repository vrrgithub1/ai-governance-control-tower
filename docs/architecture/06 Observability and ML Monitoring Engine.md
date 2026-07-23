# 06. Observability and ML Monitoring Engine

## Executive Summary

The **Observability and ML Monitoring Engine** powers **Pillar 3 (Operational Health)** within the **AI Governance Control Tower (AIGCT)**. Machine learning models and generative AI systems degrade over time due to shifting real-world data patterns (concept drift) and underlying covariate shifts (data drift).

Situated in **Layer 3 (Observability & Telemetry)**, this engine utilizes **Evidently AI** for automated statistical drift detection and performance monitoring, alongside **SHAP (SHapley Additive exPlanations)** for localized and global feature explainability. By processing inference payload logs stored in Delta Lake tables, AIGCT continuously evaluates model health without impacting live serving latency.

---

## Architectural Principles

1. **Asynchronous Monitoring:** Telemetry collection and drift analysis are fully decoupled from real-time model inference endpoints to avoid adding serving latency.
2. **Statistical Rigor:** Drift and anomaly detection rely on non-parametric statistical tests (e.g., Kolmogorov-Smirnov, Wasserstein distance, Chi-Square) tailored to individual feature data types.
3. **Transparent Explainability:** Model predictions must be interpretable by human operators and auditors using deterministic feature attribution frameworks (SHAP).

---

## Architecture Topology

```mermaid
graph TD
    subgraph ServingLayer ["Layer 1 / Inference Layer"]
        InferenceEndpoint["Databricks Model Serving / MLflow"]
    end

    subgraph TelemetryStore ["Layer 2: Unity Catalog Storage"]
        InferencePayloads["Inference Payload Delta Table<br><code>gold.inference_logs</code>"]
        BaselineStore["Training Baseline Data<br><code>gold.baseline_features</code>"]
    end

    subgraph MonitoringEngine ["Layer 3: Observability Engine"]
        direction TB
        EvidentlyEngine["Evidently AI Drift Engine"]
        ShapEngine["SHAP Explainability Calculator"]
    end

    subgraph GovernanceHub ["Control Tower Dashboard & Alerting"]
        GovernanceDash["AIGCT Dashboard<br><i>(.lvdash.json)</i>"]
        AlertNotifier["Incident Manager<br><i>(Slack / PagerDuty / Email)</i>"]
    end

    InferenceEndpoint -- "Async Payload Logging" --> InferencePayloads
    BaselineStore --> MonitoringEngine
    InferencePayloads --> MonitoringEngine
    
    EvidentlyEngine -- "Drift Scores & Metrics" --> GovernanceDash
    ShapEngine -- "Feature Importance / Attribution" --> GovernanceDash
    
    EvidentlyEngine -- "Drift Threshold Exceeded" --> AlertNotifier

    classDef servingStyle fill:#1e293b,stroke:#3b82f6,color:#f8fafc;
    classDef storageStyle fill:#064e3b,stroke:#10b981,color:#f8fafc;
    classDef engineStyle fill:#581c87,stroke:#a855f7,color:#f8fafc;
    classDef hubStyle fill:#7c2d12,stroke:#f97316,color:#f8fafc;

    class InferenceEndpoint servingStyle;
    class InferencePayloads,BaselineStore storageStyle;
    class EvidentlyEngine,ShapEngine engineStyle;
    class GovernanceDash,AlertNotifier hubStyle;
```

