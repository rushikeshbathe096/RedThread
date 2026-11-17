# ADR-006: Composite Tenancy Foreign Keys for Invariant Enforcement

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
In a multi-tenant investigation platform, cross-tenant or cross-case data contamination is a catastrophic failure. For example:
1. Assigning a user to a case belonging to an organization where the user is not a member.
2. Grounding a claim in Case A using a source document belonging to Case B.
3. Connecting a claim in Organization A to an entity belonging to Organization B.

Application-level checks (e.g. FastAPI dependencies) are necessary but insufficient on their own. A developer omission, ORM misconfiguration, or raw script execution could bypass application logic and corrupt data integrity.

## Decision
We enforce multi-tenant and cross-case boundaries **directly at the PostgreSQL schema layer** using **Composite Unique Constraints and Composite Foreign Keys**:

1. **Case Membership Isolation**:
   - `cases` enforces `UNIQUE (organization_id, id)`.
   - `memberships` enforces `UNIQUE (organization_id, user_id)`.
   - `case_members` has a composite foreign key referencing `memberships(organization_id, user_id)` and `cases(organization_id, id)`.
   - *Outcome*: It is mathematically impossible for PostgreSQL to store a case assignment where the user's organization does not match the case's organization.

2. **Organization-Safe Entity Grounding in Claims**:
   - `entities` enforces `UNIQUE (organization_id, id)`.
   - `claims` enforces composite foreign keys referencing:
     - `cases(organization_id, case_id)`
     - `entities(organization_id, subject_entity_id)`
     - `entities(organization_id, object_entity_id)`
   - *Outcome*: A claim in Organization A cannot reference a subject or object entity in Organization B.

3. **Claim Grounding Case Isolation**:
   - `documents` enforces `UNIQUE (case_id, id)`.
   - `claims` enforces `UNIQUE (case_id, id)`.
   - `document_chunks` enforces `UNIQUE (document_id, id)`.
   - `claim_sources` enforces:
     - `FOREIGN KEY (case_id, claim_id) REFERENCES claims(case_id, id)`
     - `FOREIGN KEY (case_id, document_id) REFERENCES documents(case_id, id)`
     - `FOREIGN KEY (document_id, chunk_id) REFERENCES document_chunks(document_id, id)`
   - *Outcome*: A claim in Case A can never cite a document from Case B, and a chunk cited must belong to the cited document.

## Consequences
- **Positive**: Absolute data integrity guaranteed by the database engine; prevents IDOR and cross-case contamination even if application code fails.
- **Negative**: Requires carrying `organization_id` or `case_id` into composite child keys and junction tables; slightly larger foreign key indexes.

---

## Related Documents
- [Database Design](../database-design.md)
- [Database Security & RLS](../database-security.md)
- [Threat Model](../threat-model.md)
