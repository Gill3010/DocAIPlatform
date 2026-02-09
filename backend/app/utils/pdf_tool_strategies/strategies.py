"""
Estrategias concretas para cada herramienta PDF.
Cada una valida inputs, escribe archivos en work_dir, llama a la util y devuelve ToolResult.
"""
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from app.utils.pdf_tools import (
    PdfToolError,
    merge_pdf,
    split_pdf,
    rotate_pdf,
    compress_pdf,
    protect_pdf,
    unlock_pdf,
    order_pdf,
    add_page_numbers_pdf,
    crop_pdf,
    watermark_pdf,
    repair_pdf,
    pdf_to_pdfa,
    compare_pdf_text,
    edit_pdf,
    sign_pdf,
    images_to_pdf,
    redact_pdf,
    ocr_pdf,
)
from app.utils.pdf_tool_strategies.base import PDFToolStrategy, ToolResult


def _require_file(files: Dict[str, Any], key: str) -> bytes:
    data = files.get(key)
    if not data or not isinstance(data, bytes):
        raise PdfToolError("El archivo debe ser PDF.")
    return data


def _require_pdf_list(files: Dict[str, Any], key: str) -> List[bytes]:
    raw = files.get(key)
    if isinstance(raw, bytes):
        return [raw]
    if isinstance(raw, list) and raw:
        return [x for x in raw if isinstance(x, bytes)]
    raise PdfToolError("Se necesita al menos un PDF.")


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


# --- Estrategias ---


class MergeStrategy(PDFToolStrategy):
    tool_name = "merge"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        pdfs = _require_pdf_list(files, "files")
        paths = []
        for i, content in enumerate(pdfs):
            p = work_dir / f"in_{i}.pdf"
            _write(p, content)
            paths.append(str(p))
        out = work_dir / "output.pdf"
        merge_pdf(paths, str(out))
        return ToolResult(path=out, filename="unido.pdf", media_type="application/pdf")


class SplitStrategy(PDFToolStrategy):
    tool_name = "split"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp = work_dir / "input.pdf"
        _write(inp, content)
        pages_per_file = form.get("pages_per_file")
        if pages_per_file is not None:
            try:
                pages_per_file = int(pages_per_file)
            except (TypeError, ValueError):
                pages_per_file = 1
        out_dir = work_dir / "parts"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_paths = split_pdf(str(inp), str(out_dir), pages_per_file=pages_per_file)
        paths = [Path(p) for p in out_paths]
        if len(paths) == 1:
            return ToolResult(path=paths[0], filename="parte_1.pdf", media_type="application/pdf")
        zip_path = work_dir / "partes.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED, allowZip64=False) as z:
            for p in paths:
                z.write(p, p.name)
        return ToolResult(paths=[zip_path], filename="partes.zip", media_type="application/zip")


class RotateStrategy(PDFToolStrategy):
    tool_name = "rotate"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        angle = form.get("angle", 90)
        try:
            angle = int(angle)
        except (TypeError, ValueError):
            angle = 90
        rotate_pdf(str(inp), str(out), angle=angle)
        return ToolResult(path=out, filename="rotado.pdf", media_type="application/pdf")


class CompressStrategy(PDFToolStrategy):
    tool_name = "compress"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        compress_pdf(str(inp), str(out))
        return ToolResult(path=out, filename="comprimido.pdf", media_type="application/pdf")


class ProtectStrategy(PDFToolStrategy):
    tool_name = "protect"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        password = (form.get("password") or "").strip()
        if not password:
            raise PdfToolError("La contraseña no puede estar vacía.")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        protect_pdf(str(inp), str(out), password=password)
        return ToolResult(path=out, filename="protegido.pdf", media_type="application/pdf")


class UnlockStrategy(PDFToolStrategy):
    tool_name = "unlock"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        password = (form.get("password") or "").strip()
        if not password:
            raise PdfToolError("La contraseña no puede estar vacía.")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        unlock_pdf(str(inp), str(out), password=password)
        return ToolResult(path=out, filename="desbloqueado.pdf", media_type="application/pdf")


class OrderStrategy(PDFToolStrategy):
    tool_name = "order"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        page_order = (form.get("page_order") or "").strip()
        if not page_order:
            raise PdfToolError("Indica el orden de páginas (ej: 1,3,2,4).")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        order_pdf(str(inp), str(out), page_order=page_order)
        return ToolResult(path=out, filename="ordenado.pdf", media_type="application/pdf")


class PageNumbersStrategy(PDFToolStrategy):
    tool_name = "page-numbers"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        add_page_numbers_pdf(str(inp), str(out))
        return ToolResult(path=out, filename="con_numeros.pdf", media_type="application/pdf")


class CropStrategy(PDFToolStrategy):
    tool_name = "crop"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        margin_pt = form.get("margin_pt", 0)
        try:
            margin_pt = float(margin_pt)
        except (TypeError, ValueError):
            margin_pt = 0.0
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        crop_pdf(str(inp), str(out), margin_pt=margin_pt)
        return ToolResult(path=out, filename="recortado.pdf", media_type="application/pdf")


class WatermarkStrategy(PDFToolStrategy):
    tool_name = "watermark"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        text = (form.get("text") or "").strip()
        if not text:
            raise PdfToolError("El texto de la marca de agua no puede estar vacío.")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        watermark_pdf(str(inp), str(out), text=text)
        return ToolResult(path=out, filename="con_marca_agua.pdf", media_type="application/pdf")


class RepairStrategy(PDFToolStrategy):
    tool_name = "repair"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        repair_pdf(str(inp), str(out))
        return ToolResult(path=out, filename="reparado.pdf", media_type="application/pdf")


class PdfaStrategy(PDFToolStrategy):
    tool_name = "pdfa"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        pdf_to_pdfa(str(inp), str(out))
        return ToolResult(path=out, filename="pdfa.pdf", media_type="application/pdf")


class CompareStrategy(PDFToolStrategy):
    tool_name = "compare"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        c_a = _require_file(files, "file_a")
        c_b = _require_file(files, "file_b")
        pa, pb = work_dir / "a.pdf", work_dir / "b.pdf"
        _write(pa, c_a)
        _write(pb, c_b)
        result = compare_pdf_text(str(pa), str(pb))
        out_txt = work_dir / "comparacion.txt"
        out_txt.write_text(result, encoding="utf-8")
        return ToolResult(path=out_txt, filename="comparacion.txt", media_type="text/plain")


class EditStrategy(PDFToolStrategy):
    tool_name = "edit"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        page_number = form.get("page_number", 1)
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1
        text = (form.get("text") or "").strip()
        if not text:
            raise PdfToolError("El texto a añadir no puede estar vacío.")
        position = (form.get("position") or "bottom").strip() or "bottom"
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        edit_pdf(str(inp), str(out), page_number=page_number, text=text, position=position)
        return ToolResult(path=out, filename="editado.pdf", media_type="application/pdf")


class SignStrategy(PDFToolStrategy):
    tool_name = "sign"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        signer_name = (form.get("signer_name") or "").strip()
        if not signer_name:
            raise PdfToolError("El nombre del firmante no puede estar vacío.")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        sig_path = None
        sig_content = files.get("signature_image")
        if sig_content and isinstance(sig_content, bytes) and len(sig_content) > 0:
            ext = (form.get("signature_image_ext") or ".png").lower()
            if ext not in (".png", ".jpg", ".jpeg"):
                ext = ".png"
            sig_path = work_dir / f"signature{ext}"
            _write(sig_path, sig_content)
        sign_pdf(
            str(inp), str(out),
            signer_name=signer_name,
            signature_image_path=str(sig_path) if sig_path else None,
        )
        return ToolResult(path=out, filename="firmado.pdf", media_type="application/pdf")


class ScanStrategy(PDFToolStrategy):
    tool_name = "scan"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        raw = files.get("files")
        if not isinstance(raw, list) or not raw:
            raise PdfToolError("Se necesita al menos una imagen.")
        allowed = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif")
        exts = form.get("file_extensions") or []
        if not isinstance(exts, list):
            exts = []
        paths = []
        for i, content in enumerate(raw):
            if not isinstance(content, bytes) or len(content) == 0:
                continue
            ext = (exts[i] if i < len(exts) else ".png").lower() if exts else ".png"
            if ext not in allowed:
                ext = ".png"
            p = work_dir / f"img_{i}{ext}"
            _write(p, content)
            paths.append(str(p))
        if not paths:
            raise PdfToolError("Se necesita al menos una imagen válida.")
        out = work_dir / "escaneado.pdf"
        images_to_pdf(paths, str(out))
        return ToolResult(path=out, filename="escaneado.pdf", media_type="application/pdf")


class RedactStrategy(PDFToolStrategy):
    tool_name = "redact"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        words = (form.get("words") or "").strip()
        if not words:
            raise PdfToolError("Indica al menos una palabra o frase a censurar (separadas por comas).")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        redact_pdf(str(inp), str(out), words_comma_separated=words)
        return ToolResult(path=out, filename="censurado.pdf", media_type="application/pdf")


class OcrStrategy(PDFToolStrategy):
    tool_name = "ocr"

    def run(self, work_dir: Path, files: Dict[str, Any], form: Dict[str, Any]) -> ToolResult:
        content = _require_file(files, "file")
        inp, out = work_dir / "input.pdf", work_dir / "output.pdf"
        _write(inp, content)
        ocr_pdf(str(inp), str(out))
        return ToolResult(path=out, filename="ocr.pdf", media_type="application/pdf")


# Registro por nombre de herramienta (usado por el router)
REGISTRY: Dict[str, PDFToolStrategy] = {
    "merge": MergeStrategy(),
    "split": SplitStrategy(),
    "rotate": RotateStrategy(),
    "compress": CompressStrategy(),
    "protect": ProtectStrategy(),
    "unlock": UnlockStrategy(),
    "order": OrderStrategy(),
    "page-numbers": PageNumbersStrategy(),
    "crop": CropStrategy(),
    "watermark": WatermarkStrategy(),
    "repair": RepairStrategy(),
    "pdfa": PdfaStrategy(),
    "compare": CompareStrategy(),
    "edit": EditStrategy(),
    "sign": SignStrategy(),
    "scan": ScanStrategy(),
    "redact": RedactStrategy(),
    "ocr": OcrStrategy(),
}
