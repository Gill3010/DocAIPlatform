from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import aiofiles
import uuid
import zipfile
import io
from datetime import datetime
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.conversion import Conversion
from app.models.anonymous_session import AnonymousSession
from app.schemas.conversion import ConversionResponse, ConversionUploadResponse
from app.utils.converter import convert_file, ConversionError, get_supported_conversions
from app.services.conversion_service import (
    check_user_can_convert,
    increment_user_conversion_count,
    credits_remaining_for_user,
)

router = APIRouter()

# Storage configuration
UPLOAD_DIR = Path("backend/storage/uploads")
CONVERTED_DIR = Path("backend/storage/converted")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)


def _zip_xml_and_images(output_path: Path) -> Optional[bytes]:
    """If output is XML and there are sidecar images (base_image_*), return ZIP bytes; else None."""
    if output_path.suffix.lower() != '.xml' or not output_path.exists():
        return None
    stem = output_path.stem
    parent = output_path.parent
    image_files = sorted(parent.glob(f"{stem}_image_*"))
    if not image_files:
        return None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(output_path, output_path.name)
        for f in image_files:
            z.write(f, f.name)
    buf.seek(0)
    return buf.read()

@router.post(
    "/upload",
    response_model=ConversionUploadResponse,
    summary="Subir y convertir (usuario autenticado)",
    description=(
        "Sube un archivo y lo convierte al formato indicado. Requiere JWT. "
        "Comprueba créditos del usuario (límite freemium: 5 conversiones). "
        "Devuelve `credits_remaining`. Para descargar el resultado usar GET /convert/download/{conversion_id}."
    ),
    responses={
        200: {"description": "Conversión completada; incluye conversion_id y credits_remaining"},
        400: {"description": "Extensión no soportada, combinación from/to no permitida o archivo sin extensión"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Límite de créditos alcanzado (auth_limit_reached)"},
        413: {"description": f"Archivo mayor a {settings.MAX_FILE_SIZE_MB}MB"},
        422: {"description": "Error de validación (file requerido)"},
        500: {"description": "Error en la conversión o en el servidor"},
    },
)
async def upload_and_convert(
    file: UploadFile = File(...),
    target_format: str = "pdf",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and convert a document

    - Checks user credits (free tier: 5 conversions total)
    - Saves file to storage
    - Performs conversion
    - Updates user credit counter
    """
    
    # Validate file size
    file_size_mb = 0
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
        )
    
    # Reset file position
    await file.seek(0)

    db_user = await check_user_can_convert(db, current_user.id)

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
    safe_filename = f"user_{db_user.id}_{timestamp}_{original_filename}"
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
            
            increment_user_conversion_count(db_user, is_superuser=getattr(db_user, "is_superuser", False))
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
        
        credits_remaining = credits_remaining_for_user(db_user)
        return ConversionUploadResponse(
            message="File converted successfully",
            conversion_id=int(conversion.id),
            status="completed",
            credits_remaining=int(credits_remaining),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {str(e)}"
        )


@router.post(
    "/upload-anonymous",
    response_model=ConversionUploadResponse,
    summary="Subir y convertir (anónimo)",
    description=(
        "Sube y convierte sin login. Requiere header `X-Anonymous-Session-Id` (UUID). "
        "Límite: 3 conversiones por sesión anónima. Devuelve credits_remaining. "
        "Descarga con GET /convert/download-anonymous/{conversion_id} y el mismo header."
    ),
    responses={
        200: {"description": "Conversión completada; incluye conversion_id y credits_remaining"},
        400: {"description": "X-Anonymous-Session-Id inválido (no UUID), extensión no soportada o combinación from/to no permitida"},
        403: {"description": "Límite anónimo alcanzado (anonymous_limit_reached)"},
        413: {"description": f"Archivo mayor a {settings.MAX_FILE_SIZE_MB}MB"},
        422: {"description": "Error de validación (file requerido)"},
        500: {"description": "Error en la conversión o en el servidor"},
    },
)
async def upload_and_convert_anonymous(
    file: UploadFile = File(...),
    target_format: str = "pdf",
    x_anonymous_session_id: str = Header(..., alias="X-Anonymous-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and convert for anonymous users (max 3 conversions per session)
    """
    # Validate session_id format (UUID)
    try:
        uuid.UUID(x_anonymous_session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Anonymous-Session-Id format"
        )

    # Get or create anonymous session
    result = await db.execute(
        select(AnonymousSession).where(AnonymousSession.id == x_anonymous_session_id)
    )
    anon_session = result.scalar_one_or_none()
    if not anon_session:
        anon_session = AnonymousSession(id=x_anonymous_session_id, conversions_count=0)
        db.add(anon_session)
        await db.commit()
        await db.refresh(anon_session)

    if anon_session.conversions_count >= settings.ANONYMOUS_CONVERSIONS_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="anonymous_limit_reached"
        )

    # Validate file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
        )
    await file.seek(0)

    # Extract file format
    original_filename = file.filename or "unnamed"
    file_extension = Path(original_filename).suffix.lower().replace('.', '')
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid extension"
        )

    supported = get_supported_conversions()
    if file_extension not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source format '{file_extension}' is not supported."
        )
    if target_format not in supported.get(file_extension, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert from '{file_extension}' to '{target_format}'."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"anon_{x_anonymous_session_id[:8]}_{timestamp}_{original_filename}"
    input_file_path = UPLOAD_DIR / safe_filename
    output_filename = f"{Path(safe_filename).stem}_converted.{target_format}"
    output_file_path = CONVERTED_DIR / output_filename

    try:
        async with aiofiles.open(input_file_path, 'wb') as f:
            await f.write(content)

        conversion = Conversion(
            user_id=None,
            anonymous_session_id=x_anonymous_session_id,
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

        try:
            convert_file(
                str(input_file_path),
                str(output_file_path),
                file_extension,
                target_format
            )
            conversion.status = "completed"
            conversion.completed_at = datetime.now()
            anon_session.conversions_count += 1
            anon_session.last_used_at = datetime.now()
            await db.commit()

        except ConversionError as e:
            conversion.status = "failed"
            conversion.error_message = str(e)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {str(e)}"
            )

        credits_remaining = settings.ANONYMOUS_CONVERSIONS_LIMIT - anon_session.conversions_count
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


@router.get(
    "/download-anonymous/{conversion_id}",
    summary="Descargar conversión (anónimo)",
    description="Descarga el archivo convertido. Solo si la conversión pertenece a la sesión indicada en `X-Anonymous-Session-Id`. Si el resultado es XML con imágenes, se devuelve un ZIP.",
    responses={
        200: {"description": "Archivo (o ZIP) listo para descarga"},
        400: {"description": "La conversión no está en estado completed"},
        404: {"description": "Conversión no encontrada o archivo no existe en el servidor"},
    },
)
async def download_converted_file_anonymous(
    conversion_id: int,
    x_anonymous_session_id: str = Header(..., alias="X-Anonymous-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    """Download converted file for anonymous users (must match session)"""
    result = await db.execute(
        select(Conversion).where(
            Conversion.id == conversion_id,
            Conversion.user_id.is_(None),
            Conversion.anonymous_session_id == x_anonymous_session_id
        )
    )
    conversion = result.scalar_one_or_none()
    if not conversion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found")
    if conversion.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversion is not completed. Status: {conversion.status}"
        )
    output_path = Path(conversion.output_file_path)
    if not output_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Converted file not found")
    zip_bytes = _zip_xml_and_images(output_path)
    if zip_bytes is not None:
        download_name = f"{Path(conversion.original_filename).stem}_converted.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )
    download_name = f"{Path(conversion.original_filename).stem}_converted.{conversion.target_format}"
    return FileResponse(path=str(output_path), filename=download_name, media_type='application/octet-stream')


@router.get(
    "/history",
    response_model=List[ConversionResponse],
    summary="Historial de conversiones",
    description="Lista las conversiones del usuario autenticado, ordenadas por fecha descendente. Parámetro opcional: limit (por defecto 20).",
    responses={
        200: {"description": "Lista de conversiones del usuario"},
        401: {"description": "Token ausente o inválido"},
    },
)
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

@router.get(
    "/download/{conversion_id}",
    summary="Descargar conversión (autenticado)",
    description="Descarga el archivo convertido. Solo conversiones del usuario actual. Si el resultado es XML con imágenes, se devuelve un ZIP.",
    responses={
        200: {"description": "Archivo (o ZIP) listo para descarga"},
        400: {"description": "La conversión no está en estado completed"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Conversión no encontrada o archivo no existe en el servidor"},
    },
)
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

    # XML + images: return ZIP for OJS (upload XML + dependent image files)
    zip_bytes = _zip_xml_and_images(output_path)
    if zip_bytes is not None:
        download_name = f"{Path(conversion.original_filename).stem}_converted.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )

    download_name = f"{Path(conversion.original_filename).stem}_converted.{conversion.target_format}"
    return FileResponse(
        path=str(output_path),
        filename=download_name,
        media_type='application/octet-stream'
    )

@router.get(
    "/supported-formats",
    summary="Formatos soportados",
    description="Devuelve el mapa de formatos origen → destinos permitidos, límite de tamaño (MB) y límite del tier gratuito. No requiere autenticación.",
    responses={200: {"description": "formats, max_file_size_mb, free_tier_limit"}},
)
async def get_supported_formats():
    """
    Get list of supported conversion formats
    """
    return {
        "formats": get_supported_conversions(),
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "free_tier_limit": settings.FREE_TIER_CONVERSIONS_LIMIT
    }

@router.get(
    "/status/{conversion_id}",
    response_model=ConversionResponse,
    summary="Estado de una conversión",
    description="Devuelve los datos de una conversión del usuario (estado, formatos, tamaño, etc.). Solo conversiones propias.",
    responses={
        200: {"description": "Datos de la conversión"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Conversión no encontrada"},
    },
)
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
