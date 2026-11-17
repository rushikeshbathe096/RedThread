from backend.app.db.base import Base

# Import all feature module models to ensure Base.metadata is fully populated for Alembic & DB reflection
from backend.app.modules.auth.models import User
from backend.app.modules.organizations.models import Organization, Membership
from backend.app.modules.cases.models import Case, CaseMember, CaseEntity
from backend.app.modules.documents.models import Document, DocumentChunk, IngestionJob
from backend.app.modules.entities.models import Entity, EntityAlias, EntityMergeEvent
from backend.app.modules.contradictions.models import (
    Claim,
    ClaimSource,
    ClaimVersion,
    ClaimEvent,
)
from backend.app.modules.reports.models import OutboxEvent, AuditLog, Report

__all__ = [
    "Base",
    "User",
    "Organization",
    "Membership",
    "Case",
    "CaseMember",
    "CaseEntity",
    "Document",
    "DocumentChunk",
    "IngestionJob",
    "Entity",
    "EntityAlias",
    "EntityMergeEvent",
    "Claim",
    "ClaimSource",
    "ClaimVersion",
    "ClaimEvent",
    "OutboxEvent",
    "AuditLog",
    "Report",
]
