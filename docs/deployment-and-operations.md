# RedThread Deployment & Operations Guide

> **Document Status**: `DESIGN`  
> **Topology**: Containerized local development via Docker Compose; scalable cloud deployment across serverless and managed infrastructure.

---

## 1. Local Development Architecture (Docker Compose)

For local development and automated testing, RedThread provides a complete self-contained environment:

```mermaid
flowchart TD
    subgraph Docker Compose Network [redthread-net]
        API[FastAPI Backend :8000]
        Worker[Celery Worker]
        Beat[Celery Beat Scheduler]
        Web[Next.js Frontend :3000]
        PG[(PostgreSQL 16 :5432)]
        Redis[(Redis 7 :6379)]
        MinIO[(MinIO S3 :9000)]
    end
    
    API --> PG
    API --> Redis
    API --> MinIO
    Worker --> PG
    Worker --> Redis
    Worker --> MinIO
    Web --> API
```

### Docker Compose Configuration Outline (`infrastructure/docker-compose.yml`)
- **`postgres`**: `postgres:16-alpine`, exposed on port `5432` with volume `postgres_data`.
- **`redis`**: `redis:7-alpine`, exposed on port `6379`.
- **`minio`**: `minio/minio`, S3-compatible local bucket on `9000` (API) and `9001` (Console).
- **`backend`**: FastAPI application with auto-reloading (`uvicorn --reload`).
- **`worker`**: Celery worker executing `celery -A backend.app.workers.celery_app worker -l INFO -c 4`.
- **`frontend`**: Next.js 15 running in development mode on port `3000`.

---

## 2. Cloud Production Deployment Architecture

```mermaid
flowchart LR
    User([Investigator]) -->|HTTPS| Vercel[Vercel CDN<br/>Next.js 15 Frontend]
    Vercel -->|REST API| RenderAPI[Render / Cloud VM<br/>FastAPI Web Service]
    
    subgraph Managed Cloud Services
        PG[(Neon / Supabase<br/>PostgreSQL 16)]
        RCache[(Upstash / Managed Redis)]
        R2[(Cloudflare R2 / S3<br/>Object Storage)]
    end
    
    RenderAPI --> PG
    RenderAPI --> RCache
    RenderAPI --> R2
    
    RCache --> WorkerHost[Render / Cloud VM<br/>Celery Distributed Workers]
    WorkerHost --> PG
    WorkerHost --> R2
    WorkerHost --> Gemini[Google Gemini API]
    WorkerHost --> Cognee[Cognee Cloud Engine]
```

---

## 3. Environment Configuration (`.env.example`)

```bash
# Application Environment
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=generate_a_secure_256_bit_random_secret_here

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://redthread_user:password@db-host:5432/redthread_db

# Redis
REDIS_URL=redis://redis-host:6379/0

# Object Storage (S3 / Cloudflare R2 / MinIO)
S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=redthread-evidence-vault
S3_REGION=auto

# AI & Graph Engines
GEMINI_API_KEY=your_google_gemini_api_key
COGNEE_API_KEY=your_cognee_api_key

# Security & Tokens
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 4. Operational Runbooks

### 4.1 Ingestion Backlog & Worker Stall Runbook
1. **Symptom**: Ingestion jobs remain in `QUEUED` status; Redis queue length spikes.
2. **Diagnosis**: Check worker process status:
   ```bash
   celery -A backend.app.workers.celery_app inspect active
   ```
3. **Mitigation**:
   - Check Celery logs for unhandled parser crashes or memory exhaustion (OOM).
   - Scale worker replicas or restart stuck workers:
     ```bash
     docker compose restart worker
     ```
   - Stuck jobs with expired leases are automatically reassigned by Celery.

### 4.2 Dead-Letter Queue Inspection & Bulk Reprocessing
1. **Query Dead-Lettered Jobs**:
   ```sql
   SELECT id, document_id, error_code, error_message, updated_at 
   FROM ingestion_jobs WHERE status = 'DEAD_LETTER';
   ```
2. **Re-enqueue via API**:
   ```bash
   curl -X POST https://api.redthread.ai/api/v1/documents/{document_id}/retry \
        -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

### 4.3 Database Backup & Point-in-Time Recovery (PITR)
- **Automated Backups**: Continuous Write-Ahead Log (WAL) archiving enabled in managed PostgreSQL.
- **Manual Snapshot**:
  ```bash
  pg_dump -Fc -h db-host -U redthread_user -d redthread_db > redthread_backup_$(date +%Y%m%d).dump
  ```

---

## 5. Related Documents
- [System Architecture](architecture.md)
- [Testing Strategy](testing-strategy.md)
- [Performance Targets](benchmarks/performance-targets.md)
