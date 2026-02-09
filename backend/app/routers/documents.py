from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.conversion import Conversion
from app.models.document import Document, DocumentPermission
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentPermissionCreate, DocumentPermissionResponse
from app.services.document_service import (
    create_document as svc_create_document,
    list_my_documents as svc_list_my_documents,
    get_document_with_role as svc_get_document_with_role,
    get_permissions_list as svc_get_permissions_list,
)
from app.utils.text_extractor import extract_text_from_file
from pathlib import Path

router = APIRouter()

@router.post(
    "/",
    response_model=DocumentResponse,
    summary="Crear documento",
    description="Crea un nuevo documento para edición colaborativa. Requiere JWT. Body: title, original_format.",
    responses={
        200: {"description": "Documento creado"},
        401: {"description": "Token ausente o inválido"},
        422: {"description": "Error de validación (title, original_format)"},
    },
)
async def create_document(
    doc: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo documento para edición colaborativa."""
    return await svc_create_document(db, current_user.id, doc.title, doc.original_format)

@router.get(
    "/",
    response_model=List[DocumentResponse],
    summary="Listar documentos",
    description="Lista los documentos donde el usuario es dueño o tiene permiso (viewer/editor). Requiere JWT.",
    responses={
        200: {"description": "Lista de documentos"},
        401: {"description": "Token ausente o inválido"},
    },
)
async def list_my_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista los documentos donde el usuario es dueño o tiene permisos."""
    return await svc_list_my_documents(db, current_user.id)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Obtener documento",
    description="Devuelve los detalles de un documento si el usuario tiene permiso (dueño, viewer o editor). Requiere JWT.",
    responses={
        200: {"description": "Documento"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Documento no encontrado o sin permiso"},
    },
)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene detalles de un documento si tiene permiso."""
    return await svc_get_document_with_role(db, document_id, current_user.id)

@router.get(
    "/{document_id}/permissions",
    response_model=List[DocumentPermissionResponse],
    summary="Listar permisos",
    description="Lista los permisos del documento. Solo el dueño puede ver/gestar permisos. Requiere JWT.",
    responses={
        200: {"description": "Lista de permisos (user_id, role)"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Solo el dueño puede ver permisos"},
        404: {"description": "Documento no encontrado"},
    },
)
async def get_permissions(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de usuarios con permisos en el documento (solo dueño)."""
    return await svc_get_permissions_list(db, document_id, current_user.id)

@router.post(
    "/{document_id}/permissions",
    status_code=status.HTTP_201_CREATED,
    summary="Añadir permiso",
    description="Asigna permiso (viewer o editor) a otro usuario por user_id. Solo el dueño puede hacerlo. Requiere JWT.",
    responses={
        201: {"description": "Permiso añadido correctamente"},
        400: {"description": "role inválido (debe ser viewer o editor) o el usuario ya tiene permiso"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Solo el dueño puede gestionar permisos"},
        404: {"description": "Documento no encontrado"},
    },
)
async def add_permission(
    document_id: int,
    perm: DocumentPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Asigna permisos a otro usuario (solo el dueño puede hacerlo)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owners can manage permissions")
        
    if perm.role not in ['viewer', 'editor']:
         raise HTTPException(status_code=400, detail="Invalid role. Must be 'viewer' or 'editor'")

    # Check if permission already exists
    existing_perm = await db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == perm.user_id
        )
    )
    if existing_perm.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="User already has permission")

    new_perm = DocumentPermission(
        document_id=document_id,
        user_id=perm.user_id,
        role=perm.role
    )
    db.add(new_perm)
    await db.commit()
    return {"message": "Permission added successfully"}

@router.delete(
    "/{document_id}/permissions/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar permiso",
    description="Revoca el permiso de un usuario sobre el documento. Solo el dueño puede hacerlo. Requiere JWT.",
    responses={
        204: {"description": "Permiso eliminado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Solo el dueño puede gestionar permisos"},
        404: {"description": "Documento o permiso no encontrado"},
    },
)
async def remove_permission(
    document_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoca permisos de un usuario (solo el dueño puede hacerlo)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owners can manage permissions")
        
    perm_result = await db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id
        )
    )
    perm = perm_result.scalar_one_or_none()
    
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
        
    await db.delete(perm)
    await db.commit()
    return None

@router.post(
    "/from-conversion/{conversion_id}",
    response_model=DocumentResponse,
    summary="Documento desde conversión",
    description="Crea un documento de edición colaborativa a partir de una conversión completada del usuario. Extrae texto del archivo convertido. Requiere JWT.",
    responses={
        200: {"description": "Documento creado"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Conversión no encontrada o no completada"},
    },
)
async def create_from_conversion(
    conversion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un documento para edición colaborativa a partir de una conversión finalizada."""
    # 1. Fetch conversion
    result = await db.execute(select(Conversion).where(
        Conversion.id == conversion_id,
        Conversion.user_id == current_user.id
    ))
    conversion = result.scalar_one_or_none()
    
    if not conversion or conversion.status != "completed":
        raise HTTPException(
            status_code=404, 
            detail="Conversion not found or not completed"
        )
    
    # 2. Extract content
    output_path = Path(conversion.output_file_path)
    # Check if relative path needs fixing (assuming it's relative to project root)
    if not output_path.exists():
        # Try relative to current working directory if it was saved as relative
        output_path = Path(__file__).resolve().parent.parent.parent.parent / conversion.output_file_path

    content_text = extract_text_from_file(output_path)
    
    # 3. Create document
    new_doc = Document(
        title=f"Editade: {conversion.original_filename}",
        original_format=conversion.target_format,
        initial_content=content_text,
        owner_id=current_user.id
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    return new_doc

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar documento",
    description="Elimina un documento. Solo el dueño puede hacerlo. Requiere JWT.",
    responses={
        204: {"description": "Documento eliminado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Solo el dueño puede eliminar el documento"},
        404: {"description": "Documento no encontrado"},
    },
)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento (solo el dueño puede hacerlo)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owners can delete documents")
        
    await db.delete(doc)
    await db.commit()
    return None
