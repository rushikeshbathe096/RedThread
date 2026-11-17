# ADR-007: Claims as Canonical Assertions Eliminating Redundant Relationship Tables

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
Initial prototypes often model knowledge graphs with a dedicated `relationships` table (e.g. `source_id, target_id, predicate`) alongside an evidentiary `claims` table.

However, in an investigative intelligence platform:
- Every graph relationship is, by definition, an evidence-backed claim extracted from a document or asserted by an investigator.
- Storing edges in both `claims` and a separate `relationships` table creates a duplicate source of truth.
- When an investigator disputes, updates, or retracts a claim, the application must remember to update both tables synchronously. Under network failures or concurrent updates, this produces split-brain graph inconsistencies.

## Decision
We eliminate the redundant `relationships` table. **`claims` is the single canonical representation of all assertions and graph edges in RedThread.**

### Structural Mapping:
- **Entity-to-Entity Edge**: `claims (subject_entity_id, predicate, object_entity_id)`
  - Directly maps to a directed knowledge graph edge: `(Subject) -[Predicate]-> (Object)`.
- **Entity-to-Literal Attribute**: `claims (subject_entity_id, predicate, object_value)`
  - Directly maps to an entity attribute or literal assertion (e.g. `$50,000` or `12 March 2026`).
- **Graph Traversal & Visualization**:
  - Graph views query `claims WHERE status = 'ACTIVE'`.
  - Disputed edges query `claims WHERE status = 'DISPUTED'` and render with alert styling.

## Consequences
- **Positive**: Single source of truth; zero synchronization lag between claims and graph edges; simplifies transaction boundaries; eliminates split-brain corruption.
- **Negative**: Graph queries in PostgreSQL join against `claims` and `entities` rather than a simplified node-edge projection table (mitigated by partial index `idx_claims_active`).

---

## Related Documents
- [Database Design](../database-design.md)
- [Hybrid Recall & RAG](../hybrid-recall-and-rag.md)
- [Contradiction Management](../contradiction-and-claim-lifecycle.md)
