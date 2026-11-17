# ADR-005: Weighted Multi-Attribute Entity Resolution & Pointer-Based Reversible Merges

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
Initial prototype versions of RedThread used naive exact-match string matching (e.g. lowercase and strip whitespace) for entity identification.

In production, exact matching fails in two critical ways:
1. **False Negatives**: Fails to connect obvious variants of the same entity (*"Tata Consultancy Services"*, *"TCS"*, *"Tata Consultancy Services Ltd."*).
2. **Catastrophic False Merges**: Blindly merging entities based on high token overlap (*"John A. Smith"* and *"John B. Smith"*) corrupts the knowledge graph by cross-wiring unrelated financial accounts or investigation leads.

Furthermore, attempting to support unmerging by storing pre-merge relationship JSON snapshots is fragile: intervening updates and concurrent merges break state restoration.

## Decision
We implement a **calibrated multi-signal scoring model** paired with **human-in-the-loop review queues** and a **relational pointer-based reversible merge architecture**:

1. **Scoring Function**:
   $$S = 0.35N + 0.25A + 0.25C + 0.15T$$
   Evaluating Name Similarity ($N$), Attribute Matching ($A$), Surrounding Context Similarity ($C$), and Entity Type Compatibility ($T$).
   *Important*: $S$ is treated as a **heuristic ranking score**, not a calibrated probability.
2. **Tri-Tier Decision Thresholds**:
   - $S \ge 0.90$: Auto-link as alias candidate.
   - $0.70 \le S < 0.90$: Route to investigator manual review queue.
   - $S < 0.70$: Treat as a distinct entity.
3. **Pointer-Based Reversible Merges**:
   - Source claims **never rewrite their entity foreign keys**; they permanently preserve the original entity extracted from the document.
   - `entities.merged_into_id` records the canonical redirection pointer.
   - `entity_merge_events` logs `source_entity_id`, `target_entity_id`, `merged_by`, `reason`, `created_at`, `unmerged_at`, `unmerged_by`.
   - Unmerging is $O(1)$: setting `merged_into_id = NULL` restores original canonical status with zero claim mutation or evidence loss.

## Consequences
- **Positive**: Prevents graph corruption; preserves original source attribution; makes unmerges deterministic, instantaneous, and non-destructive.
- **Negative**: Graph queries in PostgreSQL must resolve canonical nodes via `COALESCE(e.merged_into_id, e.id)`.

---

## Related Documents
- [Entity Resolution Specification](../entity-resolution.md)
- [Database Design](../database-design.md)
- [Database Transactions](../database-transactions.md)
