# Data Model

## Source status

No official Theme 2 PDF, dataset, deeplink catalog, or output schema is currently present in the workspace. Therefore this document does not define a data model or data fields.

## Official requirements

Pending the official source materials. Do not infer required fields, action types, deeplink formats, or response shapes from this placeholder.

## Current bootstrap contracts

These are temporary implementation contracts only, not official schema definitions:

- `TroubleshootRequest` accepts a non-empty `query` string.
- `PlaceholderTroubleshootResponse` returns `status`, `detail`, and the submitted `query` so the bootstrap API can explicitly state that no troubleshooting plan has been generated.
- `QueryEnrichmentResult` retains `original_query` and provides `normalized_query`, `core_intent`, and deterministic `variations` for later retrieval.
- `TroubleshootingStructure` carries those enrichment fields plus ordered `keywords`, explicit `symptoms`, explicit `entities`, explicit `device_context`, lexical `severity`, `ambiguity_reason`, `possible_intents`, and `is_ambiguous`; it intentionally contains no actions or deeplinks.

Replace these temporary contracts only after the official schema and data files are supplied and preserved in `data/original/`.
