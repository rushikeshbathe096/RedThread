import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.enums import ClaimEventType, ClaimStatus, ClaimType, ReviewOutcome


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "case_id"],
            ["cases.organization_id", "cases.id"],
            ondelete="RESTRICT",
            name="fk_claim_case_org",
        ),
        ForeignKeyConstraint(
            ["organization_id", "subject_entity_id"],
            ["entities.organization_id", "entities.id"],
            ondelete="RESTRICT",
            name="fk_claim_subject_org",
        ),
        ForeignKeyConstraint(
            ["organization_id", "object_entity_id"],
            ["entities.organization_id", "entities.id"],
            ondelete="RESTRICT",
            name="fk_claim_object_org",
        ),
        UniqueConstraint("case_id", "id", name="uq_claim_case"),
        CheckConstraint(
            "(claim_type = 'ENTITY_TO_ENTITY' AND object_entity_id IS NOT NULL AND object_value IS NULL) OR "
            "(claim_type = 'ENTITY_TO_LITERAL' AND object_entity_id IS NULL AND object_value IS NOT NULL)",
            name="chk_claim_target_exclusivity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    predicate: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim_type: Mapped[ClaimType] = mapped_column(
        SQLEnum(ClaimType, name="claim_type"), nullable=False
    )
    object_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    object_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualifiers: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_negated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        SQLEnum(ClaimStatus, name="claim_status"),
        nullable=False,
        default=ClaimStatus.ACTIVE,
        index=True,
    )
    review_outcome: Mapped[ReviewOutcome] = mapped_column(
        SQLEnum(ReviewOutcome, name="review_outcome"),
        nullable=False,
        default=ReviewOutcome.PENDING,
        index=True,
    )
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="claims")
    subject_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[subject_entity_id])
    object_entity: Mapped[Optional["Entity"]] = relationship("Entity", foreign_keys=[object_entity_id])
    sources: Mapped[List["ClaimSource"]] = relationship(
        "ClaimSource", back_populates="claim", cascade="all, delete-orphan"
    )
    versions: Mapped[List["ClaimVersion"]] = relationship(
        "ClaimVersion", back_populates="claim", cascade="all, delete-orphan"
    )
    events: Mapped[List["ClaimEvent"]] = relationship(
        "ClaimEvent", back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimSource(Base):
    __tablename__ = "claim_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "claim_id"],
            ["claims.case_id", "claims.id"],
            ondelete="RESTRICT",
            name="fk_claim_source_claim_case",
        ),
        ForeignKeyConstraint(
            ["case_id", "document_id"],
            ["documents.case_id", "documents.id"],
            ondelete="RESTRICT",
            name="fk_claim_source_doc_case",
        ),
        ForeignKeyConstraint(
            ["document_id", "chunk_id"],
            ["document_chunks.document_id", "document_chunks.id"],
            ondelete="RESTRICT",
            name="fk_claim_source_chunk",
        ),
        UniqueConstraint(
            "claim_id", "document_id", "doc_start_offset", "doc_end_offset",
            name="uq_claim_source_span",
        ),
        CheckConstraint(
            "doc_start_offset >= 0 AND doc_end_offset > doc_start_offset",
            name="chk_doc_offsets_valid",
        ),
        CheckConstraint(
            "chunk_local_start_offset IS NULL OR "
            "(chunk_local_start_offset >= 0 AND chunk_local_end_offset > chunk_local_start_offset)",
            name="chk_chunk_offsets_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    doc_start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    doc_end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_local_start_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_local_end_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quoted_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="sources")
    document: Mapped["Document"] = relationship("Document", overlaps="claim,sources")
    chunk: Mapped[Optional["DocumentChunk"]] = relationship("DocumentChunk", overlaps="document")


class ClaimVersion(Base):
    __tablename__ = "claim_versions"
    __table_args__ = (
        UniqueConstraint("claim_id", "version", name="uq_claim_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    predicate: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_type: Mapped[ClaimType] = mapped_column(
        SQLEnum(ClaimType, name="claim_type"), nullable=False
    )
    object_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    object_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualifiers: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_negated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(
        SQLEnum(ClaimStatus, name="claim_status"), nullable=False
    )
    review_outcome: Mapped[ReviewOutcome] = mapped_column(
        SQLEnum(ReviewOutcome, name="review_outcome"), nullable=False
    )
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="versions")
    actor: Mapped["User"] = relationship("User")


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ClaimEventType] = mapped_column(
        SQLEnum(ClaimEventType, name="claim_event_type"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    prior_status: Mapped[Optional[ClaimStatus]] = mapped_column(
        SQLEnum(ClaimStatus, name="claim_status"), nullable=True
    )
    new_status: Mapped[ClaimStatus] = mapped_column(
        SQLEnum(ClaimStatus, name="claim_status"), nullable=False
    )
    prior_review_outcome: Mapped[Optional[ReviewOutcome]] = mapped_column(
        SQLEnum(ReviewOutcome, name="review_outcome"), nullable=True
    )
    new_review_outcome: Mapped[ReviewOutcome] = mapped_column(
        SQLEnum(ReviewOutcome, name="review_outcome"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="events")
    actor: Mapped["User"] = relationship("User")
