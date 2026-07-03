# ADR-002: Hardened Pessimistic Security Fallbacks and Static System Placeholder

## Status

Approved

## Context

Data privacy and corporate audit compliance require perfect classification of sensitive information types (PII, Financial Data, etc.) within the global catalog. Relying on an assumption of 'No' or 'False' for missing flags introduces a critical vulnerability if business operators register data assets lazily. Additionally, non-data pipeline execution steps (infrastructure health checks, cluster initialization) require tracking but lack a natural `Dataset_Id`, creating referential integrity tracking gaps.

## Decision

We implement a two-pronged structural guardrail:

1. **Pessimistic Flag Rules:** All asset governance status columns are declared `NOT NULL` and default directly to `TRUE` (or highest tier for retention periods) unless explicitly reviewed and scaled back.
2. **Static Infrastructure Row Seeding:** We permanently inject a system identity record (`'SYSTEM'`) directly into the `data_asset_inventory` tracking catalog.

## Consequences

* **Pros:** Enforces strict protection—unreviewed files are secured by default. The system row allows infrastructure tasks to maintain foreign key integrity checks without forcing messy `NULL` fields on analytical queries.
* **Cons:** Requires explicit downstream downgrade processes by a dedicated data steward to reduce resource overhead on data fields that are actually public.
