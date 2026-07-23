# 05. Data Quality Ingestion Gate

## Executive Summary

The **Data Quality Ingestion Gate** acts as the primary in-flight firewall of the **AI Governance Control Tower (AIGCT)**. Situated in **Layer 1 (Ingestion & In-Flight Isolation)**, it ensures that unvalidated or corrupted data is halted before it can pollute downstream Medallion Delta Lake storage (Bronze/Silver/Gold).

By integrating **Great Expectations (GE)** into the ingestion pipeline, AIGCT programmatically validates incoming data streams against strict data contracts, schemas, and statistical assertions. Payloads passing validation seamlessly flow into Unity Catalog, while non-compliant records are automatically routed to isolated Quarantine storage and trigger real-time alerts.

## Architectural Principles

1. **Shift-Left Validation:** Quality, integrity, and schema checks are executed at the landing zone prior to Delta table ingestion, minimizing compute and cleaning costs downstream.
2. **Circuit Breaker Pattern:** If critical assertion thresholds fail (e.g., unexpected `NULL` values in primary keys or missing PII tags), processing halts automatically to prevent data corruption.
3. **Automated Quarantine & Remediation:** Bad payloads are never dropped silently. They are segregated with full error metadata to facilitate root-cause analysis without blocking clean data pipelines.

---

## Architecture Topology

```mermaid
graph TD
    subgraph LandingZone ["Landing Zone (Azure Blob / ADLS Gen2)"]
        RawData["Raw Input Data Payload<br><i>(JSON / CSV / Parquet)</i>"]
    end

    subgraph GE_Engine ["Data Quality Gate (Great Expectations)"]
        direction TB
        Suite["Expectation Suite<br><i>(Schema, Nullability, Ranges)</i>"]
        Validator["GE Validation Operator"]
        Suite --> Validator
    end

    subgraph StorageLayer ["Layer 2: Unity Catalog Storage"]
        BronzeTable["Medallion Bronze Table<br><i>(Raw Cleaned Delta)</i>"]
    end

    subgraph QuarantineLayer ["Quarantine & Incident Management"]
        Quarantine["Quarantine Storage<br><i>(Isolated Delta / Blob)</i>"]
        AlertSystem["Alerting System<br><i>(Webhook / Slack / PagerDuty)</i>"]
    end

    RawData --> Validator
    Validator -- "Passes Assertions" --> BronzeTable
    Validator -- "Fails Assertions" --> Quarantine
    Quarantine --> AlertSystem

    classDef landingStyle fill:#1e293b,stroke:#3b82f6,color:#f8fafc;
    classDef geStyle fill:#581c87,stroke:#a855f7,color:#f8fafc;
    classDef storageStyle fill:#064e3b,stroke:#10b981,color:#f8fafc;
    classDef quarantineStyle fill:#7c2d12,stroke:#f97316,color:#f8fafc;

    class RawData landingStyle;
    class Suite,Validator geStyle;
    class BronzeTable storageStyle;
    class Quarantine,AlertSystem quarantineStyle;
```

