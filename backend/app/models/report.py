"""
ComplianceReport model — generated report with scores and metadata.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ComplianceReport(Base):
    __tablename__ = "compliance_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    compliance_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True,
        comment="Percentage 0.00-100.00"
    )
    total_violations: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    suggestion_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_fix_time_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    total_elements_checked: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    report_pdf_key: Mapped[str | None] = mapped_column(
        String(1000), nullable=True,
        comment="S3/R2 key for generated PDF"
    )
    corrected_doc_key: Mapped[str | None] = mapped_column(
        String(1000), nullable=True,
        comment="S3/R2 key for corrected .docx"
    )
    document_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Structured list of found formatting issues"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    submission = relationship("Submission", back_populates="report")
    violations = relationship(
        "Violation", back_populates="report", cascade="all, delete-orphan",
        order_by="Violation.display_order"
    )
