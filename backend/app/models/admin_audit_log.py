from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # e.g. user_deactivate, admin_revoke
    resource_type = Column(String(32), nullable=False)  # user, conversion, etc.
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)  # JSON or text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
