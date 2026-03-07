"""User model"""
from typing import Optional

from sqlalchemy import BigInteger, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    first_name: Mapped[str] = mapped_column(String(100), default="User")
    display_name: Mapped[str] = mapped_column(String(100), default="User")

    # Money Script profile (from KMSI assessment)
    money_avoidance_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    money_worship_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    money_status_score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    money_vigilance_score: Mapped[Optional[float]] = mapped_column(Float, default=None)

    # Current therapy phase
    therapy_phase: Mapped[str] = mapped_column(
        String(50), default="assessment"
    )  # assessment, early_intervention, active_work, maintenance

    # Preferences
    preferred_methodology: Mapped[Optional[str]] = mapped_column(
        String(50), default=None
    )  # cbt, act, mi, mixed
    session_language: Mapped[str] = mapped_column(String(10), default="ru")
