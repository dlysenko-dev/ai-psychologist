"""Progress metric model"""
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base, TimestampMixin


class ProgressMetric(Base, TimestampMixin):
    __tablename__ = "progress_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    metric_date: Mapped[date] = mapped_column(Date, index=True)

    # Core tracked metrics (1-10 scale)
    monetization_actions: Mapped[Optional[int]] = mapped_column(
        Integer, default=None
    )  # count of revenue-generating actions
    belief_shift: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    emotional_regulation: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    motivation_level: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Revenue tracking
    revenue_today: Mapped[Optional[float]] = mapped_column(Float, default=None)

    # Self-sabotage indicators
    new_projects_started: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    projects_abandoned: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    avoidance_episodes: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Journal entry
    journal_entry: Mapped[Optional[str]] = mapped_column(Text, default=None)
