"""Session message model"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base, TimestampMixin


class SessionMessage(Base, TimestampMixin):
    __tablename__ = "session_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("therapy_sessions.id"), index=True
    )

    role: Mapped[str] = mapped_column(String(20))  # user, therapist, system
    content: Mapped[str] = mapped_column(Text)

    # AI metadata
    ai_model: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    tokens_input: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    tokens_output: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Therapeutic metadata (AI-tagged)
    message_type: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    # Types: reflection, question, disclosure, resistance, insight, task_review, psychoeducation
    detected_emotions: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
    detected_cognitive_distortions: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=None
    )
    crisis_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    # RAG context used
    knowledge_sources_used: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)

    # Relationship
    session: Mapped["TherapySession"] = relationship(
        "TherapySession", back_populates="messages"
    )
