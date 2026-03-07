"""Session Manager — handles session lifecycle"""
from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.message import SessionMessage
from backend.models.session import TherapySession
from backend.models.task import TherapyTask
from backend.models.user import User
from backend.services.ai_therapist import AITherapist

therapist = AITherapist()


async def get_or_create_user(db: AsyncSession, telegram_id: int, first_name: str = "User") -> User:
    """Get existing user by telegram_id or create new one."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id, first_name=first_name, display_name=first_name)
        db.add(user)
        await db.flush()
    return user


async def start_session(db: AsyncSession, user_id: int) -> TherapySession:
    """Start a new therapy session."""
    # Count existing sessions
    count_result = await db.execute(
        select(func.count(TherapySession.id)).where(
            TherapySession.user_id == user_id,
            TherapySession.status == "completed",
        )
    )
    completed_count = count_result.scalar() or 0

    session_number = completed_count + 1
    session_type = "assessment" if session_number == 1 else "intervention"

    session = TherapySession(
        user_id=user_id,
        session_number=session_number,
        session_type=session_type,
        status="active",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()

    logger.info(f"Started session #{session_number} for user {user_id}")
    return session


async def send_message(
    db: AsyncSession,
    session_id: int,
    user_id: int,
    user_message: str,
) -> dict:
    """Process a user message and get AI response."""
    # Load session
    result = await db.execute(
        select(TherapySession)
        .where(TherapySession.id == session_id)
        .options(selectinload(TherapySession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    # Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    # Save user message
    user_msg = SessionMessage(
        session_id=session_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Build conversation history
    history = []
    for msg in sorted(session.messages, key=lambda m: m.created_at):
        history.append({"role": msg.role if msg.role != "therapist" else "assistant", "content": msg.content})

    # Get context for AI
    money_scripts = "Не определены"
    if user and user.money_avoidance_score:
        scripts = []
        if user.money_avoidance_score and user.money_avoidance_score > 3.5:
            scripts.append(f"Avoidance: {user.money_avoidance_score:.1f}")
        if user.money_worship_score and user.money_worship_score > 3.5:
            scripts.append(f"Worship: {user.money_worship_score:.1f}")
        if user.money_status_score and user.money_status_score > 3.5:
            scripts.append(f"Status: {user.money_status_score:.1f}")
        if user.money_vigilance_score and user.money_vigilance_score > 3.5:
            scripts.append(f"Vigilance: {user.money_vigilance_score:.1f}")
        if scripts:
            money_scripts = ", ".join(scripts)

    # Get last session summary
    last_summary = "Первая сессия"
    if session.session_number > 1:
        prev_result = await db.execute(
            select(TherapySession)
            .where(
                TherapySession.user_id == user_id,
                TherapySession.session_number == session.session_number - 1,
            )
        )
        prev_session = prev_result.scalar_one_or_none()
        if prev_session and prev_session.summary:
            last_summary = prev_session.summary

    # Count active tasks
    tasks_result = await db.execute(
        select(func.count(TherapyTask.id)).where(
            TherapyTask.user_id == user_id,
            TherapyTask.status == "pending",
        )
    )
    active_tasks_count = tasks_result.scalar() or 0

    # Generate AI response
    ai_response = await therapist.generate_response(
        user_message=user_message,
        conversation_history=history,
        session_number=session.session_number,
        therapy_phase=user.therapy_phase if user else "assessment",
        total_sessions=session.session_number - 1,
        money_scripts_summary=money_scripts,
        active_tasks=f"{active_tasks_count} заданий" if active_tasks_count else "Нет",
        patterns="Не выявлены",  # TODO: extract from past sessions
        last_session_summary=last_summary,
        session_focus=session.session_type,
        methodology=session.methodology_used,
    )

    # Save AI response
    ai_msg = SessionMessage(
        session_id=session_id,
        role="therapist",
        content=ai_response["content"],
        ai_model=ai_response["model_used"],
        tokens_input=ai_response["tokens_input"],
        tokens_output=ai_response["tokens_output"],
        crisis_flag=ai_response["crisis_detected"],
    )
    db.add(ai_msg)
    await db.flush()

    return {
        "message_id": ai_msg.id,
        "content": ai_response["content"],
        "crisis_detected": ai_response["crisis_detected"],
        "model_used": ai_response["model_used"],
    }


async def complete_session(db: AsyncSession, session_id: int) -> dict:
    """Complete a session and generate summary."""
    result = await db.execute(
        select(TherapySession)
        .where(TherapySession.id == session_id)
        .options(selectinload(TherapySession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    # Build history for summary
    history = []
    for msg in sorted(session.messages, key=lambda m: m.created_at):
        role = "assistant" if msg.role == "therapist" else msg.role
        history.append({"role": role, "content": msg.content})

    # Generate summary
    summary_result = await therapist.generate_session_summary(history)

    # Update session
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    if session.started_at:
        delta = session.completed_at - session.started_at
        session.duration_minutes = int(delta.total_seconds() / 60)
    session.summary = summary_result.get("summary", "")

    await db.flush()

    logger.info(f"Completed session #{session.session_number}")
    return {"summary": session.summary, "duration_minutes": session.duration_minutes}
