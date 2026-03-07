"""Insights API — dashboard data and pattern analysis"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models.session import TherapySession
from backend.models.task import TherapyTask
from backend.models.progress import ProgressMetric
from backend.models.assessment import Assessment
from backend.models.user import User

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.get("/dashboard")
async def get_dashboard(
    user_id: int, db: AsyncSession = Depends(get_session)
):
    """Get dashboard data: user profile, last session, active tasks, metrics."""
    # User profile
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"error": "User not found"}

    # Last session
    session_result = await db.execute(
        select(TherapySession)
        .where(TherapySession.user_id == user_id)
        .order_by(desc(TherapySession.created_at))
        .limit(1)
    )
    last_session = session_result.scalar_one_or_none()

    # Active tasks count
    tasks_result = await db.execute(
        select(func.count(TherapyTask.id)).where(
            TherapyTask.user_id == user_id,
            TherapyTask.status == "pending",
        )
    )
    pending_tasks = tasks_result.scalar() or 0

    # Completed tasks count
    completed_result = await db.execute(
        select(func.count(TherapyTask.id)).where(
            TherapyTask.user_id == user_id,
            TherapyTask.status == "completed",
        )
    )
    completed_tasks = completed_result.scalar() or 0

    # Total sessions
    sessions_count_result = await db.execute(
        select(func.count(TherapySession.id)).where(
            TherapySession.user_id == user_id,
            TherapySession.status == "completed",
        )
    )
    total_sessions = sessions_count_result.scalar() or 0

    # Latest metrics
    metric_result = await db.execute(
        select(ProgressMetric)
        .where(ProgressMetric.user_id == user_id)
        .order_by(desc(ProgressMetric.metric_date))
        .limit(1)
    )
    latest_metric = metric_result.scalar_one_or_none()

    return {
        "user": {
            "display_name": user.display_name,
            "therapy_phase": user.therapy_phase,
            "preferred_methodology": user.preferred_methodology,
            "money_scripts": {
                "avoidance": user.money_avoidance_score,
                "worship": user.money_worship_score,
                "status": user.money_status_score,
                "vigilance": user.money_vigilance_score,
            },
        },
        "sessions": {
            "total_completed": total_sessions,
            "last_session": {
                "id": last_session.id,
                "number": last_session.session_number,
                "status": last_session.status,
                "summary": last_session.summary,
            } if last_session else None,
        },
        "tasks": {
            "pending": pending_tasks,
            "completed": completed_tasks,
        },
        "latest_metric": {
            "date": str(latest_metric.metric_date),
            "motivation": latest_metric.motivation_level,
            "monetization_actions": latest_metric.monetization_actions,
            "revenue": latest_metric.revenue_today,
        } if latest_metric else None,
    }


@router.get("/patterns")
async def get_patterns(
    user_id: int, db: AsyncSession = Depends(get_session)
):
    """Analyze patterns from session summaries and metrics."""
    # Get all completed sessions with summaries
    sessions_result = await db.execute(
        select(TherapySession)
        .where(
            TherapySession.user_id == user_id,
            TherapySession.status == "completed",
        )
        .order_by(TherapySession.session_number)
    )
    sessions = sessions_result.scalars().all()

    # Get metrics trend (last 14 days)
    metrics_result = await db.execute(
        select(ProgressMetric)
        .where(ProgressMetric.user_id == user_id)
        .order_by(desc(ProgressMetric.metric_date))
        .limit(14)
    )
    metrics = metrics_result.scalars().all()

    # Build patterns data
    session_data = []
    for s in sessions:
        session_data.append({
            "session_number": s.session_number,
            "type": s.session_type,
            "methodology": s.methodology_used,
            "summary": s.summary,
            "key_insights": s.key_insights,
            "patterns": s.identified_patterns,
            "emotional_start": s.emotional_start,
            "emotional_end": s.emotional_end,
        })

    metrics_data = []
    for m in metrics:
        metrics_data.append({
            "date": str(m.metric_date),
            "motivation": m.motivation_level,
            "monetization_actions": m.monetization_actions,
            "avoidance_episodes": m.avoidance_episodes,
            "revenue": m.revenue_today,
        })

    # Compute basic trends
    trends = {}
    if len(metrics) >= 2:
        recent = metrics[:7]
        older = metrics[7:14]
        if recent and older:
            avg_recent_motivation = _avg([m.motivation_level for m in recent])
            avg_older_motivation = _avg([m.motivation_level for m in older])
            if avg_recent_motivation and avg_older_motivation:
                trends["motivation_trend"] = (
                    "up" if avg_recent_motivation > avg_older_motivation
                    else "down" if avg_recent_motivation < avg_older_motivation
                    else "stable"
                )

    return {
        "sessions": session_data,
        "metrics_trend": metrics_data,
        "trends": trends,
        "total_sessions": len(sessions),
    }


def _avg(values: list) -> float | None:
    """Average of non-None values."""
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None
