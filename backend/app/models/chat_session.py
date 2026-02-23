from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    """Sesión de chat del asistente IA. Usuario o anónimo."""
    __tablename__ = "ai_chat_sessions"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    anonymous_session_id = Column(String(36), nullable=True, index=True)
    title = Column(String(256), nullable=True)  # Primera pregunta truncada o "Nuevo chat"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
