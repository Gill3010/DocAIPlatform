from __future__ import annotations

import uuid
from pathlib import Path

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.user_service import get_user_by_id, update_user_profile, validate_avatar
from app.models.conversion import Conversion
from app.models.pdf_tool_use import PdfToolUse
from app.schemas.user import UserResponse, UserMeResponse, UserUpdate

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads" / "avatars"


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Perfil del usuario",
    description="Devuelve el perfil del usuario autenticado: email, nombre, créditos, avatar, flags is_superuser y can_access_admin_panel. Requiere JWT.",
    responses={
        200: {"description": "Perfil del usuario"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Usuario no encontrado"},
    },
)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve el perfil del usuario autenticado (incluye flags de admin para el frontend)."""
    user = await get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Actualizar perfil",
    description="Actualiza full_name y/o password. Solo usuarios con login email pueden cambiar contraseña. Requiere JWT.",
    responses={
        200: {"description": "Perfil actualizado"},
        400: {"description": "Datos inválidos (ej. contraseña demasiado corta)"},
        401: {"description": "Token ausente o inválido"},
        422: {"description": "Error de validación"},
    },
)
async def update_current_user_profile(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualiza nombre y/o contraseña. Solo usuarios email pueden cambiar contraseña."""
    return await update_user_profile(
        db, current_user.id,
        full_name=body.full_name,
        password=body.password,
    )


@router.post(
    "/me/avatar",
    response_model=UserResponse,
    summary="Subir avatar",
    description="Sube una imagen como avatar. Acepta JPEG, PNG, GIF, WebP (máx. 5 MB). Requiere JWT.",
    responses={
        200: {"description": "Avatar actualizado; devuelve usuario con avatar_url"},
        400: {"description": "Tipo de archivo no permitido o tamaño > 5 MB"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Error de validación"},
    },
)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sube una imagen como avatar. Acepta JPEG, PNG, GIF, WebP (máx. 5 MB)."""
    content = await file.read()
    validate_avatar(file.content_type or "", len(content))
    user = await get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "img").suffix.lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)

    # URL que el frontend puede usar (static mount en main)
    avatar_url = f"/static/uploads/avatars/{filename}"
    user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "/anon-stats",
    summary="Estadísticas anónimas",
    description="Estadísticas para sesión anónima: conversiones totales/completadas, usos de PDF tools, tasa de éxito y tiempo medio. Requiere header X-Anonymous-Session-Id (UUID). No requiere JWT.",
    responses={
        200: {"description": "conversions, pdf_tool_uses, success_rate, avg_processing_time"},
        400: {"description": "X-Anonymous-Session-Id ausente o no es un UUID válido"},
    },
)
async def get_anonymous_stats(
    db: AsyncSession = Depends(get_db),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """
    Estadísticas para sesión anónima: tasa de éxito y tiempo promedio.
    Incluye conversiones de documento (Conversion) y usos de herramientas PDF (PdfToolUse).
    Requiere cabecera X-Anonymous-Session-Id. No requiere autenticación.
    """
    if not x_anonymous_session_id:
        raise HTTPException(status_code=400, detail="X-Anonymous-Session-Id required")
    try:
        uuid.UUID(x_anonymous_session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Anonymous-Session-Id")

    # Conversiones de documento
    result = await db.execute(
        select(func.count(Conversion.id)).where(
            Conversion.anonymous_session_id == x_anonymous_session_id
        )
    )
    total_conversions = result.scalar() or 0

    result = await db.execute(
        select(func.count(Conversion.id)).where(
            Conversion.anonymous_session_id == x_anonymous_session_id,
            Conversion.status == "completed",
        )
    )
    completed_conversions = result.scalar() or 0

    # Usos de herramientas PDF (todos exitosos)
    result = await db.execute(
        select(func.count(PdfToolUse.id)).where(
            PdfToolUse.anonymous_session_id == x_anonymous_session_id
        )
    )
    pdf_tool_uses = result.scalar() or 0

    total_uses = total_conversions + pdf_tool_uses
    completed_uses = completed_conversions + pdf_tool_uses
    success_rate = round((completed_uses / total_uses) * 100, 1) if total_uses else 0

    # Tiempo promedio: conversiones con (completed_at - created_at); PDF tools cuentan como 0s
    result = await db.execute(
        select(Conversion.created_at, Conversion.completed_at).where(
            Conversion.anonymous_session_id == x_anonymous_session_id,
            Conversion.status == "completed",
            Conversion.completed_at.isnot(None),
        )
    )
    rows = result.all()
    conversion_seconds = sum(
        (r.completed_at - r.created_at).total_seconds() for r in rows if r.completed_at and r.created_at
    )
    n_total = completed_conversions + pdf_tool_uses
    if n_total == 0:
        avg_processing_time = "—"
    else:
        avg_sec = conversion_seconds / n_total
        avg_processing_time = f"{avg_sec:.1f}s"

    return {
        "conversions": {"total": total_conversions, "completed": completed_conversions},
        "pdf_tool_uses": pdf_tool_uses,
        "success_rate": success_rate,
        "avg_processing_time": avg_processing_time,
    }


@router.get(
    "/me/stats",
    summary="Estadísticas del usuario",
    description="Estadísticas para el dashboard: conversiones (total, completadas, fallidas), créditos usados/restantes, tasa de éxito, tiempo medio, almacenamiento, última conversión. Requiere JWT.",
    responses={
        200: {"description": "user, conversions, credits, success_rate, avg_processing_time, storage, last_conversion"},
        401: {"description": "Token ausente o inválido"},
    },
)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user statistics for dashboard
    """
    # Total conversions
    result = await db.execute(
        select(func.count(Conversion.id))
        .where(Conversion.user_id == current_user.id)
    )
    total_conversions = result.scalar() or 0
    
    # Completed conversions
    result = await db.execute(
        select(func.count(Conversion.id))
        .where(
            Conversion.user_id == current_user.id,
            Conversion.status == 'completed'
        )
    )
    completed_conversions = result.scalar() or 0
    
    # Failed conversions
    result = await db.execute(
        select(func.count(Conversion.id))
        .where(
            Conversion.user_id == current_user.id,
            Conversion.status == 'failed'
        )
    )
    failed_conversions = result.scalar() or 0
    
    # Calculate success rate
    success_rate = 0
    if total_conversions > 0:
        success_rate = round((completed_conversions / total_conversions) * 100, 1)
    
    # Credits remaining (admin panel users have unlimited like Pro/Empresa)
    is_premium = getattr(current_user, "is_premium", False) or getattr(current_user, "is_superuser", False) or getattr(current_user, "can_access_admin_panel", False)
    plan_id = getattr(current_user, "premium_plan_id", None)

    if is_premium:
        if plan_id == 'Básico' and not getattr(current_user, "can_access_admin_panel", False):
            free_tier_limit = 50
            credits_used = getattr(current_user, "monthly_conversion_count", 0)
            credits_remaining = max(0, 50 - credits_used)
        else:
            # Pro, Empresa, Superuser
            credits_remaining = 999999
            free_tier_limit = 999999
            credits_used = getattr(current_user, "monthly_conversion_count", 0) or int(completed_conversions)
    else:
        free_tier_limit = settings.FREE_TIER_CONVERSIONS_LIMIT
        credits_used = max(current_user.free_conversion_count, int(completed_conversions))
        credits_remaining = max(0, free_tier_limit - credits_used)
    
    # Average processing time (mock for now, would need to add processing_time column)
    avg_processing_time = "2.4s"
    
    # Total storage used (sum of file sizes)
    result = await db.execute(
        select(func.sum(Conversion.file_size))
        .where(Conversion.user_id == current_user.id)
    )
    total_storage_mb = result.scalar() or 0
    
    # Last conversion
    result = await db.execute(
        select(Conversion)
        .where(Conversion.user_id == current_user.id)
        .order_by(Conversion.created_at.desc())
        .limit(1)
    )
    last_conversion = result.scalar_one_or_none()
    
    return {
        "user": {
            "name": current_user.full_name or "User",
            "email": current_user.email,
            "avatar_url": getattr(current_user, "avatar_url", None),
            "is_premium": is_premium,
            "premium_plan_id": getattr(current_user, "premium_plan_id", None)
        },
        "conversions": {
            "total": total_conversions,
            "completed": completed_conversions,
            "failed": failed_conversions,
            "processing": total_conversions - completed_conversions - failed_conversions
        },
        "credits": {
            "used": credits_used,
            "remaining": credits_remaining,
            "limit": free_tier_limit,
            "is_premium": is_premium
        },
        "success_rate": success_rate,
        "avg_processing_time": avg_processing_time,
        "storage": {
            "used_mb": round(total_storage_mb, 2),
            "limit_mb": 100  # Mock limit
        },
        "last_conversion": {
            "filename": last_conversion.original_filename if last_conversion else None,
            "date": last_conversion.created_at.isoformat() if last_conversion else None,
            "status": last_conversion.status if last_conversion else None
        } if last_conversion else None
    }

@router.get(
    "/search",
    response_model=List[UserResponse],
    summary="Buscar usuarios",
    description="Busca usuarios por email (mínimo 2 caracteres). Devuelve hasta 10 resultados; excluye al usuario actual. Para compartir documentos. Requiere JWT.",
    responses={
        200: {"description": "Lista de usuarios (id, email, full_name, etc.)"},
        401: {"description": "Token ausente o inválido"},
    },
)
async def search_users(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Busca usuarios por email para compartir documentos."""
    if len(query) < 2:
        return []
        
    result = await db.execute(
        select(User).where(User.email.ilike(f"%{query}%")).limit(10)
    )
    users = result.scalars().all()
    # No devolver el usuario actual en la búsqueda
    return [u for u in users if u.id != current_user.id]
