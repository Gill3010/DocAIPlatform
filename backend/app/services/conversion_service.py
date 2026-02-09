"""
Conversion service - credit checks and conversion flow logic.
Prioridad 2 + Prioridad 3: used by convert router and pdf_tools (same credit pool).
"""
from __future__ import annotations

import uuid
from typing import Union
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthLimitReached, AnonymousLimitReached, InvalidCredentials, InvalidInput, UserNotFound
from app.models.user import User
from app.models.conversion import Conversion
from app.models.anonymous_session import AnonymousSession


async def check_user_can_convert(
    db: AsyncSession,
    user_id: int,
) -> User:
    """
    Sync user credit count with completed conversions, then check limit.
    Returns the loaded User. Raises ValueError with message if limit reached.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFound("User not found")

    completed_result = await db.execute(
        select(func.count(Conversion.id)).where(
            Conversion.user_id == user.id,
            Conversion.status == "completed",
        )
    )
    completed_count = completed_result.scalar() or 0
    if user.free_conversion_count < completed_count:
        user.free_conversion_count = min(
            settings.FREE_TIER_CONVERSIONS_LIMIT,
            int(completed_count),
        )
        await db.commit()
        await db.refresh(user)

    if not getattr(user, "is_superuser", False) and user.free_conversion_count >= settings.FREE_TIER_CONVERSIONS_LIMIT:
        raise AuthLimitReached()
    return user


def increment_user_conversion_count(
    user: User,
    is_superuser: bool = False,
) -> None:
    """Increment free_conversion_count on user (in-memory). Caller must commit."""
    if not is_superuser:
        user.free_conversion_count = (user.free_conversion_count or 0) + 1


def credits_remaining_for_user(user: User) -> int:
    """Return remaining credits for response."""
    if getattr(user, "is_superuser", False):
        return 999999
    return max(0, settings.FREE_TIER_CONVERSIONS_LIMIT - (user.free_conversion_count or 0))


async def check_credits_for_operation(
    db: AsyncSession,
    current_user: User | None,
    x_anonymous_session_id: str | None,
) -> tuple[Union[User, AnonymousSession], bool]:
    """
    Check credits for conversion/pdf_tool (same pool). Returns (entity, is_anonymous).
    Raises ValueError with detail key (auth_limit_reached, anonymous_limit_reached, etc.).
    """
    if current_user is not None:
        user = await check_user_can_convert(db, current_user.id)
        return (user, False)
    if not x_anonymous_session_id:
        raise InvalidCredentials("Could not validate credentials")
    try:
        uuid.UUID(x_anonymous_session_id)
    except ValueError:
        raise InvalidInput("Invalid X-Anonymous-Session-Id")
    result = await db.execute(
        select(AnonymousSession).where(AnonymousSession.id == x_anonymous_session_id)
    )
    anon = result.scalar_one_or_none()
    if not anon:
        anon = AnonymousSession(id=x_anonymous_session_id, conversions_count=0)
        db.add(anon)
        await db.commit()
        await db.refresh(anon)
    if anon.conversions_count >= settings.ANONYMOUS_CONVERSIONS_LIMIT:
        raise AnonymousLimitReached()
    return (anon, True)


async def consume_credit_for_operation(
    db: AsyncSession,
    entity: Union[User, AnonymousSession],
    is_anonymous: bool,
) -> None:
    """Increment credit for conversion/pdf_tool. Caller must commit if needed (entity already updated)."""
    if is_anonymous:
        entity.conversions_count += 1
    else:
        increment_user_conversion_count(entity, is_superuser=getattr(entity, "is_superuser", False))
    await db.commit()
    await db.refresh(entity)
