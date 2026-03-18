from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.database import Base


class ManuscriptFormat(Base):
    __tablename__ = "manuscript_formats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # File information
    original_filename = Column(String)
    file_size = Column(Float)  # in MB

    # Storage path of the formatted output
    output_file_path = Column(String, nullable=True)

    # Status tracking
    status = Column(String, default="completed", index=True)  # completed, failed
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
