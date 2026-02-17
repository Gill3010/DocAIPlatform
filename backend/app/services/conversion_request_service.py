"""
Servicio de solicitud de conversión: orquesta upload, conversión y actualización de BD.

Extrae la lógica de negocio del router para mantener convert.py delgado.
"""
import asyncio
from datetime import datetime
from pathlib import Path
import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging_config import get_logger
from app.models.conversion import Conversion
from app.models.anonymous_session import AnonymousSession
from app.schemas.conversion import ConversionUploadResponse
from app.services.conversion_orchestrator import execute_conversion
from app.services.conversion_service import (
    check_premium_format_access,
    credits_remaining_for_user,
    increment_user_conversion_count,
)
from app.utils.converter import ConversionError, get_supported_conversions

_logger = get_logger(__name__)


async def process_upload_and_convert_authenticated(
    content: bytes,
    original_filename: str,
    target_format: str,
    user_id: int,
    db_user: object,
    upload_dir: Path,
    converted_dir: Path,
    db: AsyncSession,
) -> ConversionUploadResponse:
    """
    Procesa upload y conversión para usuario autenticado.
    Guarda archivo, crea registro, convierte, actualiza créditos.
    """
    file_extension = Path(original_filename).suffix.lower().replace(".", "")

    supported = get_supported_conversions()
    if file_extension not in supported:
        raise ValueError(f"Source format '{file_extension}' is not supported")
    if target_format not in supported.get(file_extension, []):
        raise ValueError(f"Cannot convert from '{file_extension}' to '{target_format}'")

    check_premium_format_access(db_user, target_format)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"user_{user_id}_{timestamp}_{original_filename}"
    input_path = upload_dir / safe_filename
    output_filename = f"{Path(safe_filename).stem}_converted.{target_format}"
    output_path = converted_dir / output_filename

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)

    conversion = Conversion(
        user_id=user_id,
        original_filename=original_filename,
        original_format=file_extension,
        target_format=target_format,
        file_size=len(content) / (1024 * 1024),
        input_file_path=str(input_path),
        output_file_path=str(output_path),
        status="processing",
    )
    db.add(conversion)
    await db.commit()
    await db.refresh(conversion)

    try:
        await asyncio.to_thread(
            execute_conversion,
            str(input_path),
            str(output_path),
            file_extension,
            target_format,
        )
        conversion.status = "completed"
        conversion.completed_at = datetime.now()
        exempt = getattr(db_user, "is_superuser", False) or getattr(
            db_user, "can_access_admin_panel", False
        )
        increment_user_conversion_count(db_user, is_superuser=exempt)
        await db.commit()
    except ConversionError as e:
        conversion.status = "failed"
        conversion.error_message = str(e)
        await db.commit()
        raise

    credits = credits_remaining_for_user(db_user)
    return ConversionUploadResponse(
        message="File converted successfully",
        conversion_id=int(conversion.id),
        status="completed",
        credits_remaining=int(credits),
    )


async def process_upload_and_convert_anonymous(
    content: bytes,
    original_filename: str,
    target_format: str,
    anonymous_session_id: str,
    anon_session: AnonymousSession,
    upload_dir: Path,
    converted_dir: Path,
    db: AsyncSession,
) -> ConversionUploadResponse:
    """
    Procesa upload y conversión para usuario anónimo.
    """
    file_extension = Path(original_filename).suffix.lower().replace(".", "")

    supported = get_supported_conversions()
    if file_extension not in supported:
        raise ValueError(f"Source format '{file_extension}' is not supported")
    if target_format not in supported.get(file_extension, []):
        raise ValueError(f"Cannot convert from '{file_extension}' to '{target_format}'")

    check_premium_format_access(anon_session, target_format)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"anon_{anonymous_session_id[:8]}_{timestamp}_{original_filename}"
    input_path = upload_dir / safe_filename
    output_filename = f"{Path(safe_filename).stem}_converted.{target_format}"
    output_path = converted_dir / output_filename

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)

    conversion = Conversion(
        user_id=None,
        anonymous_session_id=anonymous_session_id,
        original_filename=original_filename,
        original_format=file_extension,
        target_format=target_format,
        file_size=len(content) / (1024 * 1024),
        input_file_path=str(input_path),
        output_file_path=str(output_path),
        status="processing",
    )
    db.add(conversion)
    await db.commit()
    await db.refresh(conversion)

    try:
        await asyncio.to_thread(
            execute_conversion,
            str(input_path),
            str(output_path),
            file_extension,
            target_format,
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
        raise

    credits = settings.ANONYMOUS_CONVERSIONS_LIMIT - anon_session.conversions_count
    return ConversionUploadResponse(
        message="File converted successfully",
        conversion_id=conversion.id,
        status="completed",
        credits_remaining=credits,
    )
