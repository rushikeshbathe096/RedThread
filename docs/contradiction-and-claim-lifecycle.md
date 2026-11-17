# RedThread Contradiction Management & Claim Lifecycle

> **Document Status**: `DESIGN`  
> **Signature Differentiator**: Non-destructive evidence handling, explicit dispute states, immutable versioning, and historical accountability.

---

## 1. The Core Philosophy: Historical Accountability

In real-world investigations, facts evolve and testimonies clash:
* **Report 1 (June 2025)**: *"John Smith initiated wire transfer #892 to Offshore Account X."*
* **Report 2 (October 2025)**: *"Forensic audit proves wire transfer #892 was executed by a rogue financial officer using John Smith's compromised credentials."*

Traditional RAG and vector databases handle this destructively: they either overwrite the old vector embedding, return an incoherent blend of contradictory passages, or hallucinate an impossible compromise.

**RedThread preserves both pieces of evidence, tracks the controversy explicitly, and models contradictory claims as first-class graph elements.**

---

## 2. Separation of Claim Status vs. Review Outcome

A critical architectural requirement in RedThread is separating the **operational state of a claim** from the **investigative review outcome**:

| Concept | Enum Values | Meaning |
| :--- | :--- | :--- |
| **Claim Status (`status`)** | `ACTIVE` | Normal evidence; included in default graph traversal and AI recall. |
| | `DISPUTED` | Claim has been formally challenged; highlighted with dispute styling and mandatory counter-citations. |
| | `RETRACTED` | Claim has been refuted; excluded from active graph traversal and normal recall answers. |
| **Review Outcome (`review_outcome`)** | `PENDING` | Default initial state; awaiting formal investigative review. |
| | `UPHELD` | Reviewer examined conflicting sources and confirmed the claim is substantiated. |
| | `REJECTED` | Reviewer determined the claim is refuted by superior evidence. |
| | `INCONCLUSIVE` | Available evidence is insufficient to confirm or refute; claim remains flagged. |

---

## 3. The Three Orthogonal Dimensions of Truth

RedThread strictly avoids collapsing evidentiary truth into a single floating-point number:

```mermaid
quadrantChart
    title Epistemic Dimensions in RedThread
    x-axis Low Extraction Confidence --> High Extraction Confidence
    y-axis Low Evidence Strength --> High Evidence Strength
    "Scanned Hand-Written Receipt" : [0.35, 0.90]
    "Audited Bank Ledger" : [0.95, 0.95]
    "Corrupted OCR Excerpt" : [0.20, 0.20]
    "Flawlessly Extracted Anonymous Tip" : [0.98, 0.30]
```

1. **Extraction Confidence ($E_c \in [0, 1]$)**: The LLM/parser's certainty that the document *actually states* what was extracted.
2. **Evidence Strength ($E_s \in [0, 1]$)**: The evidentiary weight of the underlying document (e.g., sworn affidavit / audited ledger vs. hearsay email).
3. **Review Status ($R_s \in \{\text{ACTIVE}, \text{DISPUTED}, \text{RETRACTED}\}$)**: The formal investigative status assigned by an authorized investigator or reviewer.

---

## 4. Claim State Machine & Workflow

```mermaid
stateDiagram-v2
    [*] --> ACTIVE : Extracted from Source Document (review_outcome: PENDING)
    ACTIVE --> DISPUTED : Investigator challenges claim / Counter-document uploaded
    DISPUTED --> REVIEWED_UPHELD : Reviewer upholds claim
    REVIEWED_UPHELD --> ACTIVE : Claim confirmed (review_outcome: UPHELD)
    DISPUTED --> REVIEWED_REJECTED : Reviewer refutes claim
    REVIEWED_REJECTED --> RETRACTED : Claim retracted (review_outcome: REJECTED)
    RETRACTED --> ACTIVE : Reinstated if counter-evidence debunked
    RETRACTED --> [*]
    ACTIVE --> [*]
```

---

## 5. Immutable Versioning & The `claim_events` Ledger

### 5.1 Immutable Content Snapshots (`claim_versions`)
Every insert, challenge, review, and reinstatement creates an immutable row in `claim_versions`:
```sql
INSERT INTO claim_versions (
    id, claim_id, version, organization_id, case_id, subject_entity_id, 
    predicate, claim_type, object_entity_id, object_value, qualifiers, 
    is_negated, status, review_outcome, extraction_confidence, 
    change_reason, actor_id
) VALUES (
    uuid_generate_v4(), :claim_id, :new_version, :org_id, :case_id, :subj_id,
    :predicate, :claim_type, :obj_ent_id, :obj_val, :qualifiers,
    :is_negated, :status, :outcome, :confidence,
    :change_reason, :actor_id
);
```

### 5.2 Event Ledger (`claim_events`)
```sql
INSERT INTO claim_events (
    claim_id, event_type, actor_id, prior_status, new_status, 
    prior_review_outcome, new_review_outcome, reason, metadata
) VALUES (
    'c101-uuid', 'CLAIM_CHALLENGED', 'user-bob-uuid', 'ACTIVE', 'DISPUTED', 
    'PENDING', 'PENDING', 
    'Report B (Doc #45, Page 12) demonstrates account takeover prior to transfer.',
    '{"counter_document_id": "doc-45-uuid", "page": 12}'
);
```

---

## 6. Concrete Query Answer Transformation

### Query: *"What was John Smith's involvement in the transfer to Offshore Account X?"*

#### Scenario A: Prior to Contradiction (Claim Status: `ACTIVE`)
> **Answer**:  
> John Smith initiated a wire transfer of $50,000 to Offshore Account X on 14 June 2025 [Claim #c101].  
> **Evidence**:  
> - Wire Transfer Summary Report (Doc #12, Page 4).  
> **Graph Path**:  
> `John Smith` $\xrightarrow{\text{INITIATED}}$ `Transfer #892` $\xrightarrow{\text{CREDITED\_TO}}$ `Offshore Account X`.

#### Scenario B: After Contradiction (Claim Status: `DISPUTED`)
> **Answer**:  
> The attribution of wire transfer #892 to John Smith is **currently disputed** [Claim #c101].  
> - **Initial Claim**: Wire Transfer Summary Report (Doc #12, Page 4) documents the transfer under John Smith's name.  
> - **Counter Evidence**: Forensic IT Audit (Doc #45, Page 12) asserts John Smith's credentials were compromised prior to the transaction, attributing the transfer to an unauthorized party.  
> - **Conclusion**: The available evidence does not establish John Smith's direct involvement conclusively.  
> **Warnings**:  
> ⚠️ *Claim #c101 is marked DISPUTED by Investigator Bob.*

---

## 7. Related Documents
- [Database Design](database-design.md)
- [Database Transactions](database-transactions.md)
- [Hybrid Recall & RAG](hybrid-recall-and-rag.md)
- [ADR-004: Versioned Claim Lifecycle](decisions/ADR-004-claim-lifecycle-and-intelligent-forgetting.md)
