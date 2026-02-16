# Plan de integración: mejoras sin costo

Ubicación exacta de cada cambio para no romper conversiones actuales.

---

## 1. Nuevo módulo: detección y OCR de PDF escaneados

### Archivo nuevo: `backend/app/utils/pdf_ocr.py`

**Función:** Lógica central de detección y OCR reutilizable.

| Función | Descripción | Dependencias |
|--------|-------------|--------------|
| `is_pdf_scanned(input_path: str) -> bool` | True si el PDF tiene poco o ningún texto extraíble (PyMuPDF, muestreo de primeras páginas) | PyMuPDF (ya existe) |
| `add_ocr_to_pdf(input_path: str, output_path: str) -> bool` | Ejecuta ocrmypdf y escribe en `output_path`. Devuelve True si OK | ocrmypdf, Tesseract en sistema |

**Configuración:** `config.py`

```python
USE_OCR_FOR_SCANNED_PDF: bool = True   # Activar/desactivar OCR
```

**Flujo interno:**

```
is_pdf_scanned(path):
  - Abrir PDF con fitz
  - Para las primeras N páginas (ej. 3), page.get_text()
  - Si la mayoría tienen < X caracteres → considerar escaneado
  - Retornar True/False
```

---

## 2. Integración de OCR: punto único en `converter.py`

### Archivo: `backend/app/utils/converter.py`

**Cambios en `convert_file()`:**

```
ENTRADA: input_path, output_path, source_format, target_format

1. effective_input = input_path
2. temp_ocr_path = None

3. SI source == 'pdf' Y settings.USE_OCR_FOR_SCANNED_PDF:
   - SI is_pdf_scanned(input_path):
     - temp_ocr_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
     - add_ocr_to_pdf(input_path, temp_ocr_path.name)
     - effective_input = temp_ocr_path.name

4. converter = registry.get_converter(source, target)
5. resultado = converter.convert(effective_input, output_path)

6. SI temp_ocr_path:
   - os.unlink(temp_ocr_path.name)

7. RETORNAR resultado
```

No se tocan los converters individuales. Solo se añade lógica de preprocesado antes de la llamada al converter.

---

## 3. Conversores que usan PDF como entrada

Todos reciben un PDF ya procesado (con OCR si era escaneado):

| Conversor | Archivo | Método | Cambios |
|-----------|---------|--------|---------|
| PDF→Word | `pdf_docx_converters.py` | `PDFToDocxConverter.convert()` | Ninguno (usa input que ya viene preparado) |
| PDF→Excel | `office_converters.py` | `PDFToExcelConverter.convert()` | Ninguno para OCR; sí para camelot (ver §4) |
| PDF→PowerPoint | `office_converters.py` | `PDFToPptxConverter.convert()` | Ninguno |
| PDF→TXT | `text_converters.py` | `PDFToTextConverter.convert()` | Ninguno |

El preprocesado de OCR ocurre en `converter.py` antes de elegir el converter.

---

## 4. Fallback camelot en PDF→Excel

### Archivo: `backend/app/utils/converters/office_converters.py`

**Clase:** `PDFToExcelConverter`

**Configuración:** `config.py`

```python
USE_CAMELOT_FALLBACK: bool = True   # Fallback para tablas complejas
```

**Lugar del cambio:** En el bucle `for page_num, page in enumerate(pdf.pages, 1)`.

Flujo actual (resumido):

```python
tables = page.extract_tables(table_settings=table_settings_lines)
if not tables:
    tables = page.extract_tables(table_settings=table_settings_text)
if not tables:
    text = page.extract_text()
    if text:
        tables = [[line] for line in text.splitlines()]
        tables = [tables] if tables else []

# Aquí: si tables sigue vacío o muy pobre
```

**Cambio a añadir:**

```python
# Después del bloque anterior, ANTES de "if not tables:"
if (not tables or _is_tables_poor_quality(tables)) and settings.USE_CAMELOT_FALLBACK:
    try:
        import camelot
        camelot_tables = camelot.read_pdf(input_path, pages=str(page_num))
        if camelot_tables:
            tables = [t.df.values.tolist() for t in camelot_tables]
    except Exception:
        pass  # Mantener tables actual (o vacío)
```

**Función auxiliar nueva (misma clase o módulo):**

```python
def _is_tables_poor_quality(tables) -> bool:
    """True si las tablas parecen insuficientes (muy pocas celdas, etc.)."""
    if not tables:
        return True
    total_cells = sum(len(r) for t in tables for r in t if t)
    return total_cells < 2  # Ajustar umbral si hace falta
```

Solo se usa camelot cuando pdfplumber no devuelve tablas o devuelve tablas pobres. Si camelot falla, se sigue con el resultado actual de pdfplumber.

---

## 5. Resumen de archivos afectados

| Archivo | Tipo de cambio | Riesgo |
|---------|----------------|--------|
| `backend/app/utils/pdf_ocr.py` | Nuevo | Nuevo código, no modifica lógica existente |
| `backend/app/core/config.py` | Añadir flags | Solo lectura |
| `backend/app/utils/converter.py` | Añadir preprocesado PDF | Bajo (fallback seguro) |
| `backend/app/utils/converters/office_converters.py` | Fallback camelot en PDF→Excel | Bajo (solo path alternativo) |
| `backend/requirements.txt` | Añadir `ocrmypdf`, `camelot-py` | Bajo |

---

## 6. Diagrama de flujo

### PDF con texto (caso normal)

```
convert_file(pdf, docx)
  → is_pdf_scanned? NO
  → effective_input = input_path (sin cambios)
  → PDFToDocxConverter.convert(input_path, output_path)
  → flujo actual sin cambios
```

### PDF escaneado (nuevo path)

```
convert_file(pdf, docx)
  → is_pdf_scanned? SÍ
  → add_ocr_to_pdf(input_path, temp.pdf)
  → effective_input = temp.pdf
  → PDFToDocxConverter.convert(temp.pdf, output_path)
  → cleanup temp.pdf
```

### PDF→Excel con tablas complejas (fallback camelot)

```
PDFToExcelConverter.convert()
  → página N: pdfplumber.extract_tables() → vacío o pobre
  → USE_CAMELOT_FALLBACK? SÍ
  → camelot.read_pdf() → tablas
  → usar tablas de camelot para esa página
  → resto del flujo igual
```

---

## 7. Dependencias del sistema (instalar en el servidor)

```bash
# Tesseract (para ocrmypdf - OCR de PDF escaneados)
sudo dnf install tesseract tesseract-langpack-spa tesseract-langpack-eng

# Opcional: Ghostscript (camelot puede usar pdfium por defecto)
# sudo dnf install ghostscript
```

Sin Tesseract, el OCR no funcionará pero el resto de conversiones sí (sin regresión).

**Python:**

```text
# requirements.txt
ocrmypdf>=17.0.0
camelot-py[cv]>=0.11.0
opencv-python-headless>=4.8.0   # requisito de camelot
```

---

## 8. Orden de implementación sugerido

1. Crear `pdf_ocr.py` con `is_pdf_scanned` y `add_ocr_to_pdf`.
2. Añadir flags en `config.py`.
3. Integrar OCR en `converter.py`.
4. Probar PDF escaneados con OCR activado y desactivado.
5. Añadir fallback camelot en `PDFToExcelConverter`.
6. Probar PDF→Excel con tablas complejas.
7. Verificar que todas las conversiones actuales siguen funcionando.

---

## 9. Rollback rápido

Si algo falla:

```bash
# .env o variables de entorno
USE_OCR_FOR_SCANNED_PDF=false
USE_CAMELOT_FALLBACK=false
```

Con esto se desactivan las nuevas rutas y se vuelve al comportamiento actual.
