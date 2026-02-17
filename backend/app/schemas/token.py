from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class GoogleAuthUrlResponse(BaseModel):
    url: str
    state: str


class GoogleAuthRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class FacebookAuthRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class FacebookAuthUrlResponse(BaseModel):
    url: str
    state: str


class LinkAnonymousSessionRequest(BaseModel):
    anonymous_session_id: str


class LinkAnonymousSessionResponse(BaseModel):
    credits_used: int
    credits_remaining: int


from app.schemas.user import UserResponse


class RegisterResponse(BaseModel):
    """Cuando se requiere verificación: message y email. Sin token hasta verificar."""
    message: Optional[str] = None
    email: Optional[str] = None
    verification_url: Optional[str] = None  # Solo cuando SES no configurado (para pruebas)
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str
