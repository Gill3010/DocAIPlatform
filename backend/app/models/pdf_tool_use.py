"""Registro de cada uso exitoso de una herramienta PDF (para métricas: tasa de éxito, tiempo promedio)."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class PdfToolUse(Base):
    __tablename__ = "pdf_tool_uses"

    id = Column(Integer, primary_key=True, index=True)
    anonymous_session_id = Column(String(36), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    tool_name = Column(String(64), nullable=False, index=True)  # merge, split, rotate, ...
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
