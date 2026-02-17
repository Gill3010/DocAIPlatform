from __future__ import annotations

import asyncio
from typing import Optional
import secrets
import uuid
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.turnstile import verify_turnstile_token
from app.core.security import (
    create_access_token,
    get_password_hash,
    get_current_user,
    verify_password,
)
from app.models.user import User
from app.models.anonymous_session import AnonymousSession
from app.core.rate_limit import check_forgot_password_rate_limit
from app.services.auth_service import (
    register_user as svc_register_user,
    authenticate_user as svc_authenticate_user,
    link_anonymous_session as svc_link_anonymous_session,
    verify_email_token as svc_verify_email_token,
    request_password_reset as svc_request_password_reset,
    reset_password_with_token as svc_reset_password_with_token,
)
from app.schemas.token import (
    FacebookAuthRequest,
    FacebookAuthUrlResponse,
    GoogleAuthRequest,
    GoogleAuthUrlResponse,
    LinkAnonymousSessionRequest,
    LinkAnonymousSessionResponse,
    Token,
    RegisterResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = "openid email profile"

FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_GRAPH_URL = "https://graph.facebook.com/v18.0/me"
FACEBOOK_SCOPES = "email,public_profile"

@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Registrar usuario",
    description="Crea una cuenta con email y contraseña. Envía correo de verificación; el usuario debe verificar antes de iniciar sesión. Requiere token Turnstile si está configurado.",
    responses={
        200: {"description": "Usuario creado; revisa tu correo para verificar la cuenta"},
        400: {"description": "Email ya registrado o verificación Turnstile fallida"},
    },
)
async def register(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if settings.TURNSTILE_SECRET_KEY:
        if not user.turnstile_token:
            raise HTTPException(status_code=400, detail="Verificación de seguridad requerida. Completa el captcha.")
        remote_ip = request.client.host if request.client else None
        if not await verify_turnstile_token(user.turnstile_token, remote_ip):
            raise HTTPException(status_code=400, detail="Verificación de seguridad fallida. Intenta de nuevo.")

    new_user, verify_token = await svc_register_user(
        db, email=user.email, password=user.password, full_name=user.full_name
    )

    base_url = settings.FRONTEND_URL.rstrip("/")
    resp = {
        "message": "Revisa tu correo para activar tu cuenta. Te enviamos un enlace de verificación.",
        "email": new_user.email,
    }
    if not settings.SES_ENABLED or not settings.SES_FROM_EMAIL:
        resp["verification_url"] = f"{base_url}/auth/verify-email?token={verify_token}"
        resp["message"] = "Cuenta creada. (SES no configurado: usa el enlace abajo para verificar)"
    return resp

@router.post(
    "/login",
    response_model=Token,
    summary="Login con email y contraseña",
    description="Autenticación con `username` (email) y `password`. Devuelve un JWT en `access_token`. Requiere token Turnstile si está configurado.",
    responses={
        200: {"description": "Token JWT generado correctamente"},
        400: {"description": "Verificación Turnstile fallida"},
        401: {"description": "Credenciales inválidas"},
        422: {"description": "Formato de body incorrecto"},
    },
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    turnstile_token: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if settings.TURNSTILE_SECRET_KEY:
        if not turnstile_token:
            raise HTTPException(status_code=400, detail="Verificación de seguridad requerida. Completa el captcha.")
        remote_ip = request.client.host if request.client else None
        if not await verify_turnstile_token(turnstile_token, remote_ip):
            raise HTTPException(status_code=400, detail="Verificación de seguridad fallida. Intenta de nuevo.")
    access_token, token_type = await svc_authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    return {"access_token": access_token, "token_type": token_type}


@router.post(
    "/link-anonymous-session",
    response_model=LinkAnonymousSessionResponse,
    summary="Vincular sesión anónima",
    description="Tras el login, vincula la sesión anónima al usuario. Transfiere los créditos usados en modo anónimo al contador del usuario. Requiere JWT.",
    responses={
        200: {"description": "Sesión vinculada; devuelve créditos usados y restantes"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Límite de créditos alcanzado u otra restricción"},
        422: {"description": "Error de validación (anonymous_session_id requerido)"},
    },
)
async def link_anonymous_session(
    data: LinkAnonymousSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vincula la sesión anónima al usuario recién autenticado.
    Transfiere las conversiones anónimas usadas al contador del usuario.
    """
    credits_used, credits_remaining = await svc_link_anonymous_session(
        db, current_user.id, data.anonymous_session_id
    )
    return LinkAnonymousSessionResponse(
        credits_used=credits_used,
        credits_remaining=credits_remaining,
    )


@router.post(
    "/verify-email",
    summary="Verificar correo",
    description="Valida el token de verificación enviado por email.",
    responses={
        200: {"description": "Email verificado correctamente"},
        400: {"description": "Token inválido o expirado"},
    },
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import InvalidInput
    import logging
    logger = logging.getLogger(__name__)
    try:
        user = await svc_verify_email_token(db, data.token)
        return {"verified": True, "email": user.email, "message": "Email verificado. Ya puedes iniciar sesión."}
    except InvalidInput as e:
        raise HTTPException(status_code=400, detail=e.detail)
    except Exception as e:
        logger.exception("verify_email failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error interno al verificar. Verifica que la migración de base de datos se ejecutó (migrate_auth_tokens.py).",
        )


@router.post(
    "/forgot-password",
    summary="Solicitar recuperación de contraseña",
    description="Envía un correo con enlace para restablecer contraseña. Siempre devuelve el mismo mensaje (evitar enumeración). Rate limit: 5 req/15min por IP.",
    responses={200: {"description": "Si el email existe, recibirás un correo"}},
)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    remote_ip = request.client.host if request.client else "unknown"
    if not check_forgot_password_rate_limit(remote_ip):
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Intenta de nuevo en 15 minutos.",
        )
    await svc_request_password_reset(db, data.email)
    return {"message": "Si existe una cuenta con ese email, recibirás un enlace para restablecer tu contraseña."}


@router.post(
    "/reset-password",
    summary="Restablecer contraseña con token",
    description="Valida el token recibido por email y actualiza la contraseña.",
    responses={
        200: {"description": "Contraseña actualizada. Ya puedes iniciar sesión."},
        400: {"description": "Token inválido o expirado"},
    },
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import InvalidInput
    try:
        await svc_reset_password_with_token(db, data.token, data.new_password)
        return {"message": "Contraseña actualizada. Ya puedes iniciar sesión."}
    except InvalidInput as e:
        raise HTTPException(status_code=400, detail=e.detail)


# --- Google OAuth ---


def _create_oauth_state(purpose: str = "google_oauth") -> str:
    """Crea un state firmado para CSRF."""
    payload = {"nonce": secrets.token_urlsafe(32), "purpose": purpose}
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def _verify_oauth_state(state: str, expected_purpose: Optional[str] = None) -> bool:
    """Verifica el state firmado."""
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if expected_purpose and payload.get("purpose") != expected_purpose:
            return False
        return True
    except JWTError:
        return False


def _build_google_auth_url(redirect_uri: str, state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


@router.get(
    "/google/url",
    response_model=GoogleAuthUrlResponse,
    summary="URL de autorización Google",
    description="Devuelve la URL de login con Google y un `state` para CSRF. El frontend redirige al usuario a `url`; tras el callback, enviar `code` y `state` a POST /auth/google.",
    responses={
        200: {"description": "URL y state para iniciar el flujo OAuth"},
        503: {"description": "Google login no configurado (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)"},
    },
)
async def get_google_auth_url(redirect_uri: Optional[str] = None):
    """Obtiene la URL de autorización de Google y el state para CSRF."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google login is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    base = (redirect_uri or settings.FRONTEND_URL).rstrip("/")
    redirect = base if base.endswith("/auth/callback") else f"{base}/auth/callback"
    state = _create_oauth_state("google_oauth")
    url = _build_google_auth_url(redirect, state)
    return GoogleAuthUrlResponse(url=url, state=state)


def _build_facebook_auth_url(redirect_uri: str, state: str) -> str:
    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": FACEBOOK_SCOPES,
        "state": state,
    }
    return f"{FACEBOOK_AUTH_URL}?{urllib.parse.urlencode(params)}"


@router.get(
    "/facebook/url",
    response_model=FacebookAuthUrlResponse,
    summary="URL de autorización Facebook",
    description="Devuelve la URL de login con Facebook y un `state` para CSRF. Tras el callback, enviar `code` y `state` a POST /auth/facebook.",
    responses={
        200: {"description": "URL y state para iniciar el flujo OAuth"},
        503: {"description": "Facebook login no configurado (FACEBOOK_APP_ID / FACEBOOK_APP_SECRET)"},
    },
)
async def get_facebook_auth_url(redirect_uri: Optional[str] = None):
    """Obtiene la URL de autorización de Facebook y el state para CSRF."""
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Facebook login is not configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET.",
        )
    base = (redirect_uri or settings.FRONTEND_URL).rstrip("/")
    redirect = base if base.endswith("/auth/callback/facebook") else f"{base}/auth/callback/facebook"
    state = _create_oauth_state("facebook_oauth")
    url = _build_facebook_auth_url(redirect, state)
    return FacebookAuthUrlResponse(url=url, state=state)


@router.post(
    "/google",
    response_model=Token,
    summary="Callback Google OAuth",
    description="Intercambia el `code` devuelto por Google tras el login por un JWT. Requiere el mismo `state` obtenido en GET /auth/google/url. Crea o actualiza el usuario y devuelve el token.",
    responses={
        200: {"description": "Token JWT generado correctamente"},
        400: {"description": "State inválido o expirado; código inválido; email no proporcionado por Google"},
        403: {"description": "Cuenta deshabilitada"},
        503: {"description": "Google login no configurado"},
    },
)
async def google_auth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Intercambia el código de Google por tokens y crea/inicia sesión del usuario."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Google login is not configured.",
        )

    if not _verify_oauth_state(data.state, "google_oauth"):
        raise HTTPException(status_code=400, detail="Invalid or expired state. Please try again.")

    redirect_uri = data.redirect_uri.rstrip("/")
    if not redirect_uri.endswith("/auth/callback"):
        redirect_uri = f"{redirect_uri}/auth/callback"

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": data.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_response.status_code != 200:
        err = token_response.json() if token_response.text else {}
        raise HTTPException(
            status_code=400,
            detail=err.get("error_description", "Failed to exchange code with Google."),
        )

    token_data = token_response.json()
    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="Google did not return an id_token.")

    def _verify_id_token():
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        return google_id_token.verify_oauth2_token(
            id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )

    try:
        idinfo = await asyncio.to_thread(_verify_id_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {e}")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google did not provide your email. Please grant email permission.",
        )

    name = idinfo.get("name") or idinfo.get("given_name") or ""
    provider_user_id = idinfo.get("sub", "")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled.")
        user.auth_provider = "google"
        user.provider_user_id = provider_user_id
        if user.full_name and not name:
            name = user.full_name
        user.full_name = name or user.full_name
        await db.commit()
        await db.refresh(user)
    else:
        user = User(
            email=email,
            full_name=name or None,
            hashed_password=None,
            auth_provider="google",
            provider_user_id=provider_user_id,
            email_verified_at=datetime.now(timezone.utc),  # OAuth verifica email
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


# --- Facebook (Meta) OAuth ---


@router.post(
    "/facebook",
    response_model=Token,
    summary="Callback Facebook OAuth",
    description="Intercambia el `code` devuelto por Facebook tras el login por un JWT. Requiere el mismo `state` obtenido en GET /auth/facebook/url. Crea o actualiza el usuario y devuelve el token.",
    responses={
        200: {"description": "Token JWT generado correctamente"},
        400: {"description": "State inválido o expirado; código inválido; email no proporcionado por Facebook"},
        403: {"description": "Cuenta deshabilitada"},
        503: {"description": "Facebook login no configurado"},
    },
)
async def facebook_auth(data: FacebookAuthRequest, db: AsyncSession = Depends(get_db)):
    """Intercambia el código de Facebook por tokens y crea/inicia sesión del usuario."""
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Facebook login is not configured.",
        )

    if not _verify_oauth_state(data.state, "facebook_oauth"):
        raise HTTPException(status_code=400, detail="Invalid or expired state. Please try again.")

    redirect_uri = data.redirect_uri.rstrip("/")
    if not redirect_uri.endswith("/auth/callback/facebook"):
        redirect_uri = f"{redirect_uri}/auth/callback/facebook"

    async with httpx.AsyncClient() as client:
        token_response = await client.get(
            FACEBOOK_TOKEN_URL,
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": data.code,
            },
        )

    if token_response.status_code != 200:
        err = token_response.json() if token_response.text else {}
        raise HTTPException(
            status_code=400,
            detail=err.get("error", {}).get("message", "Failed to exchange code with Facebook."),
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Facebook did not return an access token.")

    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            FACEBOOK_GRAPH_URL,
            params={"fields": "id,email,name", "access_token": access_token},
        )

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Facebook.")

    user_data = user_response.json()
    email = user_data.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Facebook no proporcionó tu email. Verifica los permisos en tu cuenta.",
        )

    name = user_data.get("name", "")
    provider_user_id = user_data.get("id", "")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled.")
        user.auth_provider = "facebook"
        user.provider_user_id = provider_user_id
        user.full_name = name or user.full_name
        await db.commit()
        await db.refresh(user)
    else:
        user = User(
            email=email,
            full_name=name or None,
            hashed_password=None,
            auth_provider="facebook",
            provider_user_id=provider_user_id,
            email_verified_at=datetime.now(timezone.utc),  # OAuth verifica email
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=jwt_token, token_type="bearer")
