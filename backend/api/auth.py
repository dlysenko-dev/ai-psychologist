"""Auth API — Telegram-based authentication for Mini App"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_session
from backend.models.user import User
from backend.services.telegram_auth import validate_init_data

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 дней


class TelegramAuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    display_name: str


def create_token(user_id: int, telegram_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "tg": telegram_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Dependency: extract user from JWT Bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization[7:]
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")

    return user


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(req: TelegramAuthRequest, db: AsyncSession = Depends(get_session)):
    """Authenticate via Telegram WebApp initData. Creates user if needed."""
    tg_user = validate_init_data(req.init_data)
    if not tg_user:
        raise HTTPException(401, "Invalid Telegram initData")

    telegram_id = tg_user["id"]
    first_name = tg_user["first_name"]
    username = tg_user.get("username")
    display_name = first_name
    if tg_user.get("last_name"):
        display_name += f" {tg_user['last_name']}"

    # Get or create user
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        # Update name/username if changed
        user.first_name = first_name
        user.display_name = display_name
        if username:
            user.telegram_username = username
    else:
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=first_name,
            display_name=display_name,
        )
        db.add(user)
        await db.flush()

    token = create_token(user.id, telegram_id)
    return AuthResponse(token=token, user_id=user.id, display_name=user.display_name)
