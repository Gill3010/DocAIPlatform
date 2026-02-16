from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import asyncio
import aiofiles
import uuid
import zipfile
import io
from datetime import datetime
from pathlib import Path

from app.core.database import get_db, AsyncSessionLocal
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.conversion import Conversion
from app.models.anonymous_session import AnonymousSession
from app.schemas.conversion import ConversionResponse, ConversionUploadResponse
from app.utils.converter import convert_file, ConversionError, get_supported_conversions
from app.services.ecs_converter_service import convert_via_ecs
from app.core.logging_config import get_logger

_logger = get_logger(__name__)
from app.services.conversion_service import (
    check_user_can_convert,
    increment_user_conversion_count,
    credits_remaining_for_user,
    check_premium_format_access,
)

router = APIRouter()

# Storage configuration
UPLOAD_DIR = Path("backend/storage/uploads")
CONVERTED_DIR = Path("backend/storage/converted")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)


def _should_use_ecs(file_extension: str, target_format: str, use_ecs_setting: bool) -> bool:
    """
    Determina si una conversión debe usar ECS o conversión local.
    
    Reglas:
    - Conversiones rápidas (PDF→DOCX, PDF→Excel, PDF→PPTX, Excel→PDF, PPTX→PDF, imágenes, texto) → SIEMPRE locales
    - DOCX→PDF → ECS solo si use_ecs_setting=True (para mejor calidad de tablas/imágenes)
    - Otras conversiones → ECS solo si use_ecs_setting=True y tienen convertidor local como fallback
    """
    source = file_extension.lower()
    target = target_format.lower()
    
    # Conversiones que SIEMPRE deben ser locales (rápidas, evitan timeout)
    always_local = [
        ('pdf', 'docx'),      # PDF→DOCX: pdf2docx
        ('pdf', 'xlsx'),      # PDF→Excel: pdfplumber
        ('pdf', 'xls'),       # PDF→Excel: pdfplumber
        ('pdf', 'pptx'),      # PDF→PPTX: PyMuPDF + python-pptx
        ('pdf', 'ppt'),       # PDF→PPTX: PyMuPDF + python-pptx
        ('xlsx', 'pdf'),      # Excel→PDF: openpyxl + reportlab
        ('xls', 'pdf'),       # Excel→PDF: openpyxl + reportlab
        ('pptx', 'pdf'),      # PPTX→PDF: LibreOffice local o Docker
        ('ppt', 'pdf'),       # PPTX→PDF: LibreOffice local o Docker
        ('png', 'pdf'),       # Imagen→PDF: PIL
        ('jpg', 'pdf'),       # Imagen→PDF: PIL
        ('jpeg', 'pdf'),      # Imagen→PDF: PIL
        ('pdf', 'png'),       # PDF→Imagen: PyMuPDF
        ('pdf', 'txt'),       # PDF→Texto: pypdf
        ('txt', 'docx'),      # Texto→DOCX: python-docx
        ('docx', 'txt'),      # DOCX→Texto: python-docx
        ('xml', 'html'),      # XML→HTML: lxml
        ('html', 'xml'),      # HTML→XML: lxml
        ('htm', 'xml'),       # HTML→XML: lxml
        ('dxf', 'png'),       # DXF→PNG: ezdxf
        ('png', 'dxf'),       # PNG→DXF: ezdxf
    ]
    
    if (source, target) in always_local:
        return False  # Usar conversión local
    
    # DOCX→PDF: usar ECS solo si está habilitado (mejor calidad)
    if source == 'docx' and target == 'pdf':
        return use_ecs_setting
    
    # Para otras conversiones, usar ECS solo si está habilitado
    # (tendrán fallback a local si falla)
    return use_ecs_setting


async def _run_conversion_background_anon(
    conversion_id: int,
    input_path: str,
    output_path: str,
    file_extension: str,
    target_format: str,
    anonymous_session_id: str,
):
    """Ejecuta la conversión en segundo plano y actualiza la BD. Evita timeout 504 de Cloudflare."""
    from sqlalchemy import select

    _logger.info(f"Background task started for conversion {conversion_id}: {file_extension}->{target_format}")
    try:
        use_ecs_setting = getattr(settings, "USE_ECS_CONVERTER", False)
        should_use_ecs = _should_use_ecs(file_extension, target_format, use_ecs_setting)
        
        if should_use_ecs:
            _logger.info(f"Background: ECS (anon) %s->%s", file_extension, target_format)
            try:
                _logger.info(f"Background: Starting ECS conversion for {conversion_id}")
                await asyncio.to_thread(
                    convert_via_ecs,
                    input_path,
                    output_path,
                    file_extension,
                    target_format,
                )
                _logger.info(f"Background: ECS conversion completed successfully for {conversion_id}")
            except ConversionError as e:
                _logger.warning(f"Background ECS (anon) failed for {conversion_id}, fallback: %s", e)
                convert_file(input_path, output_path, file_extension, target_format)
            except Exception as e:
                _logger.exception(f"Background ECS (anon) exception for {conversion_id}: {e}")
                raise
        else:
            # Conversión local (rápida, evita timeout 504)
            _logger.info(f"Background: local (anon) %s->%s", file_extension, target_format)
            convert_file(input_path, output_path, file_extension, target_format)

        status_update = "completed"
        error_msg = None
        increment_anon = True
    except ConversionError as e:
        status_update = "failed"
        error_msg = str(e)
        increment_anon = False
        _logger.error("Background conversion (anon) failed: %s", e)
    except Exception as e:
        status_update = "failed"
        error_msg = str(e)
        increment_anon = False
        _logger.exception("Background conversion (anon) error")

    # Actualizar en una nueva sesión para no depender del request original
    async with AsyncSessionLocal() as sess:
        from app.models.conversion import Conversion  # import local para evitar ciclos
        from app.models.anonymous_session import AnonymousSession

        conv = await sess.get(Conversion, conversion_id)
        if conv:
            _logger.info(f"Background task updating conversion {conversion_id} to status: {status_update}")
            conv.status = status_update
            conv.error_message = error_msg
            if status_update == "completed":
                conv.completed_at = datetime.now()
                _logger.info(f"Background task: conversion {conversion_id} marked as completed")
        else:
            _logger.error(f"Background task: conversion {conversion_id} not found in DB!")

        if increment_anon:
            result = await sess.execute(
                select(AnonymousSession).where(AnonymousSession.id == anonymous_session_id)
            )
            anon = result.scalar_one_or_none()
            if anon:
                anon.conversions_count += 1
                anon.last_used_at = datetime.now()
                _logger.info(f"Background task: incremented anon session {anonymous_session_id} count")

        try:
            await sess.commit()
            _logger.info(f"Background task: committed status update for conversion {conversion_id}")
        except Exception as commit_error:
            _logger.error(f"Background task: failed to commit status update for conversion {conversion_id}: {commit_error}")
            await sess.rollback()


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
    
    # Check premium format access
    check_premium_format_access(db_user, target_format)

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
        
        # Perform conversion - usa función helper para determinar ECS vs local
        try:
            use_ecs_setting = getattr(settings, "USE_ECS_CONVERTER", False)
            should_use_ecs = _should_use_ecs(file_extension, target_format, use_ecs_setting)
            
            if should_use_ecs:
                _logger.info("Using ECS converter for %s->%s", file_extension, target_format)
                try:
                    await asyncio.to_thread(
                        convert_via_ecs,
                        str(input_file_path),
                        str(output_file_path),
                        file_extension,
                        target_format,
                    )
                    _logger.info("ECS conversion completed successfully")
                except ConversionError as e:
                    _logger.warning("ECS conversion failed, falling back to local: %s", e)
                    convert_file(
                        str(input_file_path),
                        str(output_file_path),
                        file_extension,
                        target_format
                    )
            else:
                # Conversión local (rápida, evita timeout 504)
                _logger.info("Using local converter for %s->%s (faster, avoids timeout)", file_extension, target_format)
                convert_file(
                    str(input_file_path),
                    str(output_file_path),
                    file_extension,
                    target_format
                )
            
            # Update conversion status
            conversion.status = "completed"
            conversion.completed_at = datetime.now()
            
            exempt = getattr(db_user, "is_superuser", False) or getattr(db_user, "can_access_admin_panel", False)
            increment_user_conversion_count(db_user, is_superuser=exempt)
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
    
    # Check premium format access
    check_premium_format_access(anon_session, target_format)

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

        # Conversión síncrona (como antes) - espera a que termine antes de responder
        try:
            use_ecs_setting = getattr(settings, "USE_ECS_CONVERTER", False)
            should_use_ecs = _should_use_ecs(file_extension, target_format, use_ecs_setting)
            
            if should_use_ecs:
                _logger.info("Using ECS converter (anon) for %s->%s", file_extension, target_format)
                try:
                    await asyncio.to_thread(
                        convert_via_ecs,
                        str(input_file_path),
                        str(output_file_path),
                        file_extension,
                        target_format,
                    )
                    _logger.info("ECS conversion (anon) completed successfully")
                except ConversionError as e:
                    _logger.warning("ECS conversion (anon) failed, falling back to local: %s", e)
                    convert_file(
                        str(input_file_path),
                        str(output_file_path),
                        file_extension,
                        target_format
                    )
            else:
                # Conversión local (rápida, evita timeout 504)
                _logger.info("Using local converter (anon) for %s->%s (faster, avoids timeout)", file_extension, target_format)
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
        _logger.warning(f"Download attempt: conversion {conversion_id} not found for session {x_anonymous_session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found")
    _logger.info(f"Download attempt: conversion {conversion_id} status is '{conversion.status}'")
    if conversion.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conversion is not completed. Status: {conversion.status}. Please wait a moment and try again."
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
    from datetime import datetime, timedelta
    
    query = select(Conversion).where(Conversion.user_id == current_user.id)
    
    # Aplicar filtros de fecha según el plan
    if not getattr(current_user, "is_superuser", False):
        # Por defecto 30 días para Gratuito y Básico
        days = 30
        if getattr(current_user, "can_access_admin_panel", False):
            days = 365
        elif current_user.is_premium and current_user.premium_plan_id in ['Pro', 'Empresa']:
            days = 365
            
        since_date = datetime.now() - timedelta(days=days)
        query = query.where(Conversion.created_at >= since_date)

    result = await db.execute(
        query
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
    "/engine-status",
    summary="Estado del motor de conversión",
    description="Indica qué motor se usa. PDF->DOCX usa pdf2docx (tablas e imágenes).",
)
async def get_engine_status():
    """Devuelve qué motor de conversión se usa."""
    use_ecs = getattr(settings, "USE_ECS_CONVERTER", False)
    try:
        from pdf2docx import Converter
        pdf2docx_available = True
    except ImportError:
        pdf2docx_available = False
    return {
        "use_ecs": use_ecs,
        "pdf_to_docx": "pdf2docx" if pdf2docx_available else "fallback",
    }


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


@router.get(
    "/status-anonymous/{conversion_id}",
    response_model=ConversionResponse,
    summary="Estado de una conversión (anónimo)",
    description="Devuelve los datos de una conversión anónima (requiere X-Anonymous-Session-Id).",
    responses={
        200: {"description": "Datos de la conversión"},
        400: {"description": "Sesión inválida"},
        404: {"description": "Conversión no encontrada"},
    },
)
async def get_conversion_status_anonymous(
    conversion_id: int,
    x_anonymous_session_id: str = Header(..., alias="X-Anonymous-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    """Get status for an anonymous conversion (polling friendly)."""
    try:
        uuid.UUID(x_anonymous_session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Anonymous-Session-Id format"
        )

    result = await db.execute(
        select(Conversion).where(
            Conversion.id == conversion_id,
            Conversion.user_id.is_(None),
            Conversion.anonymous_session_id == x_anonymous_session_id,
        )
    )
    conversion = result.scalar_one_or_none()
    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion not found"
        )
    return conversion
