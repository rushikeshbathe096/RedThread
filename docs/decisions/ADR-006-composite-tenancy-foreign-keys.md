# ADR-006: Composite Tenancy Foreign Keys for Invariant Enforcement

> **Document Status**: `DESIGN`  
> **Date**: 2026-11-18  
> **Status**: Accepted

---

## Context
In a multi-tenant investigation platform, cross-tenant or cross-case data contamination is a catastrophic failure. For example:
1. Assigning a user to a case belonging to an organization where the user is not a member.
2. Grounding a claim in Case A using a source document belonging to Case B.

Application-level checks (e.g. FastAPI dependencies) are necessary but insufficient on their own. A developer omission, ORM misconfiguration, or raw script execution could bypass application logic and corrupt data integrity.

## Decision
We enforce multi-tenant and cross-case boundaries **directly at the PostgreSQL schema layer** using **Composite Unique Constraints and Composite Foreign Keys**:

1. **Case Membership Isolation**:
   - `cases` enforces `UNIQUE (id, organization_id)`.
   - `memberships` enforces `UNIQUE (organization_id, user_id)`.
   - `case_members` has a composite foreign key referencing `memberships(organization_id, user_id)` and `cases(id, organization_id)`.
   - *Outcome*: It is mathematically impossible for PostgreSQL to store a case assignment where the user's organization does not match the case's organization.

2. **Claim Grounding Case Isolation**:
   - `documents` enforces `UNIQUE (id, case_id)`.
   - `claims` enforces `UNIQUE (id, case_id)`.
   - `claim_sources` has composite foreign keys referencing `claims(id, case_id)` and `documents(id, case_id)`.
   - *Outcome*: A claim in Case A can never be grounded by or cite a document belonging to Case B.

## Consequences
- **Positive**: Absolute data integrity guaranteed by the database engine; prevents IDOR and cross-case contamination even if application code fails.
- **Negative**: Requires carrying `organization_id` or `case_id` into composite child keys and junction tables; slightly larger foreign key indexes.

---

## Related Documents
- [Database Design](../database-design.md)
- [Database Security & RLS](../database-security.md)
- [Threat Model](../threat-model.md)
