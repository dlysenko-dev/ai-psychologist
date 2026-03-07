"""Assessments API — KMSI, monetization block screening, self-sabotage"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.models.assessment import Assessment
from backend.models.user import User

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


class StartAssessmentRequest(BaseModel):
    user_id: int
    assessment_type: str  # kmsi, monetization_block, self_sabotage


class SubmitAnswersRequest(BaseModel):
    answers: dict  # {question_id: answer_value}


class AssessmentResponse(BaseModel):
    id: int
    assessment_type: str
    status: str
    scores: dict | None = None
    interpretation: str | None = None
    recommendations: dict | None = None

    class Config:
        from_attributes = True


# KMSI scoring logic
KMSI_SCALES = {
    "money_avoidance": [1, 2, 3, 4, 5],       # question indices
    "money_worship": [6, 7, 8, 9, 10],
    "money_status": [11, 12, 13, 14, 15],
    "money_vigilance": [16, 17, 18, 19, 20],
}


def score_kmsi(answers: dict) -> dict:
    """Score KMSI-R simplified (20 questions, 1-5 Likert scale)."""
    scores = {}
    for scale, question_ids in KMSI_SCALES.items():
        values = []
        for q_id in question_ids:
            val = answers.get(str(q_id))
            if val is not None:
                values.append(int(val))
        scores[scale] = round(sum(values) / len(values), 2) if values else 0
    return scores


def interpret_kmsi(scores: dict) -> str:
    """Generate interpretation text for KMSI scores."""
    parts = []
    labels = {
        "money_avoidance": "Избегание денег",
        "money_worship": "Поклонение деньгам",
        "money_status": "Деньги как статус",
        "money_vigilance": "Бдительность к деньгам",
    }
    for scale, label in labels.items():
        score = scores.get(scale, 0)
        level = "высокий" if score >= 3.5 else "средний" if score >= 2.5 else "низкий"
        parts.append(f"{label}: {score}/5 ({level})")

    dominant = max(scores, key=lambda k: scores[k])
    dominant_label = labels[dominant]

    interpretation = (
        f"Результаты KMSI-R:\n"
        + "\n".join(f"- {p}" for p in parts)
        + f"\n\nДоминирующий денежный скрипт: {dominant_label} ({scores[dominant]}/5)."
    )
    return interpretation


def score_self_sabotage(answers: dict) -> dict:
    """Score self-sabotage indicators (7 questions, 1-10 scale)."""
    indicator_names = [
        "perfectionism", "shiny_object", "imposter_syndrome",
        "fear_of_success", "analysis_paralysis", "procrastination", "sunk_cost",
    ]
    scores = {}
    for i, name in enumerate(indicator_names, 1):
        val = answers.get(str(i))
        scores[name] = int(val) if val is not None else 0

    total = sum(scores.values())
    scores["total"] = total
    scores["severity"] = (
        "critical" if total >= 50
        else "high" if total >= 35
        else "moderate" if total >= 20
        else "low"
    )
    return scores


@router.post("", response_model=AssessmentResponse)
async def start_assessment(
    req: StartAssessmentRequest, db: AsyncSession = Depends(get_session)
):
    """Start a new assessment."""
    valid_types = ["kmsi", "monetization_block", "self_sabotage"]
    if req.assessment_type not in valid_types:
        raise HTTPException(400, f"Invalid type. Use: {', '.join(valid_types)}")

    assessment = Assessment(
        user_id=req.user_id,
        assessment_type=req.assessment_type,
        status="in_progress",
    )
    db.add(assessment)
    await db.flush()
    return assessment


@router.post("/{assessment_id}/submit", response_model=AssessmentResponse)
async def submit_answers(
    assessment_id: int,
    req: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_session),
):
    """Submit answers and get scored results."""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    assessment.answers = req.answers
    assessment.status = "completed"
    assessment.completed_at = datetime.now(timezone.utc)

    # Score based on type
    if assessment.assessment_type == "kmsi":
        scores = score_kmsi(req.answers)
        assessment.scores = scores
        assessment.interpretation = interpret_kmsi(scores)

        # Update user money script scores
        user_result = await db.execute(
            select(User).where(User.id == assessment.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.money_avoidance_score = scores.get("money_avoidance")
            user.money_worship_score = scores.get("money_worship")
            user.money_status_score = scores.get("money_status")
            user.money_vigilance_score = scores.get("money_vigilance")

    elif assessment.assessment_type == "self_sabotage":
        scores = score_self_sabotage(req.answers)
        assessment.scores = scores

    elif assessment.assessment_type == "monetization_block":
        # Open-ended questions — store answers, no auto-scoring
        assessment.scores = {"type": "qualitative"}

    await db.flush()
    return assessment


@router.get("")
async def list_assessments(
    user_id: int, db: AsyncSession = Depends(get_session)
):
    """List all assessments for a user."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
    )
    assessments = result.scalars().all()
    return [
        AssessmentResponse(
            id=a.id,
            assessment_type=a.assessment_type,
            status=a.status,
            scores=a.scores,
            interpretation=a.interpretation,
            recommendations=a.recommendations,
        )
        for a in assessments
    ]


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int, db: AsyncSession = Depends(get_session)
):
    """Get a specific assessment with results."""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return assessment
