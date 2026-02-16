"""
Detección y OCR para PDF escaneados.
Permite convertir PDFs que solo tienen imágenes de texto (no texto seleccionable).
"""
import os
import tempfile
from pathlib import Path


def is_pdf_scanned(input_path: str, max_pages_check: int = 3, min_chars_per_page: int = 50) -> bool:
    """
    Detecta si un PDF tiene poco o ningún texto extraíble (probable escaneado).
    Comprueba las primeras páginas; si la mayoría tienen muy poco texto, se considera escaneado.

    Args:
        input_path: Ruta al PDF
        max_pages_check: Máximo de páginas a revisar
        min_chars_per_page: Mínimo de caracteres para considerar que una página tiene texto

    Returns:
        True si parece escaneado (poco texto), False si tiene texto suficiente
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return False

    try:
        with fitz.open(input_path) as doc:
            if len(doc) == 0:
                return True
            pages_to_check = min(max_pages_check, len(doc))
            low_text_count = 0
            for i in range(pages_to_check):
                page = doc[i]
                text = page.get_text()
                if not text or len(text.strip()) < min_chars_per_page:
                    low_text_count += 1
            return low_text_count >= pages_to_check // 2 + 1
    except Exception:
        return False


def add_ocr_to_pdf(input_path: str, output_path: str) -> bool:
    """
    Añade capa OCR a un PDF escaneado usando ocrmypdf.
    Escribe el resultado en output_path.

    Args:
        input_path: PDF de entrada
        output_path: PDF de salida con texto OCR

    Returns:
        True si OK, False si falla
    """
    try:
        import ocrmypdf
    except ImportError:
        return False

    try:
        ocrmypdf.ocr(input_path, output_path, deskew=True, optimize=1)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception:
        return False
