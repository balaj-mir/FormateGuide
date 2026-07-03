"""
Submission model — user document uploads queued for compliance checking.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ruleset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rulesets.id"),
        nullable=True,
    )
    ruleset_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="Locked at submission time"
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    file_key: Mapped[str | None] = mapped_column(
        String(1000), nullable=True,
        comment="S3/R2 object key"
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    file_type: Mapped[str] = mapped_column(
        String(20), default="docx",
        comment="docx or pdf"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True,
        comment="pending, processing, complete, failed"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="submissions")
    ruleset = relationship("Ruleset", back_populates="submissions")
    report = relationship(
        "ComplianceReport",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )
