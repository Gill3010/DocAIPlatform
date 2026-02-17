# DocAI Platform – Contexto para continuar (post-migración de instancia)

**Usar este documento como prompt/contexto al abrir el asistente en la nueva instancia EC2.**

---

## 1. Resumen ejecutivo

- **Proyecto:** DocAI Platform – Sistema de conversión de documentos (docaiplatform.com)
- **Stack:** FastAPI (backend), React/Vite (frontend), SQLite, PM2
- **Infra:** AWS EC2, Amazon Linux 2023, ARM64 (aarch64)
- **Migración:** Instancia nueva creada desde AMI (upgrade t4g.medium → t4g.large, 8 GB RAM) para resolver OOM durante compilación de LibreDWG.

---

## 2. Lo que YA está implementado y funcionando

### 2.1 Conversiones de documentos
- PDF ↔ Word, PDF ↔ Excel, PDF ↔ PowerPoint, Excel/PPTX → PDF
- PDF/TXT/Word ↔ TXT (con placeholders `[Imagen]`)
- Word → XML (JATS), XML ↔ HTML ↔ Word

### 2.2 Sección “Imágenes y CAD” (18 cards explícitas)
- **Imagen → PDF:** PNG, JPG, JPEG → PDF
- **PDF → Imagen:** PDF → PNG, JPG, JPEG
- **Imagen → CAD:** PNG, JPG, JPEG → DXF  
- **CAD → Imagen:** DXF → PNG, JPG, JPEG  
- **DWG:** Cards para DWG→PNG/JPG/JPEG y PNG/JPG/JPEG→DWG existen en el frontend y backend, pero requieren herramienta DWG instalada (ver §4).

### 2.3 Mejoras PDF→Excel (parcial)
- Heurística anti-fragmentación (extract_text cuando tabla fragmenta)
- Imágenes posicionadas según bbox
- Celdas combinadas en encabezados  
- **Pendiente:** Afinar más; el usuario indicó refinarlo en otro momento.

### 2.4 OCR para PDF escaneados
- `backend/app/utils/pdf_ocr.py`: `is_pdf_scanned()`, `add_ocr_to_pdf()`
- Preprocesado en `converter.py` si `USE_OCR_FOR_SCANNED_PDF=true`
- Dependencias: Tesseract, Ghostscript, ocrmypdf (instaladas)

### 2.5 Fallback Camelot en PDF→Excel
- `USE_CAMELOT_FALLBACK=true` en config
- camelot-py para tablas complejas

### 2.6 Word-to-JATS Ensemble (nuevo)
- Plataforma de conversión docx→xml de alta precisión para OJS
- Módulo en `word-to-jats/` con JatsMerger, adaptadores GROBID/Pandoc/Bedrock
- Integración en backend: `USE_JATS_ENSEMBLE=true` y `GROBID_URL` (opcional)
- Ver `docs/INTEGRACION-WORD-TO-JATS.md`

### 2.7 Arquitectura modular de conversiones
- `conversion_strategy.py`: decide local / ECS / JATS según `prefers_local` del conversor y config
- `conversion_orchestrator.py`: ejecuta la conversión (router solo delega)
- `conversion_request_service.py`: orquesta upload, conversión y actualización de BD
- `converters/__init__.py`: discovery automático de conversores vía pkgutil (no imports manuales)
- `BaseConverter.prefers_local`: los conversores declaran si prefieren ejecución local (default True)

---

## 3. Archivos modificados (referencia)

| Ruta | Cambios principales |
|------|---------------------|
| `backend/app/utils/converters/office_converters.py` | PDF→Excel: extract_text, posicionamiento de imágenes, celdas combinadas |
| `backend/app/utils/converters/image_converters.py` | PDF→PNG/JPG/JPEG (PyMuPDF) |
| `backend/app/utils/converters/cad_converters.py` | DXF→PNG/JPG/JPEG, DWGToImageConverter, ImageToDWGConverter (ODA o LibreDWG) |
| `backend/app/utils/converters/__init__.py` | Registro de DWGToImageConverter, ImageToDWGConverter |
| `backend/app/utils/converter.py` | Preprocesado OCR para PDF |
| `backend/app/utils/pdf_ocr.py` | Nuevo: detección y OCR de PDF escaneados |
| `backend/app/core/config.py` | USE_OCR_FOR_SCANNED_PDF, USE_CAMELOT_FALLBACK |
| `backend/app/routers/convert.py` | Delega a conversion_orchestrator (arquitectura modular) |
| `backend/app/services/conversion_strategy.py` | Resuelve motor: local, ECS o JATS según prefers_local y config |
| `backend/app/services/conversion_orchestrator.py` | Ejecuta conversión según estrategia resuelta |
| `backend/app/services/conversion_request_service.py` | Orquesta upload + conversión + BD |
| `backend/app/utils/converters/__init__.py` | Discovery automático de conversores (pkgutil) |
| `frontend/src/constants/conversions.ts` | 18 cards específicas Imágenes y CAD, etiquetas PNG/JPG/JPEG/DXF/DWG |
| `frontend/src/hooks/useFileSelection.ts` | Formatos válidos incluyen DWG |
| `frontend/src/components/FileDropZone/FileDropZone.tsx` | DWG en lista de formatos |

---

## 4. Lo que FALTA: soporte real para DWG

### 4.1 Situación actual
- **DWGToImageConverter** y **ImageToDWGConverter** usan `ezdxf.addons.odafc` (ODA File Converter).
- ODA solo tiene binarios x64; esta instancia es ARM64 (aarch64).
- La compilación de **LibreDWG** (dwg2dxf, dxf2dwg) se intentó pero provocó OOM en t4g.medium (4 GB RAM).

### 4.2 Objetivo
- **DWG → PNG/JPG/JPEG:** DWG→DXF (dwg2dxf) → DXF→imagen (ezdxf/matplotlib)
- **PNG/JPG/JPEG → DWG:** Imagen→DXF (ezdxf) → DXF→DWG (dxf2dwg)

### 4.3 Pasos a realizar (con instancia t4g.large, 8 GB RAM)

1. **Instalar LibreDWG desde código:**
   ```bash
   cd /tmp
   git clone --depth 1 https://github.com/LibreDWG/libredwg.git
   cd libredwg
   ./autogen.sh
   ./configure --prefix=/usr/local
   make -j2    # Usar -j2 para reducir pico de RAM; -j4 puede provocar OOM
   sudo make install
   ```

2. **Ajustar `cad_converters.py`:**
   - En **DWGToImageConverter**: si ODA no está disponible, usar `dwg2dxf` (subprocess) para convertir DWG→DXF, luego pasar el DXF al flujo existente DXF→imagen.
   - En **ImageToDWGConverter**: crear DXF con ezdxf, luego llamar a `dxf2dwg` para obtener el DWG.

3. **Configurar rutas:**
   - Verificar que `dwg2dxf` y `dxf2dwg` estén en el PATH tras `make install`.
   - Opcional: variable de entorno `LIBREDWG_BIN` o similar si se instalan en ruta distinta.

---

## 5. Verificaciones rápidas en la nueva instancia

```bash
# Memoria
free -h

# Servicios
pm2 list
curl -s http://127.0.0.1:8000/health

# LibreDWG (tras instalación)
which dwg2dxf dxf2dwg
dwg2dxf --help
```

---

## 6. Orden de prioridad al retomar

1. Confirmar que backend, frontend y servicios responden.
2. Instalar LibreDWG (`dwg2dxf`, `dxf2dwg`) con `make -j2`.
3. Actualizar `DWGToImageConverter` e `ImageToDWGConverter` para usar LibreDWG como fallback cuando ODA no esté disponible.
4. Probar conversiones DWG desde docaiplatform.com.
5. (Opcional) Seguir afinando PDF→Excel.

---

## 7. Prompt corto para pegar al asistente

```
Estoy en DocAI Platform (docaiplatform.com) sobre una nueva instancia EC2 (t4g.large, 8 GB RAM) creada desde AMI.

Lee el archivo docs/PROYECTO-CONTEXTO-CONTINUACION.md para el contexto completo.

Tareas pendientes:
1. Instalar LibreDWG (dwg2dxf, dxf2dwg) desde código en /tmp/libredwg.
2. Modificar backend/app/utils/converters/cad_converters.py para usar LibreDWG como fallback cuando ODA no esté disponible: DWG→imagen vía dwg2dxf+DXFToPNG; imagen→DWG vía PNGToDXF+dxf2dwg.
3. Verificar que las conversiones DWG funcionen correctamente.
```
