# RedThread REST API Specification

**Base URL**: `/api/v1`  
**Protocol**: HTTPS  
**Content-Type**: `application/json` (except file uploads which use `multipart/form-data`)  
**Authentication**: Bearer JWT (`Authorization: Bearer <token>`)

---

## 1. Global Standards & Error Format

### 1.1 Standard Error Response Schema
```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "The requested entity ID was not found in the authorized case scope.",
    "details": {},
    "request_id": "req_88f910a3",
    "timestamp": "2026-11-18T01:45:00Z"
  }
}
```

### 1.2 Pagination Query Parameters
All listing endpoints accept standard offset-based pagination:
* `page` (integer, default: 1): Page number (1-indexed).
* `page_size` (integer, default: 20, max: 100): Number of records per page.

---

## 2. Authentication APIs

### 2.1 Register User
* **Method & Path**: `POST /auth/register`
* **Access**: Public
* **Request Body**:
```json
{
  "email": "investigator@example.com",
  "password": "StrongPassword123!",
  "full_name": "Jane Doe",
  "organization_name": "Special Investigations Unit"
}
```
* **Response (201 Created)**:
```json
{
  "user": {
    "id": "e3b0c442-98fc-1c14-9af0-2a3b9566963f",
    "email": "investigator@example.com",
    "full_name": "Jane Doe"
  },
  "organization": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Special Investigations Unit",
    "role": "ORGANIZATION_ADMIN"
  },
  "access_token": "eyJhbGciOi...",
  "refresh_token": "rt_99e821...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2.2 Login
* **Method & Path**: `POST /auth/login`
* **Request Body**:
```json
{
  "email": "investigator@example.com",
  "password": "StrongPassword123!"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "rt_99e821...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2.3 Refresh Token
* **Method & Path**: `POST /auth/refresh`
* **Request Body**:
```json
{
  "refresh_token": "rt_99e821..."
}
```
* **Response (200 OK)**: New access token and rotated refresh token.

### 2.4 Logout
* **Method & Path**: `POST /auth/logout`
* **Request Body**:
```json
{
  "refresh_token": "rt_99e821..."
}
```
* **Response (200 OK)**: `{"status": "SUCCESS", "message": "Session invalidated"}`

### 2.5 Current User Profile
* **Method & Path**: `GET /auth/me`
* **Response (200 OK)**: User profile, active memberships, and system role.

---

## 3. Organization Management APIs

### 3.1 List Organizations
* **Method & Path**: `GET /organizations`
* **Response (200 OK)**: List of organizations the user is a member of.

### 3.2 Invite Organization Member
* **Method & Path**: `POST /organizations/{id}/members`
* **Required Role**: `ORGANIZATION_ADMIN`
* **Request Body**:
```json
{
  "email": "colleague@example.com",
  "role": "INVESTIGATOR"
}
```
* **Response (201 Created)**: Member invitation details.

### 3.3 Update Member Role
* **Method & Path**: `PATCH /organizations/{id}/members/{user_id}`
* **Request Body**: `{"role": "REVIEWER"}`
* **Response (200 OK)**: Updated membership.

---

## 4. Case Management APIs

### 4.1 Create Case
* **Method & Path**: `POST /cases`
* **Required Role**: `INVESTIGATOR` or `ORGANIZATION_ADMIN`
* **Request Body**:
```json
{
  "case_number": "CASE-2026-001",
  "name": "Financial Network Investigation A",
  "description": "Cross-border transaction trace between Company X and Person B."
}
```
* **Response (201 Created)**: Case entity.

### 4.2 List Authorized Cases
* **Method & Path**: `GET /cases`
* **Query Params**: `status` (ACTIVE, ARCHIVED), `search` (string)
* **Response (200 OK)**: Array of cases accessible to current user.

### 4.3 Get Case Details
* **Method & Path**: `GET /cases/{id}`
* **Response (200 OK)**:
```json
{
  "id": "c1f2e3d4-5678-90ab-cdef-1234567890ab",
  "case_number": "CASE-2026-001",
  "name": "Financial Network Investigation A",
  "status": "ACTIVE",
  "document_count": 48,
  "entity_count": 126,
  "claim_count": 214,
  "disputed_claim_count": 4,
  "assigned_members": [
    {"user_id": "u1", "full_name": "Alice Admin", "role": "ORGANIZATION_ADMIN"},
    {"user_id": "u2", "full_name": "Bob Investigator", "role": "INVESTIGATOR"}
  ],
  "created_at": "2026-11-10T12:00:00Z"
}
```

### 4.4 Archive Case
* **Method & Path**: `DELETE /cases/{id}`
* **Response (200 OK)**: Case marked as `ARCHIVED`.

---

## 5. Document Ingestion APIs

### 5.1 Upload Document
* **Method & Path**: `POST /cases/{id}/documents`
* **Content-Type**: `multipart/form-data`
* **Payload**: Form fields: `file` (Binary), `metadata` (JSON string, optional).
* **Response (202 Accepted)**:
```json
{
  "job_id": "job_3f4a9b8c",
  "document_id": "doc_88f910a3",
  "filename": "suspicious_transfers_q1.pdf",
  "status": "QUEUED",
  "estimated_time_seconds": 15
}
```

### 5.2 Get Ingestion Status
* **Method & Path**: `GET /documents/{id}/status`
* **Response (200 OK)**:
```json
{
  "document_id": "doc_88f910a3",
  "filename": "suspicious_transfers_q1.pdf",
  "status": "PROCESSING",
  "current_stage": "LLM_EXTRACTION",
  "progress_pct": 65,
  "error_message": null
}
```

### 5.3 Retry Failed Processing
* **Method & Path**: `POST /documents/{id}/retry`
* **Response (202 Accepted)**: Reschedules the ingestion job for dead-lettered/failed items.

---

## 6. Intelligence & Graph APIs

### 6.1 Retrieve Case Subgraph
* **Method & Path**: `GET /cases/{id}/graph`
* **Query Params**:
  * `max_depth` (int, default: 2)
  * `entity_id` (UUID, optional seed node)
  * `include_disputed` (boolean, default: true)
  * `min_confidence` (float, default: 0.5)
* **Response (200 OK)**:
```json
{
  "nodes": [
    {
      "id": "ent_101",
      "name": "John Smith",
      "type": "PERSON",
      "disputed_claims_count": 1
    },
    {
      "id": "ent_202",
      "name": "Global Trade Corp",
      "type": "ORGANIZATION",
      "disputed_claims_count": 0
    }
  ],
  "edges": [
    {
      "id": "rel_501",
      "source": "ent_101",
      "target": "ent_202",
      "predicate": "TRANSFERRED_TO",
      "confidence": 0.85,
      "status": "DISPUTED",
      "claim_id": "claim_77"
    }
  ]
}
```

### 6.2 Intelligent Recall (AI Investigation Assistant)
* **Method & Path**: `POST /cases/{id}/recall`
* **Request Body**:
```json
{
  "query": "How is John Smith connected to Person B?",
  "include_disputed": true
}
```
* **Response (200 OK)**:
```json
{
  "answer": "John Smith is connected to Person B through Global Trade Corp and Account AX91, which was used in Transaction T1. However, Note that the transaction between John Smith and Global Trade Corp is currently disputed.",
  "confidence": "moderate",
  "evidence": [
    {
      "claim_id": "claim_101",
      "document_id": "doc_1",
      "document_filename": "wire_transfer_memo.pdf",
      "page": 4,
      "snippet": "John Smith transferred $50,000 to Global Trade Corp through Account AX91."
    },
    {
      "claim_id": "claim_205",
      "document_id": "doc_2",
      "document_filename": "account_audit.pdf",
      "page": 8,
      "snippet": "Account AX91 was used in a transaction involving Person B."
    }
  ],
  "path": [
    "John Smith",
    "Global Trade Corp",
    "Account AX91",
    "Transaction T1",
    "Person B"
  ],
  "warnings": [
    "Claim #101 has an open dispute regarding transaction attribution."
  ]
}
```

### 6.3 Cross-Case Overlap Detection
* **Method & Path**: `GET /cases/{id}/overlaps`
* **Response (200 OK)**:
```json
{
  "overlapping_cases": [
    {
      "case_id": "case_999",
      "case_number": "CASE-2025-084",
      "case_name": "Offshore Holding Probe",
      "shared_entities": [
        {
          "entity_id": "ent_account_ax91",
          "name": "Account AX91",
          "type": "FINANCIAL_ACCOUNT"
        }
      ]
    }
  ]
}
```

### 6.4 Find Relationship Path
* **Method & Path**: `GET /entities/{source_id}/paths/{target_id}`
* **Query Params**: `max_hops` (int, default: 4)
* **Response (200 OK)**: Shortest evidence-supported path between two entities.

---

## 7. Evidence & Claim Lifecycle APIs

### 7.1 Challenge a Claim
* **Method & Path**: `POST /claims/{id}/challenge`
* **Required Role**: `INVESTIGATOR`, `REVIEWER`, or `ORGANIZATION_ADMIN`
* **Request Body**:
```json
{
  "reason": "Document 2 (page 12) proves that the wire transfer was initiated by an unauthorized proxy, not John Smith directly.",
  "counter_document_id": "doc_99b"
}
```
* **Response (200 OK)**:
```json
{
  "claim_id": "claim_101",
  "status": "DISPUTED",
  "updated_at": "2026-11-18T01:46:00Z"
}
```

### 7.2 Review and Retract / Reinstate Claim
* **Method & Path**: `POST /claims/{id}/review`
* **Request Body**:
```json
{
  "decision": "RETRACT",
  "notes": "Evidence from forensic audit supersedes initial field report."
}
```
* **Response (200 OK)**: Updated claim status (`RETRACTED`).

### 7.3 Get Claim Audit History
* **Method & Path**: `GET /claims/{id}/history`
* **Response (200 OK)**: Chronological list of events (`CLAIM_CREATED`, `CLAIM_CHALLENGED`, `CLAIM_REVIEWED`).

---

## 8. Analytics & Audit APIs

### 8.1 Organization Overview Metrics
* **Method & Path**: `GET /analytics/overview`
* **Response (200 OK)**:
```json
{
  "total_documents": 542,
  "total_entities": 1890,
  "total_claims": 4120,
  "disputed_claims": 27,
  "ingestion_failure_rate": 0.012,
  "active_cases": 14
}
```

### 8.2 Audit Log Inspection
* **Method & Path**: `GET /audit-logs`
* **Query Params**: `case_id`, `actor_id`, `action`, `from_date`, `to_date`
* **Response (200 OK)**: Paginated audit records.
