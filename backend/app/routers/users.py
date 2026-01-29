from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.user import User
from backend.app.models.conversion import Conversion

router = APIRouter()

@router.get("/me/stats")
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
    
    # Credits remaining
    credits_used = current_user.free_conversion_count
    free_tier_limit = 10
    credits_remaining = free_tier_limit - credits_used
    
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
            "email": current_user.email
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
            "limit": free_tier_limit
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
