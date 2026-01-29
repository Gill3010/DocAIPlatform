from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # File information
    original_filename = Column(String)
    original_format = Column(String)
    target_format = Column(String)
    file_size = Column(Float)  # in MB
    
    # Storage paths
    input_file_path = Column(String)
    output_file_path = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    # user = relationship("User", back_populates="conversions")
