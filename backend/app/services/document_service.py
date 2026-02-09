"""
Document service - CRUD and permissions. Prioridad 3 - Service Layer.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.document import Document, DocumentPermission
from app.schemas.document import DocumentResponse
from app.core.exceptions import DocumentNotFound, Forbidden


async def create_document(
    db: AsyncSession,
    owner_id: int,
    title: str,
    original_format: str | None = None,
) -> Document:
    """Create a new document. Returns the created Document."""
    new_doc = Document(
        title=title,
        original_format=original_format or "",
        owner_id=owner_id,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return new_doc


async def list_my_documents(db: AsyncSession, user_id: int) -> list:
    """List documents owned by the user."""
    result = await db.execute(select(Document).where(Document.owner_id == user_id))
    return list(result.scalars().all())


async def get_document_with_role(
    db: AsyncSession,
    document_id: int,
    user_id: int,
) -> DocumentResponse:
    """Get document with current_user_role. Raises DocumentNotFound or Forbidden."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise DocumentNotFound("Document not found")
    resp = DocumentResponse.model_validate(doc)
    if doc.owner_id == user_id:
        resp.current_user_role = "owner"
        return resp
    perm_result = await db.execute(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id,
        )
    )
    perm = perm_result.scalar_one_or_none()
    if not perm:
        raise Forbidden("Not enough permissions")
    resp.current_user_role = perm.role
    return resp


async def get_permissions_list(
    db: AsyncSession,
    document_id: int,
    user_id: int,
) -> list:
    """List permissions for document. Raises DocumentNotFound or Forbidden if not owner."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise DocumentNotFound("Document not found")
    if doc.owner_id != user_id:
        raise Forbidden("Only owners can view permissions")
    perm_result = await db.execute(
        select(DocumentPermission)
        .where(DocumentPermission.document_id == document_id)
        .options(joinedload(DocumentPermission.user))
    )
    return list(perm_result.scalars().all())
