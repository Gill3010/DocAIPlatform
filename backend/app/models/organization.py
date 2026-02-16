from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Límites compartidos (opcional futuro)
    # monthly_credits_limit = Column(Integer, default=1000)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    members = relationship("User", back_populates="organization", foreign_keys="User.organization_id")
    owner = relationship("User", foreign_keys=[owner_id])
