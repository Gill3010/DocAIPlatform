# Setup: OCR y Camelot (mejoras de conversión)

## Pasos para activar las mejoras

### 1. Dependencias Python (ya añadidas a requirements.txt)

```bash
cd backend
pip install -r requirements.txt
```

Incluye: `ocrmypdf`, `camelot-py[base]`, `opencv-python-headless`.

### 2. Tesseract (sistema, para OCR de PDF escaneados)

```bash
# Amazon Linux 2023
sudo dnf install tesseract tesseract-langpack-spa tesseract-langpack-eng
```

Sin Tesseract, las conversiones siguen funcionando; solo no se podrá OCR en PDFs escaneados.

### 3. Variables de entorno (opcional)

En `.env` o variables de sistema:

```bash
USE_OCR_FOR_SCANNED_PDF=true    # OCR para PDF escaneados (default: true)
USE_CAMELOT_FALLBACK=true        # Fallback camelot en PDF→Excel (default: true)
```

Para desactivar y volver al comportamiento anterior:

```bash
USE_OCR_FOR_SCANNED_PDF=false
USE_CAMELOT_FALLBACK=false
```

### 4. Reiniciar el backend

Tras instalar dependencias y Tesseract, reiniciar el servicio del backend para cargar los cambios.
