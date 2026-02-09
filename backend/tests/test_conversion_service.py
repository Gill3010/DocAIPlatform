"""Tests for conversion_service."""
import pytest
from backend.app.core.exceptions import AuthLimitReached, AnonymousLimitReached, InvalidCredentials, InvalidInput, UserNotFound
from backend.app.services.conversion_service import (
    check_user_can_convert,
    check_credits_for_operation,
    consume_credit_for_operation,
    credits_remaining_for_user,
    increment_user_conversion_count,
)
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.anonymous_session import AnonymousSession
from backend.app.models.conversion import Conversion
from backend.app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_check_user_can_convert_limit_reached(db_session: AsyncSession):
    user = User(
        email="limit@example.com",
        hashed_password=get_password_hash("x"),
        full_name="Limit User",
        auth_provider="email",
        free_conversion_count=settings.FREE_TIER_CONVERSIONS_LIMIT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    with pytest.raises(AuthLimitReached):
        await check_user_can_convert(db_session, user.id)


@pytest.mark.asyncio
async def test_check_user_can_convert_user_not_found(db_session: AsyncSession):
    with pytest.raises(UserNotFound):
        await check_user_can_convert(db_session, 99999)


@pytest.mark.asyncio
async def test_check_credits_for_operation_no_credentials(db_session: AsyncSession):
    with pytest.raises(InvalidCredentials):
        await check_credits_for_operation(db_session, None, None)


@pytest.mark.asyncio
async def test_check_credits_for_operation_invalid_anonymous_id(db_session: AsyncSession):
    with pytest.raises(InvalidInput):
        await check_credits_for_operation(db_session, None, "not-a-uuid")


@pytest.mark.asyncio
async def test_check_credits_for_operation_anonymous_creates_session(db_session: AsyncSession):
    import uuid
    sid = str(uuid.uuid4())
    entity, is_anon = await check_credits_for_operation(db_session, None, sid)
    assert is_anon is True
    assert entity.id == sid
    assert entity.conversions_count == 0


@pytest.mark.asyncio
async def test_check_credits_anonymous_limit_reached(db_session: AsyncSession):
    import uuid
    sid = str(uuid.uuid4())
    anon = AnonymousSession(id=sid, conversions_count=settings.ANONYMOUS_CONVERSIONS_LIMIT)
    db_session.add(anon)
    await db_session.commit()

    with pytest.raises(AnonymousLimitReached):
        await check_credits_for_operation(db_session, None, sid)


def test_credits_remaining_for_user():
    user = User(free_conversion_count=2)
    limit = settings.FREE_TIER_CONVERSIONS_LIMIT
    assert credits_remaining_for_user(user) == max(0, limit - 2)


def test_increment_user_conversion_count():
    user = User(free_conversion_count=1)
    increment_user_conversion_count(user, is_superuser=False)
    assert user.free_conversion_count == 2
    increment_user_conversion_count(user, is_superuser=True)
    assert user.free_conversion_count == 2
