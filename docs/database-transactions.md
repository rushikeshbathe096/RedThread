# RedThread Database Transactions & Concurrency Control

> **Document Status**: `DESIGN`  
> **Role**: Transaction Processing, Concurrency Control, and Isolation Specification  
> **Target Engine**: PostgreSQL 16  
> **Core Principle**: Data integrity and state transitions are enforced strictly by ACID transaction boundaries, deterministic row locking, and optimistic versioning.

---

## 1. ACID Guarantees in RedThread

| ACID Property | Implementation in PostgreSQL 16 | RedThread Production Invariant |
| :--- | :--- | :--- |
| **Atomicity** | Write-Ahead Logging (WAL) and Multi-Version Concurrency Control (MVCC). All DDL and DML statements inside `BEGIN ... COMMIT` execute as an indivisible unit. | Multi-table domain mutations (e.g. creating a Claim and its `claim_sources` and initial `claim_events` entry) either completely commit or roll back to zero state. **No partial state is ever persisted.** |
| **Consistency** | Schema constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK) verified on commit. | Invariants such as composite tenant isolation, non-negative confidences, and valid claim XOR targets are enforced by the database engine. |
| **Isolation** | Snapshot Isolation (SI) and Serializable Snapshot Isolation (SSI). | Transactions execute concurrently without data corruption, lost updates, or write skew. |
| **Durability** | WAL flushed to disk (`fsync=on`) before commit acknowledgment. | Committed evidence, audit logs, and claim states survive hardware restarts and container crashes. |

> [!CAUTION]
> **Long-Running Transaction Invariant**: Never hold a PostgreSQL transaction open while executing an external HTTP call (e.g. calling Google Gemini or Cognee Cloud). LLM extraction and graph synchronization must occur **outside** of transactional locks.

---

## 2. PostgreSQL Isolation Levels Analysis

PostgreSQL does not implement ANSI SQL's lock-based isolation; it implements **Multi-Version Concurrency Control (MVCC)**:

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Serialization Anomalies | Default / Usage in RedThread |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **READ COMMITTED** | Impossible | Possible | Possible | Possible | **Default for standard CRUD**. Each statement sees a snapshot of data committed before that statement began. Fast, no serialization aborts. |
| **REPEATABLE READ** | Impossible | Impossible | Impossible | Possible (Write Skew) | **Used for complex audit queries and frozen report generation**. The entire transaction sees a snapshot frozen at the start of the first query. |
| **SERIALIZABLE** | Impossible | Impossible | Impossible | Impossible | **Used for reversible entity merges**. Employs SIREAD locks to detect dangerous read-write dependency cycles; transactions abort with `40001 serialization_failure` on conflict. |

---

## 3. Concurrency Scenarios & Race Condition Mitigations

### Scenario 1: Two Workers Process the Same Document Simultaneously
- **Risk**: Concurrent workers parse the same document and generate duplicate chunks, entities, and claims.
- **Mitigation**:
  1. Distributed Redis lock on `lock:document:{document_id}` with a 10-minute lease.
  2. Database-level state transition guard:
     ```sql
     UPDATE ingestion_jobs 
     SET status = 'PROCESSING', started_at = NOW() 
     WHERE id = :job_id AND status = 'QUEUED';
     ```
     Only the worker whose update affects exactly `1` row is permitted to proceed; the other worker immediately exits.

### Scenario 2: Two Investigators Merge Entities Concurrently (Deadlock Prevention)
- **Risk**: User 1 merges Entity A $\rightarrow$ Entity B while User 2 merges Entity B $\rightarrow$ Entity A, causing a classic circular deadlock.
- **Mitigation**:
  Pessimistic locking with **deterministic lock ordering** (sorted by UUID):
  ```sql
  -- Always acquire locks in ascending UUID order regardless of which is target or source!
  SELECT id FROM entities 
  WHERE id IN (:entity_a_id, :entity_b_id) 
  ORDER BY id ASC 
  FOR UPDATE;
  ```

### Scenario 3: Two Reviewers Update the Same Claim Concurrently
- **Risk**: Reviewer A upholds Claim #101 while Reviewer B retracts it. The second write silently overwrites the first without knowing of the concurrent decision (Lost Update).
- **Mitigation**:
  **Optimistic Concurrency Control (OCC)** using the `version` column:
  ```sql
  UPDATE claims 
  SET status = :new_status, 
      review_outcome = :new_outcome, 
      version = version + 1, 
      updated_at = NOW() 
  WHERE id = :claim_id AND version = :expected_version;
  ```
  If the row count is `0`, another reviewer has modified the claim. The API rejects the request with HTTP `409 Conflict`, prompting the second reviewer to reload the latest evidence state.

### Scenario 4: Concurrent Uploads of Duplicate Documents
- **Risk**: An investigator rapidly double-clicks "Upload" or two users upload the same PDF to a case.
- **Mitigation**:
  Schema-level unique constraint `uq_case_document_hash (case_id, content_hash)`:
  ```sql
  INSERT INTO documents (case_id, filename, storage_key, content_hash, file_size_bytes, mime_type)
  VALUES (:case_id, :filename, :storage_key, :hash, :size, :mime)
  ON CONFLICT (case_id, content_hash) DO NOTHING
  RETURNING id;
  ```

---

## 4. Transaction Boundaries for Critical Operations

### 4.1 Organization & Admin Creation
- **Isolation Level**: `READ COMMITTED`
- **Operations**:
  ```sql
  BEGIN;
    INSERT INTO organizations (id, name) VALUES (:org_id, :org_name);
    INSERT INTO users (id, email, password_hash, full_name) VALUES (:user_id, :email, :hash, :name);
    INSERT INTO memberships (organization_id, user_id, role) VALUES (:org_id, :user_id, 'ORGANIZATION_ADMIN');
    INSERT INTO audit_logs (organization_id, actor_id, action, resource_type, resource_id) 
    VALUES (:org_id, :user_id, 'ORGANIZATION_CREATED', 'ORGANIZATION', :org_id);
  COMMIT;
  ```

### 4.2 Document Upload Registration (Transactional Outbox)
- **Isolation Level**: `READ COMMITTED`
- **Operations**:
  ```sql
  BEGIN;
    INSERT INTO documents (id, case_id, filename, storage_key, content_hash, file_size_bytes, mime_type)
    VALUES (:doc_id, :case_id, :filename, :s3_key, :hash, :size, :mime);
    
    INSERT INTO ingestion_jobs (id, document_id, status)
    VALUES (:job_id, :doc_id, 'QUEUED');
    
    -- Transactional Outbox Event
    INSERT INTO outbox_events (organization_id, aggregate_type, aggregate_id, event_type, payload)
    VALUES (:org_id, 'DOCUMENT', :doc_id, 'DOCUMENT_INGESTION_REQUESTED', json_build_object(
      'job_id', :job_id, 'document_id', :doc_id, 'case_id', :case_id, 'storage_key', :s3_key
    ));
  COMMIT;
  ```

### 4.3 Ingestion Completion & Evidence Persistence
- **Isolation Level**: `READ COMMITTED`
- **Operations**: Executed after the background worker finishes LLM extraction.
  ```sql
  BEGIN;
    -- 1. Insert Chunks
    INSERT INTO document_chunks (id, document_id, chunk_index, page_number, start_char, end_char, content, token_count)
    VALUES (...);
    
    -- 2. Upsert Entities & Aliases
    INSERT INTO entities (id, organization_id, canonical_name, entity_type) VALUES (...)
    ON CONFLICT (organization_id, canonical_name, entity_type) DO UPDATE SET updated_at = NOW();
    
    INSERT INTO case_entities (case_id, entity_id) VALUES (...) ON CONFLICT DO NOTHING;
    
    -- 3. Insert Claims
    INSERT INTO claims (id, case_id, subject_entity_id, predicate, object_entity_id, object_value, extraction_confidence)
    VALUES (...);
    
    -- 4. Ground Claims in ClaimSources
    INSERT INTO claim_sources (id, claim_id, document_id, case_id, chunk_id, page_number, start_offset, end_offset, quoted_text)
    VALUES (...);
    
    -- 5. Record Creation Event in ClaimEvents
    INSERT INTO claim_events (claim_id, event_type, actor_id, prior_status, new_status, prior_review_outcome, new_review_outcome, reason)
    VALUES (:claim_id, 'CLAIM_CREATED', :system_user_id, NULL, 'ACTIVE', NULL, 'PENDING', 'Extracted via ingestion worker');
    
    -- 6. Mark Job Completed
    UPDATE ingestion_jobs SET status = 'COMPLETED', completed_at = NOW() WHERE id = :job_id;
    UPDATE documents SET status = 'INDEXED' WHERE id = :doc_id;
  COMMIT;
  ```

### 4.4 Entity Merging
- **Isolation Level**: `SERIALIZABLE`
- **Operations**:
  ```sql
  BEGIN;
    -- 1. Deterministic lock acquisition
    SELECT id FROM entities WHERE id IN (:target_id, :source_id) ORDER BY id ASC FOR UPDATE;
    
    -- 2. Snapshot current relationships
    SELECT json_agg(c) INTO :snapshot FROM claims c 
    WHERE subject_entity_id = :source_id OR object_entity_id = :source_id;
    
    -- 3. Record Merge Event
    INSERT INTO entity_merges (organization_id, target_entity_id, source_entity_id, merged_by, reason, snapshot_relationships)
    VALUES (:org_id, :target_id, :source_id, :user_id, :reason, :snapshot);
    
    -- 4. Repoint existing claims to canonical target
    UPDATE claims SET subject_entity_id = :target_id WHERE subject_entity_id = :source_id;
    UPDATE claims SET object_entity_id = :target_id WHERE object_entity_id = :source_id;
    
    -- 5. Repoint aliases
    UPDATE entity_aliases SET entity_id = :target_id WHERE entity_id = :source_id;
    
    -- 6. Soft-delete source entity
    UPDATE entities SET is_active = FALSE, updated_at = NOW() WHERE id = :source_id;
    
    -- 7. Audit Log
    INSERT INTO audit_logs (organization_id, actor_id, action, resource_type, resource_id, details)
    VALUES (:org_id, :user_id, 'ENTITY_MERGED', 'ENTITY', :target_id, json_build_object('source_id', :source_id));
  COMMIT;
  ```

### 4.5 Claim Challenge & Review Lifecycle Operations
- **Isolation Level**: `READ COMMITTED` (with optimistic version lock)
- **Operations (Challenge)**:
  ```sql
  BEGIN;
    UPDATE claims 
    SET status = 'DISPUTED', version = version + 1, updated_at = NOW()
    WHERE id = :claim_id AND version = :expected_version;
    
    -- Verify row count == 1; if 0, raise 409 Conflict
    
    INSERT INTO claim_events (claim_id, event_type, actor_id, prior_status, new_status, prior_review_outcome, new_review_outcome, reason, metadata)
    VALUES (:claim_id, 'CLAIM_CHALLENGED', :user_id, 'ACTIVE', 'DISPUTED', 'PENDING', 'PENDING', :reason, :metadata);
    
    INSERT INTO audit_logs (organization_id, actor_id, action, resource_type, resource_id, case_id)
    VALUES (:org_id, :user_id, 'CLAIM_CHALLENGED', 'CLAIM', :claim_id, :case_id);
  COMMIT;
  ```

---

## 5. Related Documents
- [Database Design Specification](database-design.md)
- [Database Security & RLS](database-security.md)
- [Data Consistency Specification](data-consistency.md)
