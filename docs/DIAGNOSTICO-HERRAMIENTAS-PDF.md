# Diagnóstico Técnico: 18 Herramientas PDF

**Fecha:** 16 Feb 2026  
**Entorno:** Amazon Linux 2023, ARM64 (aarch64), t4g.medium (~4 GB RAM, swap 1.5 GB)  
**Objetivo:** Garantizar que las 18 herramientas de "Herramientas y procesos PDF" funcionen correctamente.

---

## 1. Resumen Ejecutivo

| Resultado | Detalle |
|-----------|---------|
| **Estado general** | ✅ **18/18 herramientas operativas** |
| **Migración de instancia** | ❌ **No necesaria** |
| **Dependencias** | ✅ Todas instaladas |
| **Recursos** | ✅ Suficientes con swap actual |

---

## 2. Resultado del Diagnóstico por Herramienta

| # | Herramienta | Endpoint | Estado | Librería principal |
|---|-------------|----------|--------|-------------------|
| 1 | Unir PDF | merge | ✅ OK | pypdf |
| 2 | Dividir PDF | split | ✅ OK | pypdf |
| 3 | Rotar PDF | rotate | ✅ OK | pypdf |
| 4 | Comprimir PDF | compress | ✅ OK | pypdf |
| 5 | Proteger PDF | protect | ✅ OK | pypdf |
| 6 | Desbloquear PDF | unlock | ✅ OK | pypdf |
| 7 | Ordenar PDF | order | ✅ OK | pypdf |
| 8 | Números de página | page-numbers | ✅ OK | PyMuPDF |
| 9 | Recortar PDF | crop | ✅ OK | pypdf |
| 10 | Marca de agua | watermark | ✅ OK | PyMuPDF |
| 11 | Reparar PDF | repair | ✅ OK | pypdf |
| 12 | PDF → PDF/A | pdfa | ✅ OK* | pypdf (reescritura) |
| 13 | Comparar PDF | compare | ✅ OK | pypdf |
| 14 | Editar PDF | edit | ✅ OK | PyMuPDF |
| 15 | Firmar PDF | sign | ✅ OK | PyMuPDF |
| 16 | Escanear a PDF | scan | ✅ OK | PyMuPDF |
| 17 | Censurar PDF | redact | ✅ OK | PyMuPDF |
| 18 | OCR PDF | ocr | ✅ OK | PyMuPDF + pytesseract |

\* PDF/A: implementación actual = reescritura del PDF (no validación estricta PDF/A-1b).

---

## 3. Dependencias del Sistema

| Dependencia | Tipo | Estado | Uso |
|-------------|------|--------|-----|
| pypdf 5.0.1 | Python | ✅ Instalado | merge, split, rotate, compress, protect, unlock, order, crop, repair, compare |
| PyMuPDF 1.24.10 | Python | ✅ Instalado | page-numbers, watermark, edit, sign, scan, redact, ocr |
| pytesseract 0.3.13 | Python | ✅ Instalado | ocr |
| tesseract-ocr 5.0.1 | Sistema | ✅ `/usr/bin/tesseract` | ocr (pytesseract lo invoca) |
| Pillow | Python | ✅ Instalado | ocr (conversión pixmap → PIL) |

**No se requieren nuevas instalaciones.**

---

## 4. Consumo de Recursos

### 4.1 Memoria y almacenamiento actual

```
RAM total: 3.7 GB
Swap: 1.5 GB (configurado y persistente)
Disco /: 16 GB, 84% usado, ~2.7 GB libres
```

### 4.2 Estimación por herramienta

| Herramienta | RAM típica | Notas |
|-------------|------------|-------|
| merge, split, order | ~50–200 MB | Proporcional al tamaño del PDF |
| compress, repair, pdfa | ~50–150 MB | pypdf en memoria |
| rotate, crop | ~50–150 MB | pypdf |
| protect, unlock | ~50–150 MB | pypdf con cifrado |
| watermark, edit, sign | ~80–250 MB | PyMuPDF + render |
| compare | ~100–300 MB | Dos PDF en memoria |
| scan (imágenes→PDF) | ~100–400 MB | PyMuPDF, N imágenes |
| redact | ~80–250 MB | PyMuPDF search + draw |
| page-numbers | ~80–200 MB | PyMuPDF |
| **ocr** | **~200–600 MB** | PyMuPDF + PIL + tesseract (más intensivo) |

### 4.3 Recomendaciones

- **No migrar instancia**: los picos de memoria están dentro de lo soportado con swap.
- **OCR en PDFs grandes**: puede acercarse a 600 MB; con swap 1.5 GB hay margen.
- **Límite de archivo**: 10 MB por archivo (configuración actual) limita picos de uso.

---

## 5. Limitaciones Conocidas (no bloqueantes)

| Herramienta | Limitación | Severidad |
|-------------|------------|-----------|
| **Comprimir PDF** | pypdf reescribe; compresión real limitada | Baja |
| **PDF/A** | Solo reescritura, no conversión PDF/A-1b estricta | Media |
| **Comparar PDF** | Solo texto extraído; no diff visual de layout | Baja |
| **OCR** | Requiere buena resolución; idioma spa+eng por defecto | Baja |

---

## 6. Arquitectura y Modularidad

- **Patrón Strategy**: cada herramienta = estrategia independiente (`REGISTRY` en `strategies.py`).
- **Router**: endpoints en `pdf_tools.py` delegan en `_execute_tool()`.
- **Aislamiento**: cada ejecución usa directorio temporal propio; no comparten estado.
- **Créditos**: uso compartido con conversiones y IA.

**No se detectan riesgos de regresión** en las herramientas que ya funcionan.

---

## 7. Propuesta de Acción

### Paso 1: Diagnóstico ✅ COMPLETADO

- Las 18 herramientas funcionan correctamente en pruebas unitarias.
- Dependencias instaladas.
- Sin necesidad de migración de instancia.

### Paso 2: Implementación

**No se requieren cambios obligatorios.** El sistema está operativo.

### Paso 3: Mejoras opcionales (prioridad baja)

Solo si se prioriza en el futuro:

1. **PDF/A estricto**: integrar `ocrmypdf` o `pikepdf` para validación PDF/A-1b.
2. **Comprimir PDF**: usar Ghostscript o PyMuPDF para compresión más agresiva.
3. **Comparar PDF**: añadir diff visual con librerías como `pdf-diff` (requiere más recursos).

### Paso 4: Pruebas end-to-end recomendadas

- Probar cada herramienta desde la UI de docaiplatform.com.
- Validar flujos: anónimo (3 usos) y usuario registrado (5 usos).
- Probar OCR con un PDF escaneado real (no solo texto embebido).

### Paso 5: Monitoreo

- Revisar logs tras usar OCR en PDFs grandes.
- Comprobar uso de swap si se procesan muchos PDF en paralelo.

---

## 8. Comando de Diagnóstico

Para repetir el diagnóstico:

```bash
cd /home/ec2-user/backend
source /home/ec2-user/.venv/bin/activate
PYTHONPATH=/home/ec2-user/backend python3 test_pdf_tools.py
```

Salida esperada: `RESULTADO: 18/18 herramientas OK`

---

## 9. Conclusión

- Las 18 herramientas están operativas con las dependencias actuales.
- No es necesario migrar instancia ni ampliar recursos en este momento.
- El diseño modular permite evolución futura sin impacto en el resto de funcionalidades.
