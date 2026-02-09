"""
Panel de administrador. Todas las rutas exigen get_current_admin_user.
Prefijo: /api/v1/admin
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.models.conversion import Conversion
from app.models.admin_audit_log import AdminAuditLog
from app.schemas.admin import (
    AdminUserListItem,
    AdminUserDetail,
    AdminUserUpdate,
    AdminUsersListResponse,
    AdminConversionListItem,
    AdminConversionsListResponse,
    AdminActivityItem,
    AdminActivityListResponse,
)
from app.utils.admin_audit import log_admin_action
from datetime import datetime, date

router = APIRouter()

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _user_to_list_item(u: User) -> AdminUserListItem:
    return AdminUserListItem(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        is_active=u.is_active,
        is_superuser=getattr(u, "is_superuser", False),
        can_access_admin_panel=getattr(u, "can_access_admin_panel", False),
        auth_provider=getattr(u, "auth_provider", None),
        created_at=getattr(u, "created_at", None),
    )


@router.get(
    "/me",
    summary="Admin actual",
    description="Devuelve el usuario admin actual (id, email, full_name, is_superuser, can_access_admin_panel). Comprueba que el JWT pertenece a un usuario con acceso al panel. Requiere JWT de admin.",
    responses={
        200: {"description": "Datos del admin actual"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
    },
)
async def admin_me(current_user: User = Depends(get_current_admin_user)):
    """Devuelve el usuario admin actual (comprueba acceso al panel)."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_superuser": getattr(current_user, "is_superuser", False),
        "can_access_admin_panel": getattr(current_user, "can_access_admin_panel", False),
    }


@router.get(
    "/stats",
    summary="Estadísticas globales",
    description="Estadísticas para el panel: total/activos de usuarios, total/completadas de conversiones. Requiere JWT de admin.",
    responses={
        200: {"description": "users (total, active), conversions (total, completed)"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
    },
)
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Estadísticas globales para el panel (usuarios, conversiones)."""
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0
    result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = result.scalar() or 0
    result = await db.execute(select(func.count(Conversion.id)))
    total_conversions = result.scalar() or 0
    result = await db.execute(
        select(func.count(Conversion.id)).where(Conversion.status == "completed")
    )
    completed_conversions = result.scalar() or 0
    return {
        "users": {"total": total_users, "active": active_users},
        "conversions": {"total": total_conversions, "completed": completed_conversions},
    }


@router.get(
    "/users",
    response_model=AdminUsersListResponse,
    summary="Listar usuarios",
    description="Lista usuarios con paginación (page, size) y filtros opcionales: email (búsqueda parcial), is_active. Requiere JWT de admin.",
    responses={
        200: {"description": "items, total, page, size, pages"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
    },
)
async def admin_list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    email: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """Lista usuarios con paginación y filtros opcionales."""
    base = select(User)
    count_stmt = select(func.count(User.id))
    if email and email.strip():
        search = f"%{email.strip()}%"
        base = base.where(User.email.like(search))
        count_stmt = count_stmt.where(User.email.like(search))
    if is_active is not None:
        base = base.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    offset = (page - 1) * size
    base = base.order_by(User.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(base)
    users = result.scalars().all()
    pages = (total + size - 1) // size if total else 0
    return AdminUsersListResponse(
        items=[_user_to_list_item(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Detalle de usuario",
    description="Devuelve el detalle de un usuario (sin contraseña): perfil, créditos (free_conversion_count, ai_message_count), últimas 10 conversiones. Requiere JWT de admin.",
    responses={
        200: {"description": "Usuario con last_conversions"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
async def admin_get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Detalle de un usuario (sin contraseña) y últimas conversiones."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    last_conv = await db.execute(
        select(Conversion)
        .where(Conversion.user_id == user_id)
        .order_by(Conversion.created_at.desc())
        .limit(10)
    )
    conversions = last_conv.scalars().all()
    last_conversions = [
        {
            "id": c.id,
            "original_filename": c.original_filename,
            "original_format": c.original_format,
            "target_format": c.target_format,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversions
    ]

    detail = AdminUserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=getattr(user, "is_superuser", False),
        can_access_admin_panel=getattr(user, "can_access_admin_panel", False),
        auth_provider=getattr(user, "auth_provider", None),
        created_at=getattr(user, "created_at", None),
        free_conversion_count=getattr(user, "free_conversion_count", 0),
        ai_message_count=getattr(user, "ai_message_count", 0),
        avatar_url=getattr(user, "avatar_url", None),
        last_conversions=last_conversions,
    )
    return detail


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="Actualizar usuario (admin)",
    description="Activar/desactivar usuario (is_active) o asignar/revocar acceso al panel admin (can_access_admin_panel). No se puede cambiar can_access_admin_panel en superusers. Se registra en audit log. Requiere JWT de admin.",
    responses={
        200: {"description": "Usuario actualizado con last_conversions"},
        400: {"description": "No se puede cambiar can_access_admin_panel en un superuser"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Error de validación del body"},
    },
)
async def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Activar/desactivar usuario o asignar/revocar acceso al panel admin."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.is_active is not None:
        user.is_active = body.is_active
        await log_admin_action(
            db,
            current_user.id,
            "user_deactivate" if not body.is_active else "user_activate",
            "user",
            str(user_id),
            f"is_active={body.is_active}",
        )
    if body.can_access_admin_panel is not None:
        if user.is_superuser:
            raise HTTPException(
                status_code=400,
                detail="Cannot change can_access_admin_panel for a superuser.",
            )
        user.can_access_admin_panel = body.can_access_admin_panel
        await log_admin_action(
            db,
            current_user.id,
            "admin_revoke" if not body.can_access_admin_panel else "admin_assign",
            "user",
            str(user_id),
            f"can_access_admin_panel={body.can_access_admin_panel}",
        )

    await db.commit()
    await db.refresh(user)

    last_conv = await db.execute(
        select(Conversion)
        .where(Conversion.user_id == user_id)
        .order_by(Conversion.created_at.desc())
        .limit(10)
    )
    conversions = last_conv.scalars().all()
    last_conversions = [
        {
            "id": c.id,
            "original_filename": c.original_filename,
            "original_format": c.original_format,
            "target_format": c.target_format,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversions
    ]

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=getattr(user, "is_superuser", False),
        can_access_admin_panel=getattr(user, "can_access_admin_panel", False),
        auth_provider=getattr(user, "auth_provider", None),
        created_at=getattr(user, "created_at", None),
        free_conversion_count=getattr(user, "free_conversion_count", 0),
        ai_message_count=getattr(user, "ai_message_count", 0),
        avatar_url=getattr(user, "avatar_url", None),
        last_conversions=last_conversions,
    )


@router.get(
    "/conversions",
    response_model=AdminConversionsListResponse,
    summary="Listar conversiones",
    description="Lista todas las conversiones con paginación (page, size) y filtros opcionales: user_id, status, date_from, date_to. Requiere JWT de admin.",
    responses={
        200: {"description": "items, total, page, size, pages"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
    },
)
async def admin_list_conversions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    """Lista conversiones globales con paginación y filtros."""
    base = select(Conversion)
    count_stmt = select(func.count(Conversion.id))
    if user_id is not None:
        base = base.where(Conversion.user_id == user_id)
        count_stmt = count_stmt.where(Conversion.user_id == user_id)
    if status and status.strip():
        base = base.where(Conversion.status == status.strip())
        count_stmt = count_stmt.where(Conversion.status == status.strip())
    if date_from is not None:
        base = base.where(Conversion.created_at >= datetime.combine(date_from, datetime.min.time()))
        count_stmt = count_stmt.where(Conversion.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to is not None:
        base = base.where(Conversion.created_at <= datetime.combine(date_to, datetime.max.time()))
        count_stmt = count_stmt.where(Conversion.created_at <= datetime.combine(date_to, datetime.max.time()))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    offset = (page - 1) * size
    base = base.order_by(Conversion.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(base)
    conversions = result.scalars().all()
    pages = (total + size - 1) // size if total else 0
    items = [
        AdminConversionListItem(
            id=c.id,
            user_id=c.user_id,
            anonymous_session_id=c.anonymous_session_id,
            original_filename=c.original_filename,
            original_format=c.original_format,
            target_format=c.target_format,
            status=c.status,
            file_size=c.file_size,
            created_at=c.created_at,
            completed_at=c.completed_at,
        )
        for c in conversions
    ]
    return AdminConversionsListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get(
    "/activity",
    response_model=AdminActivityListResponse,
    summary="Audit log",
    description="Lista el historial de acciones del panel admin (audit log): user_activate, user_deactivate, admin_assign, admin_revoke, etc. Paginación (page, size) y filtro opcional por action. Requiere JWT de admin.",
    responses={
        200: {"description": "items, total, page, size, pages"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario sin acceso al panel admin"},
    },
)
async def admin_list_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    action: Optional[str] = Query(None),
):
    """Lista el historial de acciones del panel admin (audit log)."""
    base = select(AdminAuditLog)
    count_stmt = select(func.count(AdminAuditLog.id))
    if action and action.strip():
        base = base.where(AdminAuditLog.action == action.strip())
        count_stmt = count_stmt.where(AdminAuditLog.action == action.strip())

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    offset = (page - 1) * size
    base = base.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(base)
    logs = result.scalars().all()
    pages = (total + size - 1) // size if total else 0
    items = [
        AdminActivityItem(
            id=log.id,
            admin_user_id=log.admin_user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
    return AdminActivityListResponse(items=items, total=total, page=page, size=size, pages=pages)
