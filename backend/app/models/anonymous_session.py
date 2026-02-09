from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class AnonymousSession(Base):
    __tablename__ = "anonymous_sessions"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    conversions_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
