"""
Violation model — individual formatting violations detected in a document.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    element_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="body_text, heading_1, heading_2, page_margin, page_number, header, footer, caption, reference"
    )
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="critical, warning, suggestion"
    )
    is_auto_fixable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ai_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    context_excerpt: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Surrounding text snippet"
    )
    fix_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    affected_count: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="How many paragraphs/elements have this violation"
    )
    display_order: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="For ordered list in report"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    report = relationship("ComplianceReport", back_populates="violations")
