# ADR-001: Hybrid PostgreSQL and Cognee Storage Architecture

## Status
Accepted

## Context
RedThread needs to store and manage traditional application domain entities (organizations, users, memberships, case assignments, document binary metadata, audit logs) while simultaneously executing complex graph-native intelligence operations (multi-hop traversal, entity connection discovery, and semantic vector indexing).

Evaluating potential architectures:
1. **Pure Relational (PostgreSQL Only with Recursive CTEs)**:
   - *Pros*: Single datastore, ACID guarantees, mature tooling.
   - *Cons*: Deep multi-hop graph queries (4+ hops) suffer severe performance degradation. Complex graph algorithms (Dijkstra, community detection) require cumbersome SQL.
2. **Pure Graph Database (e.g., Neo4j or Cognee standalone)**:
   - *Pros*: Native graph traversal and vector indexing.
   - *Cons*: Weak support for complex multi-tenant relational constraints, granular user/case RBAC, payment/session state, and transactional claim event logs.
3. **Hybrid Architecture (PostgreSQL + Cognee)**:
   - Relational database as the authoritative source of truth.
   - Graph engine as an accelerator for graph-backed memory and traversal.

## Decision
We designate **PostgreSQL 16 as the authoritative Source of Truth** and **Cognee as the Graph & Vector Intelligence Accelerator**.

### Responsibilities:
- **PostgreSQL**:
  - Identity, authentication, and organization tenancy.
  - Case workspaces, document metadata, and ingestion job state.
  - Relational claims, source offsets, versioning, and immutable audit logs.
  - Row-Level Security (RLS) enforcement.
- **Cognee**:
  - Knowledge graph entity-relationship indexing.
  - Bounded graph path traversal and neighborhood queries.
  - Vector embeddings and semantic chunk similarity search.

### Invariant:
**Authorization Boundary**: Cognee is untrusted for multi-tenancy enforcement. Any graph path or vector chunk retrieved from Cognee must be validated against PostgreSQL case access rules before being presented to the user.

## Consequences
- **Positive**: Strict ACID guarantees on sensitive evidence, audit logs, and authentication; high-performance graph traversal for investigative queries.
- **Negative**: Requires synchronization logic between PostgreSQL and Cognee during ingestion and claim mutation workflows.
