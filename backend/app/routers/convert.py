from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
import aiofiles
import os
from datetime import datetime
from pathlib import Path

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.user import User
from backend.app.models.conversion import Conversion
from backend.app.schemas.conversion import ConversionResponse, ConversionUploadResponse
from backend.app.utils.converter import convert_file, ConversionError, get_supported_conversions

router = APIRouter()

# Storage configuration
UPLOAD_DIR = Path("backend/storage/uploads")
CONVERTED_DIR = Path("backend/storage/converted")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

# Free tier limits
MAX_FILE_SIZE_MB = 10
FREE_TIER_CONVERSIONS = 10

@router.post("/upload", response_model=ConversionUploadResponse)
async def upload_and_convert(
    file: UploadFile = File(...),
    target_format: str = "pdf",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and convert a document
    
    - Checks user credits (free tier: 10 conversions)
    - Saves file to storage
    - Performs conversion
    - Updates user credit counter
    """
    
    # Validate file size
    file_size_mb = 0
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
        )
    
    # Reset file position
    await file.seek(0)
    
    # Check user credits
    if current_user.free_conversion_count >= FREE_TIER_CONVERSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free conversion limit reached. Please upgrade to Premium."
        )
    
    # Extract file format
    original_filename = file.filename or "unnamed"
    file_extension = Path(original_filename).suffix.lower().replace('.', '')
    
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid extension"
        )
    
    # Validate conversion is supported
    supported = get_supported_conversions()
    if file_extension not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source format '{file_extension}' is not supported. Supported: {list(supported.keys())}"
        )
    
    if target_format not in supported.get(file_extension, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert from '{file_extension}' to '{target_format}'. "
                   f"Available targets: {supported.get(file_extension, [])}"
        )
    
    # Generate unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"user_{current_user.id}_{timestamp}_{original_filename}"
    input_file_path = UPLOAD_DIR / safe_filename
    
    output_filename = f"{Path(safe_filename).stem}_converted.{target_format}"
    output_file_path = CONVERTED_DIR / output_filename
    
    try:
        # Save uploaded file
        async with aiofiles.open(input_file_path, 'wb') as f:
            await f.write(content)
        
        # Create conversion record
        conversion = Conversion(
            user_id=current_user.id,
            original_filename=original_filename,
            original_format=file_extension,
            target_format=target_format,
            file_size=file_size_mb,
            input_file_path=str(input_file_path),
            output_file_path=str(output_file_path),
            status="processing"
        )
        
        db.add(conversion)
        await db.commit()
        await db.refresh(conversion)
        
        # Perform conversion (synchronous - runs in thread pool)
        try:
            convert_file(
                str(input_file_path),
                str(output_file_path),
                file_extension,
                target_format
            )
            
            # Update conversion status
            conversion.status = "completed"
            conversion.completed_at = datetime.now()
            
            # Update user credit counter
            current_user.free_conversion_count += 1
            
            await db.commit()
            
        except ConversionError as e:
            # Mark conversion as failed
            conversion.status = "failed"
            conversion.error_message = str(e)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {str(e)}"
            )
        
        # Calculate remaining credits
        credits_remaining = FREE_TIER_CONVERSIONS - current_user.free_conversion_count
        
        return ConversionUploadResponse(
            message="File converted successfully",
            conversion_id=conversion.id,
            status="completed",
            credits_remaining=credits_remaining
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/history", response_model=List[ConversionResponse])
async def get_conversion_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """
    Get user's conversion history
    """
    result = await db.execute(
        select(Conversion)
        .where(Conversion.user_id == current_user.id)
        .order_by(Conversion.created_at.desc())
        .limit(limit)
    )
    
    conversions = result.scalars().all()
    return conversions

@router.get("/download/{conversion_id}")
async def download_converted_file(
    conversion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a converted file
    """
    result = await db.execute(
        select(Conversion).where(
            Conversion.id == conversion_id,
            Conversion.user_id == current_user.id
        )
    )
    
    conversion = result.scalar_one_or_none()
    
    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion not found"
        )
    
    if conversion.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversion is not completed. Status: {conversion.status}"
        )
    
    output_path = Path(conversion.output_file_path)
    
    if not output_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converted file not found on server"
        )
    
    # Generate download filename
    download_name = f"{Path(conversion.original_filename).stem}_converted.{conversion.target_format}"
    
    return FileResponse(
        path=str(output_path),
        filename=download_name,
        media_type='application/octet-stream'
    )

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported conversion formats
    """
    return {
        "formats": get_supported_conversions(),
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "free_tier_limit": FREE_TIER_CONVERSIONS
    }

@router.get("/status/{conversion_id}", response_model=ConversionResponse)
async def get_conversion_status(
    conversion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a specific conversion
    """
    result = await db.execute(
        select(Conversion).where(
            Conversion.id == conversion_id,
            Conversion.user_id == current_user.id
        )
    )
    
    conversion = result.scalar_one_or_none()
    
    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion not found"
        )
    
    return conversion
