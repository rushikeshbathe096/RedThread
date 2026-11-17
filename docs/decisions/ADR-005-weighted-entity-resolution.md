# ADR-005: Weighted Multi-Attribute Entity Resolution

## Status
Accepted

## Context
Initial prototype versions of RedThread used naive exact-match string matching (e.g. lowercase and strip whitespace) for entity identification.

In production, exact matching fails in two critical ways:
1. **False Negatives**: Fails to connect obvious variants of the same entity (*"Tata Consultancy Services"*, *"TCS"*, *"Tata Consultancy Services Ltd."*).
2. **Catastrophic False Merges**: Blindly merging entities based on high token overlap (*"John A. Smith"* and *"John B. Smith"*) corrupts the knowledge graph by cross-wiring unrelated financial accounts or investigation leads.

## Decision
We implement a **calibrated, multi-signal scoring model** paired with **human-in-the-loop review queues** and **reversible merge history**:

1. **Scoring Function**:
   $$S = 0.35N + 0.25A + 0.25C + 0.15T$$
   Evaluating Name Similarity ($N$), Attribute Matching ($A$), Surrounding Context Similarity ($C$), and Entity Type Compatibility ($T$).
2. **Tri-Tier Decision Thresholds**:
   - $S \ge 0.90$: Auto-link as alias candidate.
   - $0.70 \le S < 0.90$: Route to investigator manual review queue.
   - $S < 0.70$: Treat as a distinct entity.
3. **Reversible Merges (Unmerge Support)**:
   - All entity merges are logged in `entity_merges` with pre-merge relationship snapshots.
   - Investigators can execute an unmerge at any time, restoring original entity IDs and decoupling falsely joined graph edges.

## Consequences
- **Positive**: Prevents graph corruption from premature merges; handles real-world corporate abbreviations and aliases; provides a clean manual review workflow.
- **Negative**: Requires tuning weights $N, A, C, T$ against labeled investigative datasets; adds a manual review queue to the frontend UI.
