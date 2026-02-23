from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from pathlib import Path
import os

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.core.security import get_current_user_optional
from app.core import config as app_config
from app.models.user import User
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.services.ai_service import (
    check_ai_can_send,
    consume_ai_credit,
    get_ai_credits_response,
    get_or_create_anonymous_session,
)
from app.services.ai_agent_service import invoke_claude, AIAgentServiceError
from app.utils.text_extractor import extract_text_from_file

router = APIRouter()

# Store for uploaded attachments: attachment_id -> {"extracted_text": str, "filename": str}
# Ephemeral; cleared on restart. For production, use Redis or DB table.
_attachment_store: dict[str, dict] = {}

# Dir for temp uploads (AI chat attachments)
AI_ATTACHMENTS_DIR = Path(app_config.BACKEND_DIR) / "static" / "uploads" / "ai_attachments"
AI_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_UPLOAD_EXT = {".pdf", ".docx", ".doc", ".txt"}
MAX_ATTACHMENT_SIZE_MB = 5


# --- Pydantic models ---
class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    attachment_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    message: str
    credits_remaining: int
    session_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class CreateSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str


async def _resolve_entity(db: AsyncSession, current_user: Optional[User], x_anonymous_session_id: Optional[str]):
    """Resolve user or anonymous session for chat ownership."""
    if current_user:
        return current_user.id, None
    if not x_anonymous_session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    anon = await get_or_create_anonymous_session(db, x_anonymous_session_id)
    return None, anon.id


async def _get_sessions_for_entity(
    db: AsyncSession, user_id: Optional[int], anonymous_session_id: Optional[str]
) -> list[ChatSession]:
    if user_id is not None:
        result = await db.execute(
            select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        )
    else:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.anonymous_session_id == anonymous_session_id)
            .order_by(ChatSession.updated_at.desc())
        )
    return list(result.scalars().all())


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Enviar mensaje al asistente IA",
    description="Envía un mensaje al asistente IA (Bedrock/Claude). Soporta sesiones y adjuntos.",
    responses={
        200: {"description": "Respuesta del asistente y credits_remaining"},
        401: {"description": "No autenticado (anon requiere X-Anonymous-Session-Id)"},
        403: {"description": "Límite de créditos alcanzado"},
        503: {"description": "Servicio IA no disponible"},
    },
)
async def chat_with_ai(
    chat_message: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    try:
        return await _chat_with_ai_impl(
            chat_message, db, current_user, x_anonymous_session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat AI error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está disponible. Inténtalo de nuevo.",
        ) from e


async def _chat_with_ai_impl(
    chat_message: ChatMessageRequest,
    db: AsyncSession,
    current_user: Optional[User],
    x_anonymous_session_id: Optional[str],
):
    entity, is_anonymous = await check_ai_can_send(db, current_user, x_anonymous_session_id)
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)

    # Resolve or create session
    session_id = chat_message.session_id
    if session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if (session.user_id and session.user_id != user_id) or (
            session.anonymous_session_id and session.anonymous_session_id != anon_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session not yours")
    else:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            anonymous_session_id=anon_id,
            title=chat_message.message[:80] + ("..." if len(chat_message.message) > 80 else ""),
        )
        db.add(session)
        await db.flush()

    # Build user message with optional attachment context
    user_content = chat_message.message
    if chat_message.attachment_ids:
        attachment_contexts = []
        for aid in chat_message.attachment_ids[:3]:  # max 3 attachments
            if aid in _attachment_store:
                ctx = _attachment_store[aid]
                attachment_contexts.append(f"\n\n[Contenido del archivo '{ctx.get('filename', 'adjunto')}']:\n{ctx.get('extracted_text', '')[:30000]}")
        if attachment_contexts:
            user_content = user_content + "\n".join(attachment_contexts)
        # Clear from store after use (one-time)
        for aid in chat_message.attachment_ids:
            _attachment_store.pop(aid, None)

    # Persist user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content=chat_message.message,
    )
    db.add(user_msg)
    await db.commit()

    # Build messages for Claude (history + current)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at)
    )
    all_msgs = list(result.scalars().all())
    messages_for_claude = []
    for m in all_msgs:
        content = m.content
        if m.id == user_msg.id and user_content != chat_message.message:
            content = user_content  # Use enriched content for the last user message
        messages_for_claude.append({"role": m.role, "content": content})

    try:
        ai_response_text = await asyncio.to_thread(invoke_claude, messages_for_claude, None, 1024)
    except AIAgentServiceError as e:
        logger.warning("Bedrock AI error: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error invoking AI: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está disponible. Inténtalo de nuevo en unos minutos.",
        ) from e

    credits_remaining = await consume_ai_credit(db, entity, is_anonymous)

    # Persist assistant message
    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="assistant",
        content=ai_response_text,
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        message=ai_response_text,
        credits_remaining=credits_remaining,
        session_id=session.id,
    )


@router.get(
    "/credits",
    summary="Créditos IA restantes",
)
async def get_ai_credits(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    return await get_ai_credits_response(db, current_user, x_anonymous_session_id)


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
    summary="Listar sesiones de chat",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)
    sessions = await _get_sessions_for_entity(db, user_id, anon_id)
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title or "Nuevo chat",
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else "",
        )
        for s in sessions
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=dict,
    summary="Obtener mensajes de una sesión",
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if (session.user_id and session.user_id != user_id) or (
        session.anonymous_session_id and session.anonymous_session_id != anon_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session not yours")

    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    messages = list(result.scalars().all())
    return {
        "id": session.id,
        "title": session.title or "Nuevo chat",
        "messages": [
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m in messages
        ],
    }


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.post(
    "/sessions",
    response_model=CreateSessionResponse,
    summary="Crear nueva sesión (Nuevo Chat)",
)
async def create_session(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        anonymous_session_id=anon_id,
        title="Nuevo chat",
    )
    db.add(session)
    await db.commit()
    return CreateSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
    )


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Renombrar sesión de chat",
)
async def update_session(
    session_id: str,
    payload: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if (session.user_id and session.user_id != user_id) or (
        session.anonymous_session_id and session.anonymous_session_id != anon_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session not yours")
    if payload.title is not None:
        session.title = (payload.title or "Nuevo chat")[:256]
    await db.commit()
    await db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar sesión de chat",
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    user_id, anon_id = await _resolve_entity(db, current_user, x_anonymous_session_id)
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if (session.user_id and session.user_id != user_id) or (
        session.anonymous_session_id and session.anonymous_session_id != anon_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session not yours")
    await db.delete(session)
    await db.commit()


@router.post(
    "/upload",
    summary="Subir archivo para análisis (PDF, Word, TXT)",
)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    if not current_user and not x_anonymous_session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Use: {', '.join(ALLOWED_UPLOAD_EXT)}",
        )
    content = await file.read()
    if len(content) > MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande (máx {MAX_ATTACHMENT_SIZE_MB} MB)",
        )
    attachment_id = str(uuid.uuid4())
    tmp_path = AI_ATTACHMENTS_DIR / f"{attachment_id}{suffix}"
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)
        extracted = extract_text_from_file(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    _attachment_store[attachment_id] = {"extracted_text": extracted or "(No se pudo extraer texto)", "filename": file.filename or "archivo"}
    return {"attachment_id": attachment_id, "filename": file.filename}
