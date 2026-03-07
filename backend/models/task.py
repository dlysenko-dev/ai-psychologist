"""Therapy task model"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base, TimestampMixin


class TherapyTask(Base, TimestampMixin):
    __tablename__ = "therapy_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("therapy_sessions.id"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50))
    # Types: behavioral_activation, thought_record, exposure, values_exercise, journaling, micro_task

    methodology: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5

    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, in_progress, completed, skipped
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # User reflection
    reflection: Mapped[Optional[str]] = mapped_column(Text, default=None)
    difficulty_rating: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    usefulness_rating: Mapped[Optional[int]] = mapped_column(Integer, default=None)
