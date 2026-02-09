from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from openai import OpenAI
from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.core.config import settings
from app.models.user import User
from app.services.ai_service import check_ai_can_send, consume_ai_credit, get_ai_credits_response

router = APIRouter()

# Initialize OpenAI client with API key from settings
try:
    if settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    else:
        print("Warning: OPENAI_API_KEY not configured in settings")
        client = None
except Exception as e:
    print(f"Warning: OpenAI client initialization failed: {e}")
    client = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    credits_remaining: int

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Enviar mensaje al asistente IA",
    description="Envía un mensaje al asistente IA (GPT). Consume un crédito del mismo pool que conversiones y PDF tools. Autenticado: 5 créditos; anónimo: 3 (header X-Anonymous-Session-Id). Devuelve respuesta y credits_remaining.",
    responses={
        200: {"description": "Respuesta del asistente y credits_remaining"},
        403: {"description": "Límite de créditos IA alcanzado (AI credits exhausted)"},
        422: {"description": "Error de validación (message requerido)"},
        503: {"description": "Servicio IA no disponible (OPENAI_API_KEY no configurado)"},
        500: {"description": "Error del servicio OpenAI"},
    },
)
async def chat_with_ai(
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """
    Send a message to the AI Assistant.
    Authenticated: 5 credits (shared with conversions). 6th query → upgrade modal. Anonymous: 3 credits, 4th → register modal.
    """
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please set OPENAI_API_KEY environment variable."
        )

    entity, is_anonymous = await check_ai_can_send(db, current_user, x_anonymous_session_id)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful AI assistant specialized in document processing and file conversion.
                    
You can help users with:
- Document formatting and editing advice
- File conversion recommendations
- Optimization tips for different file formats
- Troubleshooting document issues
- Best practices for document management

Be concise, helpful, and friendly. Focus on practical advice."""
                },
                {"role": "user", "content": chat_message.message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        ai_response = completion.choices[0].message.content
        credits_remaining = await consume_ai_credit(db, entity, is_anonymous)
        return ChatResponse(message=ai_response, credits_remaining=credits_remaining)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )

@router.get(
    "/credits",
    summary="Créditos IA restantes",
    description="Devuelve los créditos IA restantes. Autenticado: mismo pool que conversiones (límite 5). Anónimo: header X-Anonymous-Session-Id, límite 3. No consume crédito.",
    responses={
        200: {"description": "credits_remaining (y opcionalmente límite)"},
    },
)
async def get_ai_credits(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Get remaining AI credits (auth: 5, anonymous: 3, same pool as conversions)."""
    return await get_ai_credits_response(db, current_user, x_anonymous_session_id)
