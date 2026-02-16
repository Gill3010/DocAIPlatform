from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    turnstile_token: Optional[str] = None  # Para Cloudflare Turnstile (registro)

class UserUpdate(BaseModel):
    """Solo campos editables en perfil. Email no se cambia por seguridad."""
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_premium: bool = False
    premium_plan_id: Optional[str] = None
    free_conversion_count: int
    monthly_conversion_count: int = 0
    last_billing_reset: Optional[datetime] = None
    auth_provider: Optional[str] = None
    avatar_url: Optional[str] = None
    can_view_payments: bool = False

    class Config:
        from_attributes = True


class UserMeResponse(UserResponse):
    """Respuesta de GET /users/me: incluye flags de admin para el frontend."""
    is_superuser: bool = False
    can_access_admin_panel: bool = False

    class Config:
        from_attributes = True
