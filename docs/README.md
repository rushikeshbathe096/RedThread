# RedThread Engineering Documentation

> **Documentation Status**: `DESIGN`  
> **Master Specification**: Authoritative engineering blueprint for the RedThread investigative intelligence platform.

---

## 📌 Executive Summary

Organizations investigate complex situations using information spread across hundreds or thousands of heterogeneous documents (PDFs, emails, transcripts, financial ledgers, and research reports). Traditional keyword searches and vanilla vector-based RAG fail when:
1. Relationships span across multiple distinct documents (multi-hop connections).
2. Information across documents is contradictory, outdated, or disputed.
3. Generated AI answers lack granular, verifiable evidence citations.

RedThread addresses these challenges through three foundational tenets:
- **Evidence-First**: Every answer and relationship is grounded in source documents with exact character offsets.
- **Graph-Based Memory**: Cross-document relationships are preserved as traversable entities and attributed claims.
- **Historical Accountability**: Contradictions never silently overwrite past evidence; claims follow an audited lifecycle.

---

## 📚 Master Documentation Index

### Core Architecture & System Specifications
| Document | Status | Description |
| :--- | :---: | :--- |
| **[System Architecture](architecture.md)** | `DESIGN` | Modular monolith topology, PostgreSQL + Cognee hybrid persistence, and request lifecycles. |
| **[Database Design & Schema](database-design.md)** | `DESIGN` | PostgreSQL 16 schema, DDL tables, composite foreign keys, constraints, normalization, and RLS. |
| **[Database Transactions & Concurrency](database-transactions.md)** | `DESIGN` | ACID guarantees, isolation levels, row-level locking, optimistic versioning, and transaction boundaries. |
| **[Database Security & RLS](database-security.md)** | `DESIGN` | Least privilege roles (`redthread_app`, `redthread_worker`), `FORCE ROW LEVEL SECURITY`, and tenant context. |
| **[Database Performance & Indexing](database-performance.md)** | `DESIGN` | B-tree, GIN trigram, partial indexes, EXPLAIN query plans, and connection pool budgeting. |
| **[Database Operations & Recovery](database-operations.md)** | `DESIGN` | Alembic expand-and-contract migrations, continuous WAL archiving, PITR runbook, and vacuum tuning. |
| **[REST API Specification](api-specification.md)** | `DESIGN` | `/api/v1` contract covering Auth, Cases, Ingestion, Entities, Graph, Recall, and Claims. |
| **[Security Model & Multi-Tenancy](security-model.md)** | `DESIGN` | Tenant isolation, RBAC matrix, IDOR guards, Argon2id, JWT rotation, and upload security. |
| **[Document Ingestion Pipeline](ingestion-pipeline.md)** | `DESIGN` | Asynchronous Celery workers, multi-format parsers, outbox pattern, and state machine. |
| **[Entity Resolution System](entity-resolution.md)** | `DESIGN` | Multi-attribute weighted scoring ($S$), candidate retrieval, review queues, and reversible merges. |
| **[Contradiction & Claim Lifecycle](contradiction-and-claim-lifecycle.md)** | `DESIGN` | Claim state machine (`ACTIVE`, `DISPUTED`, `RETRACTED`), `claim_events`, and recall behavior. |
| **[Hybrid Recall & Grounded RAG](hybrid-recall-and-rag.md)** | `DESIGN` | 13-stage hybrid retrieval, BFS bounded traversal, citation validation, and fallback handling. |

### Operational, Testing & Security Blueprints
| Document | Status | Description |
| :--- | :---: | :--- |
| **[Implementation Status & Audit](implementation-status.md)** | `DESIGN` | Comprehensive audit of existing codebase, reuse vs. replace matrix, and progress tracker. |
| **[Testing Strategy & QA Plan](testing-strategy.md)** | `DESIGN` | Testing pyramid (unit, integration, security, citation verification, Playwright E2E). |
| **[Data Consistency & Sync](data-consistency.md)** | `DESIGN` | Dual-store consistency (PostgreSQL + Cognee), outbox relay, and reconciliation worker. |
| **[Threat Model (STRIDE)](threat-model.md)** | `DESIGN` | Threat matrix, prompt injection hardening, polyglot file defenses, and access protections. |
| **[Deployment & Operations Guide](deployment-and-operations.md)** | `DESIGN` | Docker Compose local environment, cloud topology, configuration, and operational runbooks. |
| **[Definition of Done (DoD)](definition-of-done.md)** | `DESIGN` | Strict engineering quality gates and acceptance criteria per phase. |
| **[Development Roadmap](roadmap.md)** | `DESIGN` | 12-week phased implementation plan, P0–P3 priorities, and deployment architecture. |

---

## 🏛️ Architecture Decision Records (ADRs)

Key architectural choices are formally documented in the `docs/decisions/` directory:
* **[ADR-001: Hybrid PostgreSQL and Cognee Architecture](decisions/ADR-001-postgresql-and-cognee-hybrid-storage.md)**: Designating PostgreSQL as the relational source of truth and Cognee as the graph-backed memory accelerator.
* **[ADR-002: Asynchronous Job-Based Document Ingestion](decisions/ADR-002-asynchronous-ingestion-pipeline.md)**: Decoupling HTTP upload acknowledgment from document processing using Celery, Redis, and a Transactional Outbox.
* **[ADR-003: Hybrid Graph-Vector Retrieval for Multi-Hop Inquiries](decisions/ADR-003-hybrid-graph-vector-recall.md)**: Pairing dense vector similarity with knowledge graph traversal for complex intelligence questions.
* **[ADR-004: Versioned Claim Lifecycle and Intelligent Forgetting](decisions/ADR-004-claim-lifecycle-and-intelligent-forgetting.md)**: Preserving contradictory evidence through an append-only event log rather than destructive updates.
* **[ADR-005: Weighted Multi-Attribute Entity Resolution](decisions/ADR-005-weighted-entity-resolution.md)**: Implementing calibrated string, attribute, and token similarity with human-in-the-loop fallback.
* **[ADR-006: Composite Tenancy Foreign Keys](decisions/ADR-006-composite-tenancy-foreign-keys.md)**: Enforcing cross-tenant and cross-case isolation directly at the database engine level.
* **[ADR-007: Claims as Canonical Assertions](decisions/ADR-007-claims-as-canonical-graph-assertions.md)**: Unifying graph relationships and evidence assertions into a single canonical model.

---

## 📊 Benchmarks & Evaluations

* **[Evaluation Framework](benchmarks/evaluation-framework.md)**: 200-question ground-truth benchmark suite, metrics (Recall@5, Precision@5, MRR, nDCG@10, Faithfulness), and test splits.
* **[Performance Targets & SLAs](benchmarks/performance-targets.md)**: Latency budgets (median retrieval $< 500\text{ ms}$, p95 query $< 5\text{ s}$), throughput ($\ge 5\text{ docs/min}$), and SLAs.

---

## 🔄 Core Intelligence Loop

```mermaid
graph LR
    A[Ingest Document] --> B[Extract Entities & Claims]
    B --> C[Entity Resolution]
    C --> D[Graph & Relational Sync]
    D --> E[Hybrid Recall RAG]
    E --> F[Investigator Challenge]
    F --> G[Historical State Update]
    G -.->|Preserved Audited Memory| D
```
