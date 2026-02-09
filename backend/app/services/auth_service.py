"""
Auth service - registration, login, anonymous session linking.
Business logic moved from auth router (Prioridad 2 - Service Layer).
"""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCredentials, InvalidInput, UserNotFound
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.models.anonymous_session import AnonymousSession


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """Create a new user with email/password. Raises InvalidInput if email exists."""
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise InvalidInput("Email already registered")
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name or "",
        auth_provider="email",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[str, str]:
    """
    Validate credentials and return (access_token, token_type).
    Raises InvalidCredentials on failure.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise InvalidCredentials("Incorrect email or password")
    if not user.hashed_password:
        raise InvalidCredentials("This account uses social login. Use Google or Facebook to sign in.")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Incorrect email or password")
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=expires)
    return token, "bearer"


async def link_anonymous_session(
    db: AsyncSession,
    user_id: int,
    anonymous_session_id: str,
) -> tuple[int, int]:
    """
    Link anonymous session conversions to the user. Returns (credits_used, credits_remaining).
    """
    try:
        UUID(anonymous_session_id)
    except ValueError:
        raise InvalidInput("Invalid anonymous_session_id format")

    result = await db.execute(
        select(AnonymousSession).where(AnonymousSession.id == anonymous_session_id)
    )
    anon_session = result.scalar_one_or_none()

    result_user = await db.execute(select(User).where(User.id == user_id))
    db_user = result_user.scalar_one_or_none()
    if not db_user:
        raise UserNotFound("User not found")

    if not anon_session or anon_session.conversions_count == 0:
        used = db_user.free_conversion_count
        remaining = max(0, settings.FREE_TIER_CONVERSIONS_LIMIT - used)
        return used, remaining

    anon_count = min(anon_session.conversions_count, 3)
    if db_user.free_conversion_count < anon_count:
        db_user.free_conversion_count = anon_count
        await db.commit()
        await db.refresh(db_user)

    used = db_user.free_conversion_count
    remaining = max(0, settings.FREE_TIER_CONVERSIONS_LIMIT - used)
    return used, remaining
