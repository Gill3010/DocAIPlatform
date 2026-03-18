from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ManuscriptFormatResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    file_size: float
    output_file_path: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
