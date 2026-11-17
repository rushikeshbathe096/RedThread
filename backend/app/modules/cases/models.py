import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    DateTime,
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
from backend.app.db.enums import CaseStatus, OrgRole


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "case_number", name="uq_case_org_number"),
        UniqueConstraint("organization_id", "id", name="uq_case_org"),
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
    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        SQLEnum(CaseStatus, name="case_status"),
        nullable=False,
        default=CaseStatus.ACTIVE,
    )
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
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

    organization: Mapped["Organization"] = relationship("Organization", back_populates="cases")
    members: Mapped[List["CaseMember"]] = relationship(
        "CaseMember", back_populates="case", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="case")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="case")


class CaseMember(Base):
    __tablename__ = "case_members"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "case_id"],
            ["cases.organization_id", "cases.id"],
            ondelete="CASCADE",
            name="fk_case_member_org_case",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[OrgRole] = mapped_column(
        SQLEnum(OrgRole, name="org_role"),
        nullable=False,
        default=OrgRole.INVESTIGATOR,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped["Case"] = relationship("Case", back_populates="members")
    user: Mapped["User"] = relationship("User")


class CaseEntity(Base):
    __tablename__ = "case_entities"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped["Case"] = relationship("Case")
    entity: Mapped["Entity"] = relationship("Entity")
