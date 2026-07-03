"""
Institution model — organizations that manage rulesets and users.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="e.g. nust.edu.pk — used for auto-institution linking"
    )
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(
        String(50), default="starter",
        comment="starter, growth, enterprise"
    )
    max_users: Mapped[int] = mapped_column(Integer, default=300)
    max_rulesets: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    users = relationship("User", back_populates="institution")
    rulesets = relationship("Ruleset", back_populates="institution")
