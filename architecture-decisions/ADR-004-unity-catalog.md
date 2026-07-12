# Architectural Decision Record: ADR-004 - Unity Catalog Enterprise Data Layout

## Status

Proposed (Milestone I)

## Context

In Phase I of the AI Governance Control Tower (AIGCT), we established a decoupled, relational metadata engine to track active model and data asset inventories. As we transition to an enterprise cloud architecture on Azure Databricks, we need a standardized, governed data layout that programmatically enforces structural boundaries across the data lifecycle.

Without a centralized governance catalog, mapping multi-tenant data pipelines, managing column-level data lineage, and enforcing fine-grained access control across the Medallion architecture (Bronze, Silver, Gold layers) introduces significant operational overhead and audit risks.

## Decision

We will adopt **Azure Databricks Unity Catalog** as the primary enterprise governance plane. The platform's native **3-level namespace (`catalog.schema.table_or_view`)** will be strictly mandated to enforce logical isolation, automated data lineage tracking, and deterministic metadata capturing.

### 1. Catalog Hierarchy Design

To achieve isolated environment promotion and clear separation of concerns, the layout will be structured around a dedicated system governance catalog and separate environment-specific production catalogs:

- `aigct_governance`: The central control plane catalog. It houses the unified system logs, operational audit trails, and global policy configurations.
- `aigct_dev` / `aigct_stg` / `aigct_prod`: Environment-specific data catalogs containing the actual operational pipelines.

### 2. Schema (Database) Architecture mapping the Medallion Flow

Inside each environment catalog (e.g., `aigct_prod`), data assets will be stratified using schemas that map directly to functional data processing maturity states:

- `..._bronze`: Raw landing zone. Ingests raw technical telemetry and upstream operational source data as immutable append-only Delta tables.
- `..._silver`: Enforced validation zone. Cleaned, structurally validated, and heavily scrutinized data assets where out-of-bounds trade variables or missing features are filtered or quarantined.
- `..._gold`: Aggregated business layer. Executive-ready tables, feature store matrices, and final inference tables optimized for dashboard consumption and auditing.

### 3. Structural Metadata Tagging

We will leverage Unity Catalog’s **Attribute-Based Access Control (ABAC)** and object tags to natively embed your Phase I asset tracking directly onto the data layer. Tables and columns will programmatically receive tags such as `PII=true`, `RegulatoryScope=EU_AI_ACT`, and `RiskClassification=High`.

[ Ingestion Layer ] ──► Ingests to: aigct_prod.raw_source_bronze
│
▼ (Data Quality Guardrails)
[ Validation Layer ] ──► Transforms to: aigct_prod.validated_data_silver
│
▼ (Lineage Logged by Unity Catalog)
[ Aggregation Layer ] ──► Publishes to: aigct_prod.executive_scores_gold

## Consequences

### Positive

- **Automated Runtime Lineage:** Unity Catalog captures runtime column-level and table-level lineage out of the box for all Spark SQL and PySpark executions. This completely automates the tracking requirements detailed in ADR-002.
- **Immutable System Tables:** Audit tracking shifts from custom table writing to querying Databricks' native, immutable `system.operational_lineage` and `system.access_logs`, maximizing audit reliability.
- **Fine-Grained Governance:** Centralized access control allows for dynamic column-masking and row-filtering policies on sensitive attributes (like credit scores or personal identifiers) directly inside the storage layer.

### Negative / Trade-offs

- **Platform Dependency:** Moving to Unity Catalog couples our data schema layer tightly with the Databricks engine, reducing open-source engine portability.
- **Compute Overheads:** Querying Unity Catalog-governed tables requires executing workloads on Databricks clusters running Shared or Single-User access modes, which may restrict the usage of older, legacy cluster configurations.

## References

- **ADR-002:** Data Asset Inventory Baseline
- **AIGCT Azure Databricks Roadmap:** Milestone I (Data Posture Blueprint)
