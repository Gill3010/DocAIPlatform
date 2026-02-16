from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import Forbidden, AuthLimitReached
from app.models.user import User

router = APIRouter()

@router.post(
    "/format",
    summary="Formatear manuscrito (Solo Pro/Empresa)",
    description=(
        "Aplica formato profesional a un documento. "
        "Requiere plan Pro o Empresa. Los planes Gratuito y Básico no tienen acceso."
    ),
    responses={
        200: {"description": "Documento formateado"},
        403: {"description": "Acceso restringido (se requiere plan Pro o superior)"},
    },
)
async def format_manuscript(
    file: UploadFile = File(...),
    style: str = Form("standard"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Regla: Solo Plan Pro y superiores, o usuarios con acceso al panel admin
    if not current_user.is_superuser and not getattr(current_user, "can_access_admin_panel", False) and current_user.premium_plan_id not in ['Pro', 'Empresa']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="pro_plan_required"
        )
    
    # Placeholder for future implementation
    return {
        "message": "Esta funcionalidad estará disponible próximamente para usuarios Pro.",
        "status": "coming_soon",
        "plan": current_user.premium_plan_id
    }
