"""
Operaciones sobre PDF (herramientas): unir, dividir, rotar, comprimir, etc.
Usa pypdf y PyMuPDF. Una sola implementación por operación.
"""
from pathlib import Path
from typing import List, Optional
import io
import zipfile
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class PdfToolError(Exception):
    """Error en una operación de herramienta PDF."""
    pass


def _ensure_pdf(path: str) -> PdfReader:
    try:
        return PdfReader(path)
    except Exception as e:
        raise PdfToolError(f"PDF inválido o corrupto: {e}") from e


def merge_pdf(input_paths: List[str], output_path: str) -> None:
    """Unir varios PDF en uno. output_path debe ser ruta de archivo."""
    if not input_paths:
        raise PdfToolError("Se necesita al menos un PDF para unir.")
    writer = PdfWriter()
    for p in input_paths:
        reader = _ensure_pdf(p)
        for page in reader.pages:
            writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def split_pdf(input_path: str, output_dir: str, pages_per_file: Optional[int] = None) -> List[str]:
    """
    Dividir PDF. Si pages_per_file es None, un archivo por página.
    Devuelve lista de rutas de PDF generados.
    """
    reader = _ensure_pdf(input_path)
    n = len(reader.pages)
    if n == 0:
        raise PdfToolError("El PDF no tiene páginas.")
    step = pages_per_file or 1
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_paths = []
    for i in range(0, n, step):
        writer = PdfWriter()
        for j in range(i, min(i + step, n)):
            writer.add_page(reader.pages[j])
        out = Path(output_dir) / f"parte_{len(out_paths) + 1}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        out_paths.append(str(out))
    return out_paths


def rotate_pdf(input_path: str, output_path: str, angle: int = 90) -> None:
    """Rotar todas las páginas (angle: 90, 180 o 270)."""
    if angle not in (90, 180, 270):
        raise PdfToolError("Ángulo debe ser 90, 180 o 270.")
    reader = _ensure_pdf(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def compress_pdf(input_path: str, output_path: str) -> None:
    """Reescribir PDF (pypdf no comprime mucho; reduce objetos redundantes)."""
    reader = _ensure_pdf(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def protect_pdf(input_path: str, output_path: str, password: str) -> None:
    """Proteger PDF con contraseña."""
    if not password or not password.strip():
        raise PdfToolError("La contraseña no puede estar vacía.")
    reader = _ensure_pdf(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def unlock_pdf(input_path: str, output_path: str, password: str) -> None:
    """Desbloquear PDF con contraseña."""
    if not password or not password.strip():
        raise PdfToolError("La contraseña no puede estar vacía.")
    reader = _ensure_pdf(input_path)
    if not reader.is_encrypted:
        raise PdfToolError(
            "El PDF no está protegido con contraseña. Selecciona el archivo que descargaste al usar "
            "'Proteger PDF' (no el archivo original sin proteger)."
        )
    try:
        reader.decrypt(password)
    except Exception as e:
        raise PdfToolError("Contraseña incorrecta o PDF no se pudo desbloquear.") from e
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def order_pdf(input_path: str, output_path: str, page_order: str) -> None:
    """Reordenar páginas. page_order ej: '1,3,2,4' (índices 1-based)."""
    reader = _ensure_pdf(input_path)
    n = len(reader.pages)
    try:
        indices = [int(x.strip()) - 1 for x in page_order.split(",") if x.strip()]
    except ValueError:
        raise PdfToolError("Orden de páginas inválido. Use números separados por coma, ej: 1,3,2,4")
    for i in indices:
        if i < 0 or i >= n:
            raise PdfToolError(f"Número de página fuera de rango (1-{n}).")
    writer = PdfWriter()
    for i in indices:
        writer.add_page(reader.pages[i])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def add_page_numbers_pdf(input_path: str, output_path: str) -> None:
    """Añadir números de página usando PyMuPDF (overlay de texto)."""
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF. pip install PyMuPDF")
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    for i in range(len(doc)):
        page = doc[i]
        rect = page.rect
        text = f"{i + 1} / {len(doc)}"
        r = fitz.Rect(rect.width - 70, rect.height - 25, rect.width - 5, rect.height - 5)
        page.insert_textbox(r, text, fontsize=10, fontname="helv", align=2)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


def crop_pdf(input_path: str, output_path: str, margin_pt: float = 0) -> None:
    """Recortar márgenes (margin_pt: puntos a recortar por lado)."""
    if margin_pt < 0:
        raise PdfToolError("El margen no puede ser negativo.")
    reader = _ensure_pdf(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        if margin_pt > 0:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            page.cropbox.lower_left = (margin_pt, margin_pt)
            page.cropbox.upper_right = (w - margin_pt, h - margin_pt)
        writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def watermark_pdf(input_path: str, output_path: str, text: str) -> None:
    """Añadir marca de agua de texto en cada página (PyMuPDF). Texto gris centrado con insert_text."""
    if not text or not text.strip():
        raise PdfToolError("El texto de la marca de agua no puede estar vacío.")
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF.")
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    color_gris = (0.4, 0.4, 0.4)
    txt = text.strip()
    fontsize = 48
    for i in range(len(doc)):
        page = doc[i]
        rect = page.rect
        cx, cy = rect.width / 2, rect.height / 2
        # insert_text usa (x, y) como esquina inferior izquierda; aproximar centro
        # Ancho aproximado ~0.6 * fontsize * len(txt) en helv
        ancho_aprox = 0.6 * fontsize * len(txt)
        x = cx - ancho_aprox / 2
        y = cy + fontsize * 0.35
        page.insert_text(
            (x, y), txt, fontsize=fontsize, fontname="helv", color=color_gris
        )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path, garbage=4, deflate=True, clean=True, incremental=False)
    doc.close()


def repair_pdf(input_path: str, output_path: str) -> None:
    """Intentar reparar PDF leyendo y reescribiendo (puede corregir algunos daños)."""
    reader = _ensure_pdf(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def pdf_to_pdfa(input_path: str, output_path: str) -> None:
    """Convertir a PDF/A. Sin librería específica se reescribe; PDF/A estricto requiere pikepdf."""
    # Reescribir como aproximación; PDF/A-1b estricto requiere validación de fuentes/colores
    repair_pdf(input_path, output_path)


def compare_pdf_text(path_a: str, path_b: str) -> str:
    """Comparar dos PDFs extrayendo texto; devuelve resumen de diferencias (texto)."""
    ra = _ensure_pdf(path_a)
    rb = _ensure_pdf(path_b)
    lines_a = []
    lines_b = []
    for page in ra.pages:
        t = page.extract_text()
        if t:
            lines_a.extend(t.splitlines())
    for page in rb.pages:
        t = page.extract_text()
        if t:
            lines_b.extend(t.splitlines())
    na, nb = len(lines_a), len(lines_b)
    diff = []
    if na != nb:
        diff.append(f"Páginas/líneas: A={na} líneas, B={nb} líneas.")
    for i, (la, lb) in enumerate(zip(lines_a, lines_b)):
        if la != lb:
            diff.append(f"Línea {i + 1}: A={la!r} | B={lb!r}")
    if len(lines_a) != len(lines_b):
        for i in range(min(len(lines_a), len(lines_b)), max(len(lines_a), len(lines_b))):
            if i < len(lines_a):
                diff.append(f"Solo en A línea {i + 1}: {lines_a[i]!r}")
            else:
                diff.append(f"Solo en B línea {i + 1}: {lines_b[i]!r}")
    return "\n".join(diff) if diff else "Los textos extraídos son idénticos."


# --- Herramientas adicionales: editar, firmar, OCR, escanear a PDF, censurar ---

def edit_pdf(input_path: str, output_path: str, page_number: int = 1, text: str = "", position: str = "bottom") -> None:
    """Añadir texto a una página del PDF (edición simple). position: top, center, bottom."""
    if not text or not text.strip():
        raise PdfToolError("El texto a añadir no puede estar vacío.")
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF.")
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    page_idx = max(0, min(page_number - 1, len(doc) - 1))
    page = doc[page_idx]
    rect = page.rect
    if position == "top":
        r = fitz.Rect(50, 20, rect.width - 50, 55)
    elif position == "center":
        cx, cy = rect.width / 2, rect.height / 2
        r = fitz.Rect(cx - 200, cy - 15, cx + 200, cy + 15)
    else:
        r = fitz.Rect(50, rect.height - 55, rect.width - 50, rect.height - 20)
    page.insert_textbox(r, text.strip(), fontsize=11, fontname="helv", align=0)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


def sign_pdf(input_path: str, output_path: str, signer_name: str, signature_image_path: Optional[str] = None) -> None:
    """Añadir firma: texto 'Firmado por X el [fecha]' en la última página y opcionalmente una imagen de firma."""
    from datetime import datetime
    if not signer_name or not signer_name.strip():
        raise PdfToolError("El nombre del firmante no puede estar vacío.")
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF.")
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    page = doc[-1]
    rect = page.rect
    date_str = datetime.now().strftime("%d/%m/%Y")
    text = f"Firmado por {signer_name.strip()} el {date_str}"
    r_text = fitz.Rect(50, rect.height - 40, rect.width - 50, rect.height - 10)
    page.insert_textbox(r_text, text, fontsize=10, fontname="helv", align=2)
    if signature_image_path and Path(signature_image_path).exists():
        img_rect = fitz.Rect(50, rect.height - 90, 200, rect.height - 45)
        page.insert_image(img_rect, filename=signature_image_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


def images_to_pdf(image_paths: List[str], output_path: str) -> None:
    """Crear un PDF a partir de una lista de imágenes (Escanear a PDF)."""
    if not image_paths:
        raise PdfToolError("Se necesita al menos una imagen.")
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF.")
    doc = fitz.open()
    for path in image_paths:
        p = Path(path)
        if not p.exists():
            raise PdfToolError(f"Imagen no encontrada: {p.name}")
        img_doc = fitz.open(path)
        if img_doc.page_count >= 1:
            page = img_doc[0]
            rect = page.rect
            new_page = doc.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(new_page.rect, filename=path)
        img_doc.close()
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("No se pudo crear el PDF a partir de las imágenes.")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


def redact_pdf(input_path: str, output_path: str, words_comma_separated: str) -> None:
    """Censurar (redactar) palabras en el PDF: se dibujan rectángulos negros sobre las coincidencias."""
    if not words_comma_separated or not words_comma_separated.strip():
        raise PdfToolError("Indica al menos una palabra o frase a censurar (separadas por comas).")
    try:
        import fitz
    except ImportError:
        raise PdfToolError("Esta función requiere PyMuPDF.")
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    words = [w.strip() for w in words_comma_separated.split(",") if w.strip()]
    if not words:
        raise PdfToolError("Indica al menos una palabra a censurar.")
    for page in doc:
        for word in words:
            areas = page.search_for(word, quads=False)
            for rect in areas:
                page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()


def ocr_pdf(input_path: str, output_path: str) -> None:
    """Añadir capa de texto mediante OCR (PDF escaneado → texto buscable). Requiere pytesseract y pdf2image."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise PdfToolError(
            "OCR requiere PyMuPDF, pytesseract y Pillow. Instale: pip install pytesseract Pillow. "
            "En el sistema instale tesseract-ocr (ej: apt install tesseract-ocr tesseract-ocr-spa)."
        ) from e
    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        raise PdfToolError("El PDF no tiene páginas.")
    try:
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="spa+eng")
            if text and text.strip():
                rect = page.rect
                r = fitz.Rect(50, 50, rect.width - 50, rect.height - 50)
                page.insert_textbox(r, text.strip(), fontsize=8, fontname="helv", align=0)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
    finally:
        doc.close()
