# ADR-004: Versioned Claim Lifecycle and Intelligent Forgetting

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
In real investigations, information is rarely static. Initial reports frequently contain assumptions, mistaken identities, or deliberate deception that subsequent forensic evidence contradicts.

Traditional search systems and vector stores handle updates destructively:
- They overwrite or delete existing records.
- Or they index contradictory documents simultaneously, causing the LLM to output conflicting statements or invent an erroneous synthesis.

In legal and investigative domains, **silent erasure of historical claims is unacceptable**. Investigators must know *what* was believed, *when* it was challenged, *who* reviewed it, and *why* it was altered.

## Decision
We reject destructive updates and in-place deletions in favor of an **Append-Only Audited Claim State Machine with Immutable Version Snapshots**:

1. **Separation of Operational Status vs. Review Outcome**:
   - Claim Status: `ACTIVE`, `DISPUTED`, `RETRACTED`.
   - Review Outcome: `PENDING`, `UPHELD`, `REJECTED`, `INCONCLUSIVE`.
2. **Strict Exclusivity & Structured Qualifiers**:
   - `claim_type`: `ENTITY_TO_ENTITY` or `ENTITY_TO_LITERAL`.
   - Structured metadata (amounts, currencies, dates) stored in `qualifiers` (`JSONB`).
3. **Immutable Content Versioning (`claim_versions`)**:
   - The canonical `claims` table represents the current active operational state.
   - Every mutation inserts an immutable full content snapshot into `claim_versions` with the actor, reason, timestamp, and version number.
4. **Immutable Event Log (`claim_events`)**:
   - Every challenge, dispute, review, and retraction creates an immutable event row recording actor ID, prior status, new status, timestamp, and counter-document reference.
5. **Intelligent Recall Integration**:
   - `ACTIVE` claims are included in default graph traversal.
   - `DISPUTED` claims are included with mandatory dispute annotations and counter-citations.
   - `RETRACTED` claims are excluded from standard recall answers but preserved in historical audits and reports.

## Consequences
- **Positive**: Complete historical accountability; legal and investigative integrity; eliminates LLM confusion when handling contradictory sources.
- **Negative**: Database storage increases monotonically; graph queries require conditional filtering on claim status.

---

## Related Documents
- [Contradiction Management & Claim Lifecycle](../contradiction-and-claim-lifecycle.md)
- [Database Design](../database-design.md)
- [Database Transactions](../database-transactions.md)
