"""
Ruleset and RulesetVersion models — formatting rule definitions with versioning.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text,
)
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ruleset(Base):
    __tablename__ = "rulesets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Verified by FormatGuard team"
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_avg: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    rules: Mapped[dict] = mapped_column(
        JSON, nullable=False,
        comment="Full ruleset JSON schema (see Appendix A)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    institution = relationship("Institution", back_populates="rulesets")
    creator = relationship("User", back_populates="rulesets_created")
    versions = relationship(
        "RulesetVersion", back_populates="ruleset", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="ruleset")
    ratings = relationship(
        "RulesetRating", back_populates="ruleset", cascade="all, delete-orphan"
    )


class RulesetVersion(Base):
    __tablename__ = "ruleset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ruleset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rulesets.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    rules: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ruleset = relationship("Ruleset", back_populates="versions")
