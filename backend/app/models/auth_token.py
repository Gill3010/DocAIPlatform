"""Modelo para tokens de verificación de email y reset de contraseña."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class AuthToken(Base):
    """Tokens de un solo uso para verificación de email y reset de contraseña."""
    __tablename__ = "auth_tokens"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String(32), nullable=False)  # 'email_verification' | 'password_reset'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
