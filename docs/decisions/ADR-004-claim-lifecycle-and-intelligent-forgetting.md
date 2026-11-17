# ADR-004: Versioned Claim Lifecycle and Intelligent Forgetting

## Status
Accepted

## Context
In real investigations, information is rarely static. Initial reports frequently contain assumptions, mistaken identities, or deliberate deception that subsequent forensic evidence contradicts.

Traditional search systems and vector stores handle updates destructively:
- They overwrite or delete existing records.
- Or they index contradictory documents simultaneously, causing the LLM to output conflicting statements or invent an erroneous synthesis.

In legal and investigative domains, **silent erasure of historical claims is unacceptable**. Investigators must know *what* was believed, *when* it was challenged, *who* reviewed it, and *why* it was altered.

## Decision
We reject destructive updates and in-place deletions in favor of an **Append-Only Audited Claim State Machine**:

1. **Explicit Review Statuses**: Claims transition across `ACTIVE`, `DISPUTED`, `REVIEWED`, and `RETRACTED`.
2. **Three Orthogonal Dimensions**: We maintain separate metrics for:
   - *Extraction Confidence* (model's certainty in reading the text).
   - *Evidence Strength* (evidentiary weight of the document type).
   - *Review Status* (formal investigative status assigned by a human).
   These are never collapsed into a single floating-point number.
3. **Immutable Event Log (`claim_events`)**: Every challenge, dispute, review, and retraction creates an immutable event row recording actor ID, prior status, new status, timestamp, and counter-document reference.
4. **Intelligent Recall Integration**:
   - `ACTIVE` claims are included in default graph traversal.
   - `DISPUTED` claims are included with mandatory dispute annotations and counter-citations.
   - `RETRACTED` claims are excluded from standard recall answers but preserved in historical audits and reports.

## Consequences
- **Positive**: Complete historical accountability; legal and investigative integrity; eliminates LLM confusion when handling contradictory sources.
- **Negative**: Database storage increases monotonically; graph queries require conditional filtering on claim status.
