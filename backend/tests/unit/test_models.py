import uuid
import pytest
from backend.app.db.all_models import (
    Base,
    Organization,
    User,
    Membership,
    Case,
    Document,
    DocumentChunk,
    Entity,
    Claim,
    ClaimSource,
    OutboxEvent,
)
from backend.app.db.enums import (
    CaseStatus,
    ClaimEventType,
    ClaimStatus,
    ClaimType,
    DocumentType,
    EntityType,
    IngestionStatus,
    OrgRole,
    OutboxStatus,
    ReviewOutcome,
)


def test_all_19_tables_registered_in_metadata():
    tables = list(Base.metadata.tables.keys())
    assert len(tables) == 19
    expected_tables = {
        "organizations", "users", "memberships", "cases", "case_members",
        "documents", "document_chunks", "ingestion_jobs", "entities",
        "entity_aliases", "entity_merge_events", "case_entities", "claims",
        "claim_sources", "claim_versions", "claim_events", "outbox_events",
        "audit_logs", "reports",
    }
    assert expected_tables == set(tables)


def test_entity_model_instantiation():
    org_id = uuid.uuid4()
    entity = Entity(
        organization_id=org_id,
        canonical_name="Acme Corporation",
        entity_type=EntityType.ORGANIZATION,
        metadata_={"country": "US"},
        is_active=True,
    )
    assert entity.canonical_name == "Acme Corporation"
    assert entity.entity_type == EntityType.ORGANIZATION
    assert entity.merged_into_id is None


def test_claim_model_instantiation():
    org_id = uuid.uuid4()
    case_id = uuid.uuid4()
    subj_id = uuid.uuid4()
    obj_id = uuid.uuid4()
    claim = Claim(
        organization_id=org_id,
        case_id=case_id,
        subject_entity_id=subj_id,
        predicate="TRANSFERRED_TO",
        claim_type=ClaimType.ENTITY_TO_ENTITY,
        object_entity_id=obj_id,
        qualifiers={"amount": 50000, "currency": "USD"},
        status=ClaimStatus.ACTIVE,
        review_outcome=ReviewOutcome.PENDING,
        extraction_confidence=0.95,
    )
    assert claim.claim_type == ClaimType.ENTITY_TO_ENTITY
    assert claim.status == ClaimStatus.ACTIVE
    assert claim.review_outcome == ReviewOutcome.PENDING
    assert claim.qualifiers["amount"] == 50000


def test_outbox_event_model_instantiation():
    org_id = uuid.uuid4()
    event = OutboxEvent(
        organization_id=org_id,
        aggregate_type="DOCUMENT",
        aggregate_id=uuid.uuid4(),
        aggregate_version=1,
        event_type="DOCUMENT_UPLOADED",
        payload={"filename": "report.pdf"},
        status=OutboxStatus.PENDING,
    )
    assert event.aggregate_type == "DOCUMENT"
    assert event.status == OutboxStatus.PENDING
