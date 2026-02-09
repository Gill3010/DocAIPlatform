"""
User profile service - get, update, avatar. Prioridad 3 - Service Layer.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash
from app.core.exceptions import CannotChangePasswordSocial, InvalidInput, UserNotFound

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Load user by id. Returns None if not found."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    full_name: str | None = None,
    password: str | None = None,
) -> User:
    """Update user full_name and/or password. Returns updated User. Raises AppException if invalid."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound("User not found")
    if full_name is not None:
        user.full_name = full_name.strip() or None
    if password is not None and password.strip():
        if getattr(user, "auth_provider", "email") != "email":
            raise CannotChangePasswordSocial()
        user.hashed_password = get_password_hash(password)
    await db.commit()
    await db.refresh(user)
    return user


def validate_avatar(content_type: str, content_size: int) -> None:
    """Raises InvalidInput if invalid."""
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise InvalidInput("Invalid file type. Use JPEG, PNG, GIF or WebP.")
    if content_size > MAX_AVATAR_SIZE:
        raise InvalidInput("File too large (max 5 MB).")
