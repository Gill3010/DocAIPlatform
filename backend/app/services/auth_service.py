"""
Auth service - registration, login, verification, password reset, anonymous session linking.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
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
from app.models.auth_token import AuthToken
from app.models.anonymous_session import AnonymousSession
from app.services.email_service import send_verification_email, send_password_reset_email

# Expiración de tokens
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """Create a new user with email/password. Sends verification email. Raises InvalidInput if email exists."""
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise InvalidInput("Email already registered")
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name or "",
        auth_provider="email",
        email_verified_at=None,  # Requiere verificación
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generar token de verificación
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
    auth_token = AuthToken(
        token_hash=token_hash,
        user_id=user.id,
        purpose="email_verification",
        expires_at=expires_at,
    )
    db.add(auth_token)
    await db.commit()

    send_verification_email(user.email, token, user.full_name)
    return user, token


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[str, str]:
    """
    Validate credentials and return (access_token, token_type).
    Raises InvalidCredentials on failure.
    Rechaza cuentas email/password no verificadas.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise InvalidCredentials("Incorrect email or password")
    if not user.hashed_password:
        raise InvalidCredentials("This account uses social login. Use Google or Facebook to sign in.")
    if user.auth_provider == "email" and user.email_verified_at is None:
        raise InvalidCredentials("Please verify your email before signing in. Check your inbox.")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Incorrect email or password")
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=expires)
    return token, "bearer"


async def verify_email_token(db: AsyncSession, token: str) -> User:
    """Valida el token de verificación y marca el usuario como verificado. Raises InvalidInput si es inválido."""
    token_hash = _hash_token(token)
    result = await db.execute(
        select(AuthToken)
        .where(AuthToken.token_hash == token_hash, AuthToken.purpose == "email_verification")
        .limit(1)
    )
    auth_token = result.scalar_one_or_none()
    if not auth_token:
        raise InvalidInput("Invalid or expired verification link")
    if auth_token.used_at:
        raise InvalidInput("This link has already been used")
    now = datetime.now(timezone.utc)
    expires_at = auth_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise InvalidInput("This verification link has expired")

    user_result = await db.execute(select(User).where(User.id == auth_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise InvalidInput("User not found")

    auth_token.used_at = now
    user.email_verified_at = now
    await db.commit()
    await db.refresh(user)
    return user


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """
    Si existe un usuario con ese email (auth_provider=email), genera token y envía correo.
    Siempre retorna sin error (evitar enumeración de emails).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or user.auth_provider != "email" or not user.hashed_password:
        return

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    auth_token = AuthToken(
        token_hash=token_hash,
        user_id=user.id,
        purpose="password_reset",
        expires_at=expires_at,
    )
    db.add(auth_token)
    await db.commit()

    send_password_reset_email(user.email, token, user.full_name)


async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> None:
    """Valida el token de reset y actualiza la contraseña. Raises InvalidInput si es inválido."""
    token_hash = _hash_token(token)
    result = await db.execute(
        select(AuthToken)
        .where(AuthToken.token_hash == token_hash, AuthToken.purpose == "password_reset")
        .limit(1)
    )
    auth_token = result.scalar_one_or_none()
    if not auth_token:
        raise InvalidInput("Invalid or expired reset link")
    if auth_token.used_at:
        raise InvalidInput("This link has already been used")
    now = datetime.now(timezone.utc)
    expires_at = auth_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise InvalidInput("This reset link has expired")

    user_result = await db.execute(select(User).where(User.id == auth_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise InvalidInput("User not found")

    auth_token.used_at = now
    user.hashed_password = get_password_hash(new_password)
    await db.commit()


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
