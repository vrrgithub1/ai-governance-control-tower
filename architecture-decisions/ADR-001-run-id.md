# ADR-001: Sequential Date-Based Formatting for Run Identifiers

## Status

Approved

## Context

The platform requires a global execution token (`Run_Id`) to unify multiple concurrent or sequential data pipeline executions under a single, trackable business batch execution window. This ID must be highly readable, chronologically sortable by downstream analytical layers (such as DuckDB or Streamlit), and explicitly convey when a processing run occurred.

## Decision

We choose to enforce a structured, sequence-appended format for all master orchestration run tracking tokens:
`RUN_YYYYMMDD_NNN`

Where:

* `RUN_`: Explicit system constant prefix.
* `YYYYMMDD`: Dynamic execution date timestamp context.
* `_NNN`: A zero-padded, 3-digit incremental integer sequence reset daily (e.g., `RUN_20260703_001`).

## Consequences

* **Pros:** Highly scannable for audit lookups; can be sorted using simple string sorting without needing complex timestamp fields.
* **Cons:** Requires a database sequence check query (`MAX(Run_Id)`) at runtime initiation to accurately compute the next dynamic increment.
