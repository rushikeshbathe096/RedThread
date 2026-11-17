# RedThread REST API Specification

> **Document Status**: `DESIGN`  
> **Base URL**: `/api/v1`  
> **Protocol**: HTTPS  
> **Content-Type**: `application/json` (except document uploads: `multipart/form-data`)  
> **Authentication**: Bearer JWT (`Authorization: Bearer <token>`)

---

## 1. Global Standards, Errors & Pagination

### 1.1 Error Response Contract
```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "The requested entity was not found in the authorized case scope.",
    "details": {},
    "request_id": "req_88f910a3",
    "timestamp": "2026-11-18T02:00:00Z"
  }
}
```

### 1.2 Pagination Parameters
List endpoints support standard pagination:
- `page` (integer, default: 1, minimum: 1)
- `page_size` (integer, default: 20, minimum: 1, maximum: 100)

---

## 2. Authentication & Identity APIs

### 2.1 Register User
- **Method & Path**: `POST /auth/register`
- **Access**: Public
- **Request Body**:
```json
{
  "email": "investigator@example.com",
  "password": "CorrectHorseBatteryStaple123!",
  "full_name": "Jane Doe",
  "organization_name": "Forensic Intelligence Unit"
}
```
- **Response (201 Created)**:
```json
{
  "user": {
    "id": "e3b0c442-98fc-1c14-9af0-2a3b9566963f",
    "email": "investigator@example.com",
    "full_name": "Jane Doe"
  },
  "organization": {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "Forensic Intelligence Unit",
    "role": "ORGANIZATION_ADMIN"
  },
  "access_token": "eyJhbGciOi...",
  "refresh_token": "rt_99e821...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2.2 Login
- **Method & Path**: `POST /auth/login`
- **Access**: Public
- **Request Body**: `{"email": "investigator@example.com", "password": "..."}`
- **Response (200 OK)**: `{"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900}`

### 2.3 Refresh Token Rotation
- **Method & Path**: `POST /auth/refresh`
- **Request Body**: `{"refresh_token": "rt_99e821..."}`
- **Response (200 OK)**: New access token and rotated refresh token.

### 2.4 Logout
- **Method & Path**: `POST /auth/logout`
- **Request Body**: `{"refresh_token": "rt_99e821..."}`
- **Response (200 OK)**: `{"status": "SUCCESS", "message": "Session invalidated"}`

### 2.5 Current User Profile
- **Method & Path**: `GET /auth/me`
- **Response (200 OK)**: User profile, active memberships, and organization permissions.

---

## 3. Organization Management APIs

### 3.1 List Organizations
- **Method & Path**: `GET /organizations`
- **Response (200 OK)**: Array of organizations the user belongs to.

### 3.2 Invite Organization Member
- **Method & Path**: `POST /organizations/{id}/members`
- **Required Role**: `ORGANIZATION_ADMIN`
- **Request Body**: `{"email": "analyst@example.com", "role": "INVESTIGATOR"}`
- **Response (201 Created)**: Membership invitation details.

### 3.3 Update Member Role
- **Method & Path**: `PATCH /organizations/{id}/members/{user_id}`
- **Required Role**: `ORGANIZATION_ADMIN`
- **Request Body**: `{"role": "REVIEWER"}`
- **Response (200 OK)**: Updated membership.

---

## 4. Case Management APIs

### 4.1 Create Case
- **Method & Path**: `POST /cases`
- **Required Role**: `INVESTIGATOR` or `ORGANIZATION_ADMIN`
- **Request Body**:
```json
{
  "case_number": "CASE-2026-001",
  "name": "Financial Network Probe",
  "description": "Multi-jurisdictional shell company transaction analysis."
}
```
- **Response (201 Created)**: Created case record.

### 4.2 List Cases
- **Method & Path**: `GET /cases`
- **Query Params**: `status` (`ACTIVE`, `ARCHIVED`, `CLOSED`), `search` (string)
- **Response (200 OK)**: Paginated array of authorized cases.

### 4.3 Get Case Details
- **Method & Path**: `GET /cases/{id}`
- **Response (200 OK)**:
```json
{
  "id": "c1f2e3d4-5678-90ab-cdef-1234567890ab",
  "case_number": "CASE-2026-001",
  "name": "Financial Network Probe",
  "status": "ACTIVE",
  "document_count": 48,
  "entity_count": 126,
  "claim_count": 214,
  "disputed_claim_count": 3,
  "created_at": "2026-11-10T12:00:00Z"
}
```

### 4.4 Archive Case
- **Method & Path**: `DELETE /cases/{id}`
- **Required Role**: `ORGANIZATION_ADMIN`
- **Response (200 OK)**: Case marked as `ARCHIVED`.

---

## 5. Document Ingestion APIs

### 5.1 Upload Document
- **Method & Path**: `POST /cases/{id}/documents`
- **Content-Type**: `multipart/form-data`
- **Payload**: `file` (Binary), `metadata` (JSON string, optional)
- **Response (202 Accepted)**:
```json
{
  "job_id": "job_3f4a9b8c",
  "document_id": "doc_88f910a3",
  "filename": "wire_transfers.pdf",
  "status": "QUEUED"
}
```

### 5.2 Get Ingestion Status
- **Method & Path**: `GET /documents/{id}/status`
- **Response (200 OK)**:
```json
{
  "document_id": "doc_88f910a3",
  "filename": "wire_transfers.pdf",
  "status": "PROCESSING",
  "attempt_count": 1,
  "error_message": null
}
```

### 5.3 Retry Ingestion Job
- **Method & Path**: `POST /documents/{id}/retry`
- **Response (202 Accepted)**: Re-enqueues a `FAILED` or `DEAD_LETTER` ingestion task.

---

## 6. Entity & Entity Resolution APIs

### 6.1 List Case Entities
- **Method & Path**: `GET /cases/{id}/entities`
- **Query Params**: `entity_type`, `search`, `page`, `page_size`
- **Response (200 OK)**: Paginated entity records.

### 6.2 Get Entity Details & Aliases
- **Method & Path**: `GET /entities/{id}`
- **Response (200 OK)**: Canonical entity details, aliases list, and co-occurrence statistics.

### 6.3 Merge Entities
- **Method & Path**: `POST /entities/{id}/merge`
- **Required Role**: `INVESTIGATOR` or `ORGANIZATION_ADMIN`
- **Request Body**:
```json
{
  "subsumed_entity_id": "ent_99a8b7c6",
  "reason": "Corporate filing demonstrates TCS is the recognized alias for Tata Consultancy Services."
}
```
- **Response (200 OK)**:
```json
{
  "merge_id": "merge_33a1b2c4",
  "canonical_target_id": "ent_canonical_uuid",
  "subsumed_source_id": "ent_99a8b7c6",
  "status": "MERGED"
}
```

### 6.4 Unmerge Entities
- **Method & Path**: `POST /entities/{id}/unmerge`
- **Required Role**: `INVESTIGATOR` or `ORGANIZATION_ADMIN`
- **Request Body**: `{"source_entity_id": "ent_99a8b7c6"}`
- **Response (200 OK)**:
```json
{
  "restored_entity_id": "ent_99a8b7c6",
  "status": "RESTORED",
  "unmerged_at": "2026-11-18T02:30:00Z"
}
```

---

## 7. Knowledge Graph & Recall APIs

### 7.1 Retrieve Subgraph
- **Method & Path**: `GET /cases/{id}/graph`
- **Query Params**: `seed_entity_id`, `max_depth` (default: 2), `include_disputed` (default: true)
- **Response (200 OK)**:
```json
{
  "nodes": [
    {"id": "ent_1", "label": "John Smith", "type": "PERSON", "disputed": false},
    {"id": "ent_2", "label": "Global Trade Corp", "type": "ORGANIZATION", "disputed": true}
  ],
  "edges": [
    {
      "id": "claim_101",
      "source": "ent_1",
      "target": "ent_2",
      "predicate": "TRANSFERRED_TO",
      "claim_type": "ENTITY_TO_ENTITY",
      "qualifiers": {"amount": 50000, "currency": "USD"},
      "is_negated": false,
      "status": "DISPUTED",
      "review_outcome": "PENDING",
      "confidence": 0.95
    }
  ]
}
```

### 7.2 Intelligent Recall (AI Investigation Assistant)
- **Method & Path**: `POST /cases/{id}/recall`
- **Request Body**:
```json
{
  "query": "How is John Smith connected to Person B?",
  "include_disputed": true
}
```
- **Response (200 OK)**:
```json
{
  "answer": "John Smith is connected to Person B through Global Trade Corp and Account AX91 [Claim #101, #142, #205]. However, Claim #101 is currently disputed.",
  "confidence": "moderate",
  "evidence": [
    {
      "claim_id": "claim_101",
      "document_id": "doc_1",
      "document_filename": "wire_memo.pdf",
      "page": 4,
      "doc_start_offset": 1240,
      "doc_end_offset": 1342,
      "snippet": "John Smith transferred $50,000 to Global Trade Corp through Account AX91."
    }
  ],
  "path": ["John Smith", "Global Trade Corp", "Account AX91", "Person B"],
  "warnings": ["Claim #101 is marked DISPUTED."]
}
```

---

## 8. Claim Lifecycle & Evidence APIs

### 8.1 Challenge a Claim
- **Method & Path**: `POST /claims/{id}/challenge`
- **Required Role**: `INVESTIGATOR`, `REVIEWER`, or `ORGANIZATION_ADMIN`
- **Request Body**:
```json
{
  "reason": "Doc #45 proves credentials compromised before transfer.",
  "counter_document_id": "doc_45",
  "expected_version": 1
}
```
- **Response (200 OK)**: Claim status updated to `DISPUTED` with incremented version.

### 8.2 Review Claim
- **Method & Path**: `POST /claims/{id}/review`
- **Required Role**: `REVIEWER` or `ORGANIZATION_ADMIN`
- **Request Body**:
```json
{
  "review_outcome": "REJECTED",
  "reason": "Forensic audit debunked attribution.",
  "expected_version": 2
}
```
- **Response (200 OK)**: Claim status updated to `RETRACTED` and review outcome set to `REJECTED`.

### 8.3 Get Claim History & Versions
- **Method & Path**: `GET /claims/{id}/history`
- **Response (200 OK)**:
```json
{
  "claim_id": "claim_101",
  "current_version": 3,
  "versions": [
    {
      "version": 1,
      "status": "ACTIVE",
      "review_outcome": "PENDING",
      "change_reason": "Initial extraction",
      "created_at": "2026-11-10T12:00:00Z"
    },
    {
      "version": 2,
      "status": "DISPUTED",
      "review_outcome": "PENDING",
      "change_reason": "Investigator challenge",
      "created_at": "2026-11-12T14:30:00Z"
    },
    {
      "version": 3,
      "status": "RETRACTED",
      "review_outcome": "REJECTED",
      "change_reason": "Forensic audit debunked attribution",
      "created_at": "2026-11-15T09:15:00Z"
    }
  ],
  "events": [...]
}
```

---

## 9. Reports & Audit APIs

### 9.1 Generate Evidentiary Report
- **Method & Path**: `POST /cases/{id}/reports`
- **Request Body**: `{"format": "PDF", "include_graph": true, "include_audit_history": true}`
- **Response (201 Created)**: Frozen report artifact metadata with download URL.

### 9.2 Inspect Audit Logs
- **Method & Path**: `GET /audit-logs`
- **Query Params**: `case_id`, `actor_id`, `action`, `page`, `page_size`
- **Response (200 OK)**: Paginated audit event records.
