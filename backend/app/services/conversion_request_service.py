"""
Servicio de solicitud de conversión: orquesta upload, conversión y actualización de BD.

Extrae la lógica de negocio del router para mantener convert.py delgado.
Conversiones en segundo plano para evitar timeout 504 (Cloudflare ~100s).
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
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


async def _run_conversion_background(
    conversion_id: int,
    input_path: str,
    output_path: str,
    file_extension: str,
    target_format: str,
    user_id: Optional[int],
    anonymous_session_id: Optional[str],
    is_superuser_exempt: bool,
):
    """Ejecuta la conversión en segundo plano y actualiza la BD. Evita timeout 504 de Cloudflare."""
    _logger.info(f"Background conversion started: {conversion_id} ({file_extension}->{target_format})")
    try:
        await asyncio.to_thread(
            execute_conversion,
            input_path,
            output_path,
            file_extension,
            target_format,
        )
        status_update = "completed"
        error_msg = None
        increment = True
    except ConversionError as e:
        status_update = "failed"
        error_msg = str(e)
        increment = False
        _logger.error("Background conversion failed: %s", e)
    except Exception as e:
        status_update = "failed"
        error_msg = str(e)
        increment = False
        _logger.exception("Background conversion error")

    async with AsyncSessionLocal() as sess:
        conv = await sess.get(Conversion, conversion_id)
        if conv:
            conv.status = status_update
            conv.error_message = error_msg
            if status_update == "completed":
                conv.completed_at = datetime.now()
                if increment:
                    if user_id:
                        from app.models.user import User
                        u = await sess.get(User, user_id)
                        if u:
                            increment_user_conversion_count(u, is_superuser=is_superuser_exempt)
                            _logger.info(f"Background: incremented user {user_id} conversion count")
                    elif anonymous_session_id:
                        r = await sess.execute(
                            select(AnonymousSession).where(AnonymousSession.id == anonymous_session_id)
                        )
                        anon = r.scalar_one_or_none()
                        if anon:
                            anon.conversions_count += 1
                            anon.last_used_at = datetime.now()
                            _logger.info(f"Background: incremented anon session {anonymous_session_id}")
            await sess.commit()


async def process_upload_and_convert_authenticated(
    content: bytes,
    original_filename: str,
    target_format: str,
    user_id: int,
    db_user: object,
    upload_dir: Path,
    converted_dir: Path,
    db: AsyncSession,
    background_tasks,
) -> ConversionUploadResponse:
    """
    Procesa upload y lanza conversión en segundo plano. Retorna inmediatamente con status=processing
    para evitar timeout 504 (Cloudflare ~100s). El frontend debe hacer polling a /convert/status/{id}.
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

    exempt = getattr(db_user, "is_superuser", False) or getattr(
        db_user, "can_access_admin_panel", False
    )

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

    background_tasks.add_task(
        _run_conversion_background,
        int(conversion.id),
        str(input_path),
        str(output_path),
        file_extension,
        target_format,
        user_id=user_id,
        anonymous_session_id=None,
        is_superuser_exempt=exempt,
    )

    credits = credits_remaining_for_user(db_user)
    return ConversionUploadResponse(
        message="Conversion started",
        conversion_id=int(conversion.id),
        status="processing",
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
    background_tasks,
) -> ConversionUploadResponse:
    """
    Procesa upload y lanza conversión en segundo plano. Retorna inmediatamente con status=processing.
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

    background_tasks.add_task(
        _run_conversion_background,
        int(conversion.id),
        str(input_path),
        str(output_path),
        file_extension,
        target_format,
        user_id=None,
        anonymous_session_id=anonymous_session_id,
        is_superuser_exempt=False,
    )

    credits = settings.ANONYMOUS_CONVERSIONS_LIMIT - anon_session.conversions_count
    return ConversionUploadResponse(
        message="Conversion started",
        conversion_id=conversion.id,
        status="processing",
        credits_remaining=credits,
    )
