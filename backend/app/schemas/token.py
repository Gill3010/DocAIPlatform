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
    user: Optional[UserResponse] = None
    access_token: str
    token_type: str
