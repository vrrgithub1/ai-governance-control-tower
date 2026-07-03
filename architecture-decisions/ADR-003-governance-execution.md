# ADR-003: Double-Layer Status Separation for Operational Integrity

## Status

Approved

## Context

A pipeline script can execute perfectly to its final line of code without crashing, yet ingest a completely invalid data file payload full of parsing anomalies. Conversely, a script might drop its database connection while handling verified data. A single `Status` attribute cannot convey both mechanical application runtime states and data payload quality.

## Decision

We enforce a decoupled status state architecture inside the master execution catalog tracking records:

* **`Status`:** Reflects the script's runtime engine state (`'In Progress'`, `'Completed'`, `'Failed'`).
* **`Overall_Status`:** Reflects the structural integrity of the processed data payload matrix (`'RUNNING'`, `'PASSED'`, `'PASSED WITH WARNINGS'`, `'FAILED'`).

## Consequences

* **Pros:** Allows compliance dashboards to instantly highlight scenarios where data validation failed even though the underlying technology pipeline ran to completion successfully.
* **Cons:** Increases logging complexity within the final operational cleanup code block to calculate data volume distributions.
