"""Helper para registrar acciones en admin_audit_log."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_audit_log import AdminAuditLog


async def log_admin_action(
    db: AsyncSession,
    admin_user_id: int,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: str | None = None,
) -> None:
    entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(entry)
    await db.flush()
