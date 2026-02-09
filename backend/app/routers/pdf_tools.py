"""
Router para Herramientas PDF: unir, dividir, rotar, comprimir, etc.
Mismos límites que conversiones: anónimo 3 usos, registrado 5 (compartidos con conversiones y IA).
Usa patrón Strategy: cada herramienta es una estrategia; el ejecutor común aplica créditos, work dir y respuesta.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Header, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import uuid
import shutil
from datetime import datetime
from typing import List, Optional, Tuple, Union, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.user import User
from app.models.anonymous_session import AnonymousSession
from app.models.pdf_tool_use import PdfToolUse
from app.utils.pdf_tools import PdfToolError
from app.utils.pdf_tool_strategies import REGISTRY
from app.utils.pdf_tool_strategies.base import ToolResult
from app.core.config import settings
from app.services.conversion_service import check_credits_for_operation, consume_credit_for_operation

router = APIRouter()

# Respuestas OpenAPI comunes para herramientas PDF (créditos compartidos con conversiones/IA)
PDF_TOOL_RESPONSES = {
    200: {"description": "Archivo PDF/ZIP o texto devuelto; header X-Credits-Remaining"},
    400: {"description": "Archivo no PDF, parámetros inválidos o error de la herramienta (PdfToolError)"},
    403: {"description": "Límite de créditos alcanzado (auth_limit_reached o anonymous_limit_reached)"},
    413: {"description": f"Archivo mayor a {settings.MAX_FILE_SIZE_MB}MB"},
    500: {"description": "Error interno en la herramienta"},
}

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "pdf_tools"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_upload(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


async def _read_file(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) / (1024 * 1024) > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Tamaño máximo {settings.MAX_FILE_SIZE_MB}MB",
        )
    return content


async def _check_pdf_tool_credits(
    db: AsyncSession,
    current_user: Optional[User],
    x_anonymous_session_id: Optional[str],
) -> Tuple[Union[User, AnonymousSession], bool]:
    return await check_credits_for_operation(db, current_user, x_anonymous_session_id)


async def _consume_pdf_tool_credit(
    db: AsyncSession,
    entity: Union[User, AnonymousSession],
    is_anonymous: bool,
) -> None:
    await consume_credit_for_operation(db, entity, is_anonymous)


async def _record_pdf_tool_use(
    db: AsyncSession,
    entity: Union[User, AnonymousSession],
    is_anonymous: bool,
    tool_name: str,
) -> None:
    use = PdfToolUse(
        anonymous_session_id=entity.id if is_anonymous else None,
        user_id=entity.id if not is_anonymous else None,
        tool_name=tool_name,
    )
    db.add(use)
    await db.commit()


def _credits_remaining_headers(
    entity: Union[User, AnonymousSession],
    is_anonymous: bool,
) -> dict:
    if is_anonymous:
        remaining = settings.ANONYMOUS_CONVERSIONS_LIMIT - entity.conversions_count
    else:
        remaining = (
            999 if getattr(entity, "is_superuser", False) else settings.FREE_TIER_CONVERSIONS_LIMIT - (entity.free_conversion_count or 0)
        )
    return {"X-Credits-Remaining": str(max(0, remaining))}


def _cleanup_work_dir(work: Path) -> None:
    try:
        if work.exists() and work.is_dir():
            shutil.rmtree(work, ignore_errors=True)
    except Exception:
        pass


def _build_response(result: ToolResult, cred_headers: dict) -> Union[FileResponse, Response]:
    if result.path and result.path.exists():
        return FileResponse(
            result.path,
            filename=result.filename,
            media_type=result.media_type,
            headers=cred_headers,
        )
    if result.paths and len(result.paths) == 1 and result.paths[0].exists():
        return FileResponse(
            result.paths[0],
            filename=result.filename,
            media_type=result.media_type,
            headers=cred_headers,
        )
    if result.paths and len(result.paths) > 1:
        import zipfile
        zip_path = result.paths[0].parent / "out.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED, allowZip64=False) as z:
            for p in result.paths:
                z.write(p, p.name)
        zip_bytes = zip_path.read_bytes()
        cred_headers = {**cred_headers, "Content-Disposition": f'attachment; filename="{result.filename}"', "Content-Length": str(len(zip_bytes)), "Content-Encoding": "identity"}
        return Response(content=zip_bytes, media_type=result.media_type, headers=cred_headers)
    if result.text is not None:
        return Response(content=result.text.encode("utf-8"), media_type=result.media_type, headers=cred_headers)
    raise HTTPException(status_code=500, detail="Resultado de herramienta inválido.")


async def _execute_tool(
    tool_name: str,
    files: Dict[str, Any],
    form: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession,
    current_user: Optional[User],
    x_anonymous_session_id: Optional[str],
) -> Union[FileResponse, Response]:
    strategy = REGISTRY.get(tool_name)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Herramienta desconocida: {tool_name}.")
    credit_ctx = await _check_pdf_tool_credits(db, current_user, x_anonymous_session_id)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = STORAGE_DIR / f"{tool_name}_{ts}_{uuid.uuid4().hex[:8]}"
    work.mkdir(parents=True, exist_ok=True)
    try:
        result = strategy.run(work, files, form)
        await _consume_pdf_tool_credit(db, credit_ctx[0], credit_ctx[1])
        await _record_pdf_tool_use(db, credit_ctx[0], credit_ctx[1], tool_name)
        background_tasks.add_task(_cleanup_work_dir, work)
        cred_headers = _credits_remaining_headers(credit_ctx[0], credit_ctx[1])
        return _build_response(result, cred_headers)
    except PdfToolError as e:
        background_tasks.add_task(_cleanup_work_dir, work)
        raise HTTPException(status_code=400, detail=str(e))


# --- Endpoints (cada uno construye files/form y delega en _execute_tool) ---

@router.post(
    "/merge",
    summary="Unir PDF",
    description="Combina varios archivos PDF en uno. Mínimo 2 archivos. Consume un crédito. Usuario opcional; si no hay JWT, enviar X-Anonymous-Session-Id.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_merge(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Unir PDF: varios archivos → un PDF."""
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 PDF para unir.")
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Todos los archivos deben ser PDF.")
    contents = [await _read_file(f) for f in files]
    return await _execute_tool(
        "merge", {"files": contents}, {}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/split",
    summary="Dividir PDF",
    description="Divide un PDF en varios (por páginas). Opcional: pages_per_file. Devuelve ZIP si hay varios archivos. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_split(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pages_per_file: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Dividir PDF: un PDF → varios (o ZIP)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    form = {"pages_per_file": pages_per_file} if pages_per_file is not None else {}
    return await _execute_tool(
        "split", {"file": content}, form, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/rotate",
    summary="Rotar PDF",
    description="Rota todas las páginas del PDF (angle: 90, 180 o 270). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_rotate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    angle: int = Form(90),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Rotar PDF (90, 180 o 270)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "rotate", {"file": content}, {"angle": angle}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/compress",
    summary="Comprimir PDF",
    description="Reduce el tamaño del PDF por reescritura. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Comprimir PDF (reescritura)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool("compress", {"file": content}, {}, background_tasks, db, current_user, x_anonymous_session_id)


@router.post(
    "/protect",
    summary="Proteger PDF",
    description="Añade contraseña al PDF. Form: password. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_protect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Proteger PDF con contraseña."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "protect", {"file": content}, {"password": password}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/unlock",
    summary="Desbloquear PDF",
    description="Quita la contraseña del PDF. Form: password. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_unlock(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Desbloquear PDF con contraseña."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "unlock", {"file": content}, {"password": password}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/order",
    summary="Ordenar páginas",
    description="Reordena páginas del PDF. Form: page_order (ej. 1,3,2,4). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_order(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_order: str = Form(..., description="Ej: 1,3,2,4"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Ordenar páginas del PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "order", {"file": content}, {"page_order": page_order}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/page-numbers",
    summary="Añadir números de página",
    description="Añade numeración a las páginas del PDF. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_page_numbers(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Añadir números de página."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool("page-numbers", {"file": content}, {}, background_tasks, db, current_user, x_anonymous_session_id)


@router.post(
    "/crop",
    summary="Recortar márgenes",
    description="Recorta márgenes del PDF. Form: margin_pt (puntos). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_crop(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    margin_pt: float = Form(0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Recortar márgenes (puntos)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "crop", {"file": content}, {"margin_pt": margin_pt}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/watermark",
    summary="Marca de agua",
    description="Añade texto como marca de agua en cada página. Form: text. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_watermark(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    text: str = Form(..., description="Texto de la marca de agua"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Marca de agua (texto en cada página)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "watermark", {"file": content}, {"text": text}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/repair",
    summary="Reparar PDF",
    description="Intenta reparar un PDF dañado. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_repair(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Intentar reparar PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool("repair", {"file": content}, {}, background_tasks, db, current_user, x_anonymous_session_id)


@router.post(
    "/pdfa",
    summary="Convertir a PDF/A",
    description="Convierte el PDF a formato PDF/A (archivo). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_pdfa(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Convertir a PDF/A (reescritura)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool("pdfa", {"file": content}, {}, background_tasks, db, current_user, x_anonymous_session_id)


@router.post(
    "/compare",
    summary="Comparar PDF",
    description="Compara dos PDF por texto y devuelve un TXT con las diferencias. Form: file_a, file_b. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_compare(
    background_tasks: BackgroundTasks,
    file_a: UploadFile = File(..., alias="file_a"),
    file_b: UploadFile = File(..., alias="file_b"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Comparar dos PDF (texto). Devuelve TXT con diferencias."""
    for f, name in [(file_a, "file_a"), (file_b, "file_b")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Ambos archivos deben ser PDF.")
    c_a, c_b = await _read_file(file_a), await _read_file(file_b)
    return await _execute_tool(
        "compare", {"file_a": c_a, "file_b": c_b}, {}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/edit",
    summary="Añadir texto a PDF",
    description="Añade texto en una página. Form: page_number, text, position (top/center/bottom). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_edit(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_number: int = Form(1),
    text: str = Form(..., description="Texto a añadir"),
    position: str = Form("bottom", description="top, center, bottom"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Editar PDF: añadir texto en una página."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "edit",
        {"file": content},
        {"page_number": page_number, "text": text, "position": position},
        background_tasks, db, current_user, x_anonymous_session_id,
    )


@router.post(
    "/sign",
    summary="Firmar PDF",
    description="Añade firma (texto signer_name y opcionalmente imagen). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_sign(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    signer_name: str = Form(..., description="Nombre del firmante"),
    signature_image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Firmar PDF: añadir texto de firma y opcionalmente imagen de firma."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    files_dict: Dict[str, Any] = {"file": content}
    form_dict: Dict[str, Any] = {"signer_name": signer_name}
    if signature_image and signature_image.filename:
        sig_content = await signature_image.read()
        if len(sig_content) > 0:
            ext = Path(signature_image.filename).suffix.lower() or ".png"
            if ext not in (".png", ".jpg", ".jpeg"):
                ext = ".png"
            files_dict["signature_image"] = sig_content
            form_dict["signature_image_ext"] = ext
    return await _execute_tool("sign", files_dict, form_dict, background_tasks, db, current_user, x_anonymous_session_id)


@router.post(
    "/scan",
    summary="Imágenes a PDF",
    description="Combina una o más imágenes (PNG, JPG, BMP, TIFF) en un PDF. Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_scan(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Imágenes a combinar en un PDF"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Escanear a PDF: una o más imágenes → un PDF."""
    if len(files) < 1:
        raise HTTPException(status_code=400, detail="Se necesita al menos una imagen.")
    allowed = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")
    contents = []
    exts = []
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail="Solo se aceptan imágenes (PNG, JPG, BMP, TIFF).")
        contents.append(await _read_file(f))
        exts.append(ext)
    if not contents:
        raise HTTPException(status_code=400, detail="Se necesita al menos una imagen válida.")
    return await _execute_tool(
        "scan", {"files": contents}, {"file_extensions": exts}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/redact",
    summary="Censurar PDF",
    description="Oculta palabras o frases con rectángulos negros. Form: words (separadas por comas). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_redact(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    words: str = Form(..., description="Palabras o frases a censurar, separadas por comas"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """Censurar PDF: ocultar palabras o frases con rectángulos negros."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool(
        "redact", {"file": content}, {"words": words}, background_tasks, db, current_user, x_anonymous_session_id
    )


@router.post(
    "/ocr",
    summary="OCR PDF",
    description="Añade capa de texto buscable al PDF (requiere tesseract-ocr en el servidor). Consume un crédito.",
    responses=PDF_TOOL_RESPONSES,
)
async def tool_ocr(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    x_anonymous_session_id: Optional[str] = Header(None, alias="X-Anonymous-Session-Id"),
):
    """OCR PDF: añadir capa de texto buscable (requiere tesseract-ocr instalado)."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser PDF.")
    content = await _read_file(file)
    return await _execute_tool("ocr", {"file": content}, {}, background_tasks, db, current_user, x_anonymous_session_id)
