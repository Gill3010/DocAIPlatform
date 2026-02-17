"""Tests for auth_service."""
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import InvalidInput, InvalidCredentials
from backend.app.services.auth_service import register_user, authenticate_user
from backend.app.core.security import get_password_hash
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session: AsyncSession):
    await register_user(db_session, "test@example.com", "secret123", "Test User")
    with pytest.raises(InvalidInput) as exc_info:
        await register_user(db_session, "test@example.com", "other456", "Other")
    assert "already registered" in str(exc_info.value.detail).lower() or "email" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession):
    user = await register_user(db_session, "new@example.com", "secret123", "New User")
    assert user.id is not None
    assert user.email == "new@example.com"
    assert user.hashed_password is not None
    assert user.auth_provider == "email"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession):
    user = User(
        email="auth@example.com",
        hashed_password=get_password_hash("correct"),
        full_name="Auth User",
        auth_provider="email",
        email_verified_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    with pytest.raises(InvalidCredentials):
        await authenticate_user(db_session, "auth@example.com", "wrongpassword")


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession):
    user = await register_user(db_session, "success@example.com", "mypassword", "Success User")
    user.email_verified_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(user)
    token, token_type = await authenticate_user(db_session, "success@example.com", "mypassword")
    assert token_type == "bearer"
    assert isinstance(token, str) and len(token) > 0
