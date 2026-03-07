"""Assessment model"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base, TimestampMixin


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("therapy_sessions.id"), default=None
    )

    assessment_type: Mapped[str] = mapped_column(
        String(50)
    )  # kmsi, monetization_block, self_sabotage
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress"
    )  # in_progress, completed

    # Answers stored as JSON: {question_id: answer_value}
    answers: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)

    # Computed scores
    scores: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)

    # AI interpretation
    interpretation: Mapped[Optional[str]] = mapped_column(Text, default=None)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
