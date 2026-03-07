"""Progress API — daily metrics tracking"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models.progress import ProgressMetric

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


class LogMetricRequest(BaseModel):
    user_id: int
    metric_date: date | None = None
    monetization_actions: int | None = None
    belief_shift: int | None = None
    emotional_regulation: int | None = None
    motivation_level: int | None = None
    revenue_today: float | None = None
    new_projects_started: int | None = None
    projects_abandoned: int | None = None
    avoidance_episodes: int | None = None
    journal_entry: str | None = None


class MetricResponse(BaseModel):
    id: int
    metric_date: date
    monetization_actions: int | None = None
    belief_shift: int | None = None
    emotional_regulation: int | None = None
    motivation_level: int | None = None
    revenue_today: float | None = None
    new_projects_started: int | None = None
    projects_abandoned: int | None = None
    avoidance_episodes: int | None = None
    journal_entry: str | None = None

    class Config:
        from_attributes = True


@router.post("", response_model=MetricResponse)
async def log_metric(
    req: LogMetricRequest, db: AsyncSession = Depends(get_session)
):
    """Log daily progress metrics. Upserts for the given date."""
    target_date = req.metric_date or date.today()

    # Check if entry for this date exists
    result = await db.execute(
        select(ProgressMetric).where(
            ProgressMetric.user_id == req.user_id,
            ProgressMetric.metric_date == target_date,
        )
    )
    metric = result.scalar_one_or_none()

    if metric:
        # Update existing
        for field in [
            "monetization_actions", "belief_shift", "emotional_regulation",
            "motivation_level", "revenue_today", "new_projects_started",
            "projects_abandoned", "avoidance_episodes", "journal_entry",
        ]:
            value = getattr(req, field)
            if value is not None:
                setattr(metric, field, value)
    else:
        metric = ProgressMetric(
            user_id=req.user_id,
            metric_date=target_date,
            monetization_actions=req.monetization_actions,
            belief_shift=req.belief_shift,
            emotional_regulation=req.emotional_regulation,
            motivation_level=req.motivation_level,
            revenue_today=req.revenue_today,
            new_projects_started=req.new_projects_started,
            projects_abandoned=req.projects_abandoned,
            avoidance_episodes=req.avoidance_episodes,
            journal_entry=req.journal_entry,
        )
        db.add(metric)

    await db.flush()
    return metric


@router.get("")
async def get_progress(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_session),
):
    """Get progress metrics for the last N days."""
    result = await db.execute(
        select(ProgressMetric)
        .where(ProgressMetric.user_id == user_id)
        .order_by(ProgressMetric.metric_date.desc())
        .limit(days)
    )
    metrics = result.scalars().all()
    return [
        MetricResponse(
            id=m.id,
            metric_date=m.metric_date,
            monetization_actions=m.monetization_actions,
            belief_shift=m.belief_shift,
            emotional_regulation=m.emotional_regulation,
            motivation_level=m.motivation_level,
            revenue_today=m.revenue_today,
            new_projects_started=m.new_projects_started,
            projects_abandoned=m.projects_abandoned,
            avoidance_episodes=m.avoidance_episodes,
            journal_entry=m.journal_entry,
        )
        for m in metrics
    ]


@router.get("/summary")
async def get_progress_summary(
    user_id: int, db: AsyncSession = Depends(get_session)
):
    """Get aggregated progress summary."""
    result = await db.execute(
        select(
            func.count(ProgressMetric.id).label("total_days"),
            func.sum(ProgressMetric.monetization_actions).label("total_actions"),
            func.sum(ProgressMetric.revenue_today).label("total_revenue"),
            func.avg(ProgressMetric.motivation_level).label("avg_motivation"),
            func.avg(ProgressMetric.emotional_regulation).label("avg_regulation"),
            func.sum(ProgressMetric.new_projects_started).label("total_new_projects"),
            func.sum(ProgressMetric.avoidance_episodes).label("total_avoidance"),
        ).where(ProgressMetric.user_id == user_id)
    )
    row = result.one()

    return {
        "total_days_tracked": row.total_days or 0,
        "total_monetization_actions": row.total_actions or 0,
        "total_revenue": float(row.total_revenue or 0),
        "avg_motivation": round(float(row.avg_motivation or 0), 1),
        "avg_emotional_regulation": round(float(row.avg_regulation or 0), 1),
        "total_new_projects_started": row.total_new_projects or 0,
        "total_avoidance_episodes": row.total_avoidance or 0,
    }
