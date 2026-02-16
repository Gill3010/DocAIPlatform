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
from app.core.exceptions import (
    AuthLimitReached, 
    AnonymousLimitReached, 
    InvalidCredentials, 
    InvalidInput, 
    UserNotFound,
    PremiumFormatRequired
)
from app.models.user import User
from app.models.conversion import Conversion
from app.models.anonymous_session import AnonymousSession


async def check_user_can_convert(
    db: AsyncSession,
    user_id: int,
) -> User:
    """
    Sync user credit count, check for monthly reset, then check limit based on plan.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFound("User not found")

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    # 1. Handle Subscription Expiration
    if user.is_premium and user.subscription_end_date:
        # Ensure subscription_end_date is timezone-aware for comparison if it's not
        end_date = user.subscription_end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
            
        if now > end_date:
            user.is_premium = False
            user.premium_plan_id = None
            # We keep monthly_conversion_count for history, but user is now free tier
            await db.commit()
            await db.refresh(user)

    # 2. Handle Monthly Reset for Premium Users
    if user.is_premium and user.last_billing_reset:
        # Check if 30 days have passed since last reset
        reset_date = user.last_billing_reset
        if reset_date.tzinfo is None:
            reset_date = reset_date.replace(tzinfo=timezone.utc)

        if now >= reset_date + timedelta(days=30):
            user.monthly_conversion_count = 0
            user.last_billing_reset = now
            await db.commit()
            await db.refresh(user)

    # 2. Check Limits (superuser and admin panel users have unlimited conversions)
    if getattr(user, "is_superuser", False) or getattr(user, "can_access_admin_panel", False):
        return user

    if user.is_premium:
        # Basic Plan: 50 conversions/month
        if user.premium_plan_id == 'Básico':
            if (user.monthly_conversion_count or 0) >= 50:
                raise AuthLimitReached() # Should probably be a more specific "MonthlyLimitReached" but this triggers the modal
        # Pro/Empresa are unlimited
        return user
    
    # Free Tier Logic
    completed_result = await db.execute(
        select(func.count(Conversion.id)).where(
            Conversion.user_id == user.id,
            Conversion.status == "completed",
        )
    )
    completed_count = completed_result.scalar() or 0
    if (user.free_conversion_count or 0) < completed_count:
        user.free_conversion_count = min(
            settings.FREE_TIER_CONVERSIONS_LIMIT,
            int(completed_count),
        )
        await db.commit()
        await db.refresh(user)

    if (user.free_conversion_count or 0) >= settings.FREE_TIER_CONVERSIONS_LIMIT:
        raise AuthLimitReached()
    
    return user


def increment_user_conversion_count(
    user: User,
    is_superuser: bool = False,
) -> None:
    """Increment conversion count on user (in-memory). Caller must commit."""
    if is_superuser or getattr(user, "can_access_admin_panel", False):
        return

    if getattr(user, "is_premium", False):
        user.monthly_conversion_count = (user.monthly_conversion_count or 0) + 1
    else:
        user.free_conversion_count = (user.free_conversion_count or 0) + 1


def credits_remaining_for_user(user: User) -> int:
    """Return remaining credits for response."""
    if getattr(user, "is_superuser", False) or getattr(user, "can_access_admin_panel", False) or user.premium_plan_id in ['Pro', 'Empresa']:
        return 999999
    
    if user.premium_plan_id == 'Básico':
        return max(0, 50 - (user.monthly_conversion_count or 0))
        
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
        exempt = getattr(entity, "is_superuser", False) or getattr(entity, "can_access_admin_panel", False)
        increment_user_conversion_count(entity, is_superuser=exempt)
    await db.commit()
    await db.refresh(entity)


def check_premium_format_access(
    entity: User | AnonymousSession,
    target_format: str,
) -> None:
    """
    Check if the user/entity can access the requested target format.
    Premium formats are restricted to premium users.
    """
    if target_format.lower() in settings.PREMIUM_FORMATS:
        is_premium = getattr(entity, "is_premium", False) or getattr(entity, "is_superuser", False) or getattr(entity, "can_access_admin_panel", False)
        if not is_premium:
            raise PremiumFormatRequired()
