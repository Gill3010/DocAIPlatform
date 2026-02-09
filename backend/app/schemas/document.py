from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DocumentBase(BaseModel):
    title: str
    original_format: str

class DocumentCreate(DocumentBase):
    pass

class UserSummary(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentPermissionResponse(BaseModel):
    user_id: int
    role: str
    user: Optional[UserSummary] = None

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: int
    owner_id: int
    initial_content: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    current_user_role: Optional[str] = None # 'owner', 'editor', 'viewer'
    
    class Config:
        from_attributes = True

class DocumentPermissionCreate(BaseModel):
    user_id: int
    role: str # 'viewer', 'editor'
