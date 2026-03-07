"""Sessions API — therapy session management"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_session
from backend.models.session import TherapySession
from backend.models.message import SessionMessage
from backend.services.session_manager import start_session, send_message, complete_session

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class StartSessionRequest(BaseModel):
    user_id: int


class SendMessageRequest(BaseModel):
    user_id: int
    content: str


class SessionResponse(BaseModel):
    id: int
    session_number: int
    session_type: str
    status: str
    summary: str | None = None
    duration_minutes: int | None = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    crisis_flag: bool = False

    class Config:
        from_attributes = True


@router.get("")
async def list_sessions(
    user_id: int, db: AsyncSession = Depends(get_session)
):
    """List all sessions for a user."""
    result = await db.execute(
        select(TherapySession)
        .where(TherapySession.user_id == user_id)
        .order_by(TherapySession.session_number.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=s.id,
            session_number=s.session_number,
            session_type=s.session_type,
            status=s.status,
            summary=s.summary,
            duration_minutes=s.duration_minutes,
        )
        for s in sessions
    ]


@router.post("", response_model=SessionResponse)
async def create_session(
    req: StartSessionRequest, db: AsyncSession = Depends(get_session)
):
    """Start a new therapy session."""
    session = await start_session(db, req.user_id)
    return SessionResponse(
        id=session.id,
        session_number=session.session_number,
        session_type=session.session_type,
        status=session.status,
    )


@router.get("/{session_id}")
async def get_session_detail(
    session_id: int, db: AsyncSession = Depends(get_session)
):
    """Get session details with all messages."""
    result = await db.execute(
        select(TherapySession)
        .where(TherapySession.id == session_id)
        .options(selectinload(TherapySession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    messages = sorted(session.messages, key=lambda m: m.created_at)
    return {
        "session": SessionResponse(
            id=session.id,
            session_number=session.session_number,
            session_type=session.session_type,
            status=session.status,
            summary=session.summary,
            duration_minutes=session.duration_minutes,
        ),
        "messages": [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                crisis_flag=m.crisis_flag,
            )
            for m in messages
        ],
    }


@router.post("/{session_id}/message")
async def post_message(
    session_id: int,
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_session),
):
    """Send a message in a session and get AI response."""
    response = await send_message(db, session_id, req.user_id, req.content)
    if "error" in response:
        raise HTTPException(404, response["error"])
    return response


@router.post("/{session_id}/complete")
async def post_complete(
    session_id: int, db: AsyncSession = Depends(get_session)
):
    """End a session and generate summary."""
    result = await complete_session(db, session_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result
