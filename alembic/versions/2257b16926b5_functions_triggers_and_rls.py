"""functions_triggers_and_rls

Revision ID: 2257b16926b5
Revises: 1156a05815a4
Create Date: 2026-11-18 03:17:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2257b16926b5'
down_revision: Union[str, Sequence[str], None] = '1156a05815a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')

    # 2. GIN Trigram & JSONB Indexes
    op.execute('CREATE INDEX IF NOT EXISTS idx_entities_trgm ON entities USING GIN (canonical_name gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_entity_aliases_trgm ON entity_aliases USING GIN (alias gin_trgm_ops);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_entities_metadata ON entities USING GIN (metadata jsonb_path_ops);')
    op.execute("CREATE INDEX IF NOT EXISTS idx_outbox_pending_dispatch ON outbox_events(status, next_retry_at, created_at) WHERE status = 'PENDING';")

    # 3. Security Helper Schema & Functions
    op.execute("CREATE SCHEMA IF NOT EXISTS app;")
    op.execute("""
    CREATE OR REPLACE FUNCTION app.current_org_id()
    RETURNS UUID AS $$
    BEGIN
        RETURN NULLIF(current_setting('app.current_org_id', true), '')::UUID;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION app.current_user_id()
    RETURNS UUID AS $$
    BEGIN
        RETURN NULLIF(current_setting('app.current_user_id', true), '')::UUID;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION app.is_authenticated_org_member()
    RETURNS BOOLEAN AS $$
    DECLARE
        v_org_id UUID;
        v_user_id UUID;
    BEGIN
        v_org_id := app.current_org_id();
        v_user_id := app.current_user_id();
        IF v_org_id IS NULL OR v_user_id IS NULL THEN
            RETURN FALSE;
        END IF;

        RETURN EXISTS (
            SELECT 1 FROM public.memberships m 
            JOIN public.users u ON u.id = m.user_id
            WHERE m.organization_id = v_org_id 
              AND m.user_id = v_user_id
              AND u.is_active = TRUE
        );
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION app.has_case_access(p_case_id UUID, p_min_role org_role DEFAULT 'VIEWER')
    RETURNS BOOLEAN AS $$
    DECLARE
        v_org_id UUID;
        v_user_id UUID;
        v_user_role org_role;
        v_is_worker BOOLEAN;
    BEGIN
        v_is_worker := COALESCE(NULLIF(current_setting('app.is_worker', true), '')::BOOLEAN, false);
        IF v_is_worker THEN
            RETURN TRUE;
        END IF;

        v_org_id := app.current_org_id();
        v_user_id := app.current_user_id();

        IF v_org_id IS NULL OR v_user_id IS NULL THEN
            RETURN FALSE;
        END IF;

        -- Check organizational role first
        SELECT m.role INTO v_user_role
        FROM public.memberships m
        WHERE m.organization_id = v_org_id AND m.user_id = v_user_id;

        IF v_user_role IS NULL THEN
            RETURN FALSE;
        END IF;

        -- Organization Admin has unrestricted access to all cases in the organization
        IF v_user_role = 'ORGANIZATION_ADMIN' THEN
            RETURN EXISTS (SELECT 1 FROM public.cases WHERE id = p_case_id AND organization_id = v_org_id);
        END IF;

        -- Verify case belongs to active organization
        IF NOT EXISTS (SELECT 1 FROM public.cases WHERE id = p_case_id AND organization_id = v_org_id) THEN
            RETURN FALSE;
        END IF;

        -- Case-level permission verification
        RETURN EXISTS (
            SELECT 1 FROM public.case_members cm
            WHERE cm.case_id = p_case_id 
              AND cm.user_id = v_user_id
              AND (
                  p_min_role = 'VIEWER' OR
                  (p_min_role = 'REVIEWER' AND cm.role IN ('ORGANIZATION_ADMIN', 'INVESTIGATOR', 'REVIEWER')) OR
                  (p_min_role = 'INVESTIGATOR' AND cm.role IN ('ORGANIZATION_ADMIN', 'INVESTIGATOR')) OR
                  (p_min_role = 'ORGANIZATION_ADMIN' AND cm.role = 'ORGANIZATION_ADMIN')
              )
        );
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER STABLE;
    """)

    # 4. Entity Merge Cycle Prevention Trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_check_entity_merge_cycle()
    RETURNS TRIGGER AS $$
    DECLARE
        v_curr UUID := NEW.merged_into_id;
        v_depth INT := 0;
    BEGIN
        IF NEW.merged_into_id IS NULL THEN
            RETURN NEW;
        END IF;
        
        IF NEW.merged_into_id = NEW.id THEN
            RAISE EXCEPTION 'Entity % cannot be merged into itself', NEW.id;
        END IF;

        WHILE v_curr IS NOT NULL LOOP
            IF v_curr = NEW.id THEN
                RAISE EXCEPTION 'Merge cycle detected: entity % is already an ancestor of %', NEW.id, NEW.merged_into_id;
            END IF;
            
            v_depth := v_depth + 1;
            IF v_depth > 20 THEN
                RAISE EXCEPTION 'Merge chain depth exceeded limit (20) for entity %', NEW.id;
            END IF;
            
            SELECT merged_into_id INTO v_curr FROM entities WHERE id = v_curr;
        END LOOP;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("DROP TRIGGER IF EXISTS trg_prevent_entity_merge_cycles ON entities;")
    op.execute("""
    CREATE TRIGGER trg_prevent_entity_merge_cycles
    BEFORE INSERT OR UPDATE OF merged_into_id ON entities
    FOR EACH ROW
    EXECUTE FUNCTION fn_check_entity_merge_cycle();
    """)

    # 5. Recursive Canonical Resolution Function & View
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_get_canonical_entity_id(p_entity_id UUID)
    RETURNS UUID AS $$
    DECLARE
        v_current UUID := p_entity_id;
        v_next UUID;
        v_depth INT := 0;
    BEGIN
        LOOP
            SELECT merged_into_id INTO v_next FROM entities WHERE id = v_current;
            IF v_next IS NULL OR v_next = v_current THEN
                RETURN v_current;
            END IF;
            v_current := v_next;
            v_depth := v_depth + 1;
            IF v_depth > 20 THEN
                RAISE EXCEPTION 'Merge chain depth exceeded limit (20) for entity %', p_entity_id;
            END IF;
        END LOOP;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
    CREATE OR REPLACE VIEW vw_canonical_entities AS
    WITH RECURSIVE entity_chain AS (
        SELECT id AS original_id, id AS canonical_id, merged_into_id, 0 AS depth
        FROM entities
        UNION ALL
        SELECT ec.original_id, e.id AS canonical_id, e.merged_into_id, ec.depth + 1
        FROM entity_chain ec
        JOIN entities e ON ec.merged_into_id = e.id
        WHERE ec.merged_into_id IS NOT NULL AND ec.depth < 20
    )
    SELECT original_id, canonical_id
    FROM entity_chain
    WHERE merged_into_id IS NULL;
    """)

    # 6. Chunk Offset Coordinate Alignment Trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_validate_claim_source_chunk_offsets()
    RETURNS TRIGGER AS $$
    DECLARE
        v_chunk_start INT;
        v_chunk_end INT;
    BEGIN
        IF NEW.chunk_id IS NOT NULL THEN
            SELECT start_char, end_char INTO v_chunk_start, v_chunk_end
            FROM document_chunks
            WHERE id = NEW.chunk_id;
            
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Referenced chunk % does not exist', NEW.chunk_id;
            END IF;
            
            IF NEW.doc_start_offset < v_chunk_start OR NEW.doc_end_offset > v_chunk_end THEN
                RAISE EXCEPTION 'Claim citation offsets [%, %] exceed chunk boundaries [%, %]', 
                    NEW.doc_start_offset, NEW.doc_end_offset, v_chunk_start, v_chunk_end;
            END IF;
            
            IF NEW.chunk_local_start_offset IS NOT NULL AND NEW.chunk_local_end_offset IS NOT NULL THEN
                IF NEW.chunk_local_start_offset <> (NEW.doc_start_offset - v_chunk_start) OR
                   NEW.chunk_local_end_offset <> (NEW.doc_end_offset - v_chunk_start) THEN
                    RAISE EXCEPTION 'Chunk-local offsets [%, %] do not match relative position within chunk [%, %]',
                        NEW.chunk_local_start_offset, NEW.chunk_local_end_offset,
                        v_chunk_start, v_chunk_end;
                END IF;
            END IF;
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("DROP TRIGGER IF EXISTS trg_validate_claim_source_chunk_offsets ON claim_sources;")
    op.execute("""
    CREATE TRIGGER trg_validate_claim_source_chunk_offsets
    BEFORE INSERT OR UPDATE ON claim_sources
    FOR EACH ROW
    EXECUTE FUNCTION fn_validate_claim_source_chunk_offsets();
    """)

    # 7. Enable & Force Row-Level Security on All Tables
    tables = [
        "organizations", "memberships", "cases", "case_members",
        "documents", "document_chunks", "ingestion_jobs", "entities",
        "entity_aliases", "entity_merge_events", "case_entities", "claims",
        "claim_sources", "claim_versions", "claim_events", "outbox_events",
        "audit_logs", "reports",
    ]
    for tbl in tables:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY;")

    # 8. Define RLS Policies
    op.execute("""
    CREATE POLICY rls_org_select ON organizations FOR SELECT
    USING (id = app.current_org_id() AND app.is_authenticated_org_member());
    """)

    op.execute("""
    CREATE POLICY rls_mem_select ON memberships FOR SELECT
    USING (organization_id = app.current_org_id() AND app.is_authenticated_org_member());
    """)

    op.execute("""
    CREATE POLICY rls_cases_select ON cases FOR SELECT
    USING (organization_id = app.current_org_id() AND app.has_case_access(id));
    """)

    op.execute("""
    CREATE POLICY rls_doc_select ON documents FOR SELECT
    USING (app.has_case_access(case_id));
    """)

    op.execute("""
    CREATE POLICY rls_entities_select ON entities FOR SELECT
    USING (organization_id = app.current_org_id() AND app.is_authenticated_org_member());
    """)

    op.execute("""
    CREATE POLICY rls_claims_select ON claims FOR SELECT
    USING (organization_id = app.current_org_id() AND app.has_case_access(case_id));
    """)

    op.execute("""
    CREATE POLICY rls_claim_sources_select ON claim_sources FOR SELECT
    USING (app.has_case_access(case_id));
    """)


def downgrade() -> None:
    tables = [
        "organizations", "memberships", "cases", "case_members",
        "documents", "document_chunks", "ingestion_jobs", "entities",
        "entity_aliases", "entity_merge_events", "case_entities", "claims",
        "claim_sources", "claim_versions", "claim_events", "outbox_events",
        "audit_logs", "reports",
    ]
    for tbl in tables:
        op.execute(f"ALTER TABLE {tbl} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP TRIGGER IF EXISTS trg_validate_claim_source_chunk_offsets ON claim_sources;")
    op.execute("DROP FUNCTION IF EXISTS fn_validate_claim_source_chunk_offsets();")
    op.execute("DROP VIEW IF EXISTS vw_canonical_entities;")
    op.execute("DROP FUNCTION IF EXISTS fn_get_canonical_entity_id(UUID);")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_entity_merge_cycles ON entities;")
    op.execute("DROP FUNCTION IF EXISTS fn_check_entity_merge_cycle();")
    op.execute("DROP FUNCTION IF EXISTS app.has_case_access(UUID, org_role);")
    op.execute("DROP FUNCTION IF EXISTS app.is_authenticated_org_member();")
    op.execute("DROP FUNCTION IF EXISTS app.current_user_id();")
    op.execute("DROP FUNCTION IF EXISTS app.current_org_id();")
    op.execute("DROP SCHEMA IF EXISTS app CASCADE;")
