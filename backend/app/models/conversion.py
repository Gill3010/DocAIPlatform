from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # For history/list by user
    anonymous_session_id = Column(String(36), nullable=True, index=True)  # For anonymous conversions
    
    # File information
    original_filename = Column(String)
    original_format = Column(String)
    target_format = Column(String)
    file_size = Column(Float)  # in MB
    
    # Storage paths
    input_file_path = Column(String)
    output_file_path = Column(String, nullable=True)
    
    # Status tracking (index for admin filters)
    status = Column(String, default="pending", index=True)  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    
    # Timestamps (index for ordering in history/list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    # user = relationship("User", back_populates="conversions")
