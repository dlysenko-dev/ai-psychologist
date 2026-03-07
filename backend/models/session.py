"""Therapy session model"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base, TimestampMixin


class TherapySession(Base, TimestampMixin):
    __tablename__ = "therapy_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_number: Mapped[int] = mapped_column(Integer)

    # Session metadata
    session_type: Mapped[str] = mapped_column(
        String(50)
    )  # assessment, intervention, check_in, crisis
    methodology_used: Mapped[Optional[str]] = mapped_column(
        String(50), default=None
    )  # cbt, act, mi, sfbt, ba, mixed
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, completed, abandoned

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # AI-generated session summary
    summary: Mapped[Optional[str]] = mapped_column(Text, default=None)
    key_insights: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
    identified_patterns: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
    homework_assigned: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)

    # Therapeutic scores (AI-assessed at session close)
    emotional_state_start: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    emotional_state_end: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    engagement_level: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    resistance_level: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Relationships
    messages: Mapped[List["SessionMessage"]] = relationship(
        "SessionMessage", back_populates="session", cascade="all, delete-orphan"
    )
