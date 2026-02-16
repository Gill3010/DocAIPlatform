"""
AI Assistant service - credit checks and consumption (anonymous + authenticated).
Prioridad 3 - Service Layer.
"""
from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AICreditsExhausted,
    AnonymousLimitReached,
    InvalidCredentials,
    InvalidInput,
    UserNotFound,
)
from app.models.user import User
from app.models.anonymous_session import AnonymousSession

AI_CREDITS_PER_MESSAGE = 1


async def get_or_create_anonymous_session(
    db: AsyncSession,
    session_id: str,
) -> AnonymousSession:
    """Validate UUID, get or create AnonymousSession. Raises InvalidInput if invalid."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise InvalidInput("Invalid X-Anonymous-Session-Id")
    result = await db.execute(
        select(AnonymousSession).where(AnonymousSession.id == session_id)
    )
    anon = result.scalar_one_or_none()
    if not anon:
        anon = AnonymousSession(id=session_id, conversions_count=0)
        db.add(anon)
        await db.commit()
        await db.refresh(anon)
    return anon


async def check_ai_can_send(
    db: AsyncSession,
    current_user: User | None,
    x_anonymous_session_id: str | None,
) -> tuple[AnonymousSession | User, bool]:
    """
    Check if the user/anonymous can send an AI message (credits available).
    Returns (entity to increment, is_anonymous). Raises AppException subclass on failure.
    """
    if current_user is not None:
        result = await db.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFound("User not found")
        is_limit_exempt = getattr(user, "is_superuser", False) or getattr(user, "is_premium", False) or getattr(user, "can_access_admin_panel", False)
        if not is_limit_exempt and (user.free_conversion_count or 0) >= settings.FREE_TIER_AI_CREDITS:
            raise AICreditsExhausted()
        return (user, False)
    if not x_anonymous_session_id:
        raise InvalidCredentials("Could not validate credentials")
    anon = await get_or_create_anonymous_session(db, x_anonymous_session_id)
    if anon.conversions_count >= settings.ANONYMOUS_AI_LIMIT:
        raise AnonymousLimitReached()
    return (anon, True)


async def consume_ai_credit(
    db: AsyncSession,
    entity: AnonymousSession | User,
    is_anonymous: bool,
) -> int:
    """Increment credit usage. Returns credits_remaining after consume."""
    if is_anonymous:
        entity.conversions_count += 1
        await db.commit()
        await db.refresh(entity)
        return max(0, settings.ANONYMOUS_AI_LIMIT - entity.conversions_count)
    is_limit_exempt = getattr(entity, "is_superuser", False) or getattr(entity, "is_premium", False) or getattr(entity, "can_access_admin_panel", False)
    if not is_limit_exempt:
        entity.free_conversion_count = (entity.free_conversion_count or 0) + AI_CREDITS_PER_MESSAGE
    await db.commit()
    await db.refresh(entity)
    if is_limit_exempt:
        return 999999
    return max(0, settings.FREE_TIER_AI_CREDITS - (entity.free_conversion_count or 0))


async def get_ai_credits_response(
    db: AsyncSession,
    current_user: User | None,
    x_anonymous_session_id: str | None,
) -> dict:
    """Return dict with credits_used, credits_remaining, credits_limit."""
    if current_user is not None:
        result = await db.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFound("User not found")
        used = user.free_conversion_count or 0
        limit = settings.FREE_TIER_AI_CREDITS
        is_limit_exempt = getattr(user, "is_superuser", False) or getattr(user, "is_premium", False) or getattr(user, "can_access_admin_panel", False)
        remaining = 999999 if is_limit_exempt else max(0, limit - used)
        return {"credits_used": used, "credits_remaining": remaining, "credits_limit": limit}
    if not x_anonymous_session_id:
        raise InvalidCredentials("Could not validate credentials")
    anon = await get_or_create_anonymous_session(db, x_anonymous_session_id)
    limit = settings.ANONYMOUS_AI_LIMIT
    remaining = max(0, limit - anon.conversions_count)
    return {
        "credits_used": anon.conversions_count,
        "credits_remaining": remaining,
        "credits_limit": limit,
    }
