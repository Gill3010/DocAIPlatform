from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    """Solo campos editables en perfil. Email no se cambia por seguridad."""
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    free_conversion_count: int
    auth_provider: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserMeResponse(UserResponse):
    """Respuesta de GET /users/me: incluye flags de admin para el frontend."""
    is_superuser: bool = False
    can_access_admin_panel: bool = False

    class Config:
        from_attributes = True
