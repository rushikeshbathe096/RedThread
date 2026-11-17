# Module 10: Reports and Export

> **Document Status**: `DESIGN`  
> **Module ID**: `MOD-10`  
> **Responsibility**: Frozen evidentiary dossier generation (PDF, JSON, CSV) and historical snapshot compliance.

---

## 1. Purpose & Scope
At the conclusion of an investigation (or during periodic compliance audits), investigators must export evidence-backed summaries for court submission, regulatory review, or executive briefings.

---

## 2. Key Capabilities
- **Snapshot Evidence Preservation**:
  Reports capture an immutable snapshot of all claims, sources, and dispute statuses at generation time. If a claim is subsequently challenged or retracted in the active database, previous reports reflect exactly what was known when generated.
- **Report Contents**:
  - Investigation overview & question addressed.
  - Entity rosters & network diagram visualizations.
  - Granular claims list with document, page, and offset citations.
  - Disputed claims register with counter-citations.
  - Audit log timeline of investigator actions.
- **Multi-Format Export**:
  - **PDF**: Formatted evidentiary dossier suitable for legal submission.
  - **JSON**: Machine-readable evidence package with full graph topology.
  - **CSV**: Tabular dump of entities, transactions, and claim registries.

---

## 3. Workflow

```mermaid
flowchart LR
    A[Investigator] -->|Request Export| B[POST /cases/{id}/reports]
    B --> C[Fetch Frozen Claim & Entity Snapshot]
    C --> D[Render Graph Vector / Diagram]
    D --> E[Generate PDF / JSON / CSV Artifact]
    E --> F[Store in S3 & Log in audit_logs]
    F --> G[Return Downloadable URL]
```

---

## 4. Related Documents
- [API Specification](../api-specification.md)
- [Database Design](../database-design.md)
- [Definition of Done](../definition-of-done.md)
