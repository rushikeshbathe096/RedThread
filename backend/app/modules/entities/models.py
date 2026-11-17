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
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.enums import EntityType


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("organization_id", "canonical_name", "entity_type", name="uq_org_entity_name_type"),
        UniqueConstraint("organization_id", "id", name="uq_entity_org"),
        CheckConstraint("merged_into_id <> id", name="chk_prevent_self_merge_pointer"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType, name="entity_type"), nullable=False, index=True
    )
    merged_into_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization")
    merged_into: Mapped[Optional["Entity"]] = relationship(
        "Entity", remote_side=[id], foreign_keys=[merged_into_id]
    )
    aliases: Mapped[List["EntityAlias"]] = relationship(
        "EntityAlias", back_populates="entity", cascade="all, delete-orphan"
    )


class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    __table_args__ = (
        UniqueConstraint("entity_id", "alias", name="uq_entity_alias"),
        ForeignKeyConstraint(
            ["organization_id", "entity_id"],
            ["entities.organization_id", "entities.id"],
            ondelete="CASCADE",
            name="fk_alias_entity_org",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="INGESTION")
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    entity: Mapped["Entity"] = relationship("Entity", back_populates="aliases")


class EntityMergeEvent(Base):
    __tablename__ = "entity_merge_events"
    __table_args__ = (
        CheckConstraint("target_entity_id <> source_entity_id", name="chk_merge_distinct_entities"),
        ForeignKeyConstraint(
            ["organization_id", "source_entity_id"],
            ["entities.organization_id", "entities.id"],
            ondelete="RESTRICT",
            name="fk_merge_source_org",
        ),
        ForeignKeyConstraint(
            ["organization_id", "target_entity_id"],
            ["entities.organization_id", "entities.id"],
            ondelete="RESTRICT",
            name="fk_merge_target_org",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    merged_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    unmerged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unmerged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    source_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[source_entity_id])
    target_entity: Mapped["Entity"] = relationship("Entity", foreign_keys=[target_entity_id])
    actor: Mapped["User"] = relationship("User", foreign_keys=[merged_by])
