from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConversionBase(BaseModel):
    original_filename: str
    original_format: str
    target_format: str
    file_size: float

class ConversionCreate(ConversionBase):
    user_id: int
    input_file_path: str

class ConversionResponse(ConversionBase):
    id: int
    user_id: int
    status: str
    input_file_path: str
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConversionUploadResponse(BaseModel):
    message: str
    conversion_id: int
    status: str
    credits_remaining: int
