"""
RulesetRating model — user ratings and reviews for marketplace rulesets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RulesetRating(Base):
    __tablename__ = "ruleset_ratings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ruleset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rulesets.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="1-5 star rating"
    )
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # One rating per user per ruleset
    __table_args__ = (
        UniqueConstraint("ruleset_id", "user_id", name="uq_ruleset_user_rating"),
    )

    # Relationships
    ruleset = relationship("Ruleset", back_populates="ratings")
    user = relationship("User", back_populates="ratings")
