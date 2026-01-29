from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from openai import OpenAI
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.core.config import settings
from backend.app.models.user import User

router = APIRouter()

# Initialize OpenAI client (will use OPENAI_API_KEY from environment)
try:
    client = OpenAI()
except Exception as e:
    print(f"Warning: OpenAI client initialization failed: {e}")
    client = None

# AI Assistant configuration
AI_CREDITS_PER_MESSAGE = 1
FREE_TIER_AI_CREDITS = 10

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    credits_remaining: int

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI Assistant
    
    - Checks user has available AI credits
    - Sends message to OpenAI GPT-4
    - Returns AI response
    - Deducts credit from user
    """
    
    # Check AI credits (using same counter as conversions for now)
    # In production, you'd have a separate ai_credits_count column
    if current_user.free_conversion_count >= FREE_TIER_AI_CREDITS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI credits exhausted. Please upgrade to Premium for unlimited AI assistance."
        )
    
    # Check if OpenAI is configured
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        # Call OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini model for cost efficiency
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
                {
                    "role": "user",
                    "content": chat_message.message
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = completion.choices[0].message.content
        
        # Update user credit counter
        # TODO: Create separate AI credits column in production
        current_user.free_conversion_count += AI_CREDITS_PER_MESSAGE
        await db.commit()
        
        # Calculate remaining credits
        credits_remaining = FREE_TIER_AI_CREDITS - current_user.free_conversion_count
        
        return ChatResponse(
            message=ai_response,
            credits_remaining=max(0, credits_remaining)
        )
        
    except Exception as e:
        # Don't charge credits if API call fails
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )

@router.get("/credits")
async def get_ai_credits(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's remaining AI credits
    """
    credits_used = current_user.free_conversion_count
    credits_remaining = FREE_TIER_AI_CREDITS - credits_used
    
    return {
        "credits_used": credits_used,
        "credits_remaining": max(0, credits_remaining),
        "credits_limit": FREE_TIER_AI_CREDITS
    }
