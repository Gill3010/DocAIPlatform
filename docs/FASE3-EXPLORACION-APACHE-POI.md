# Fase 3: Exploración Apache POI para PDF → Excel

## Conclusión

**Apache POI no es viable para mejorar la conversión PDF → Excel en este proyecto.**

## Justificación técnica

### ¿Qué es Apache POI?

Apache POI es una librería Java para leer y escribir formatos de Microsoft Office:
- Excel (XLS, XLSX)
- Word (DOC, DOCX)
- PowerPoint (PPT, PPTX)

### ¿Puede POI convertir PDF a Excel?

**No.** Apache POI solo manipula archivos Office. No lee ni interpreta PDFs.

La conversión PDF → Excel requiere dos pasos separados:

1. **Extracción de tablas del PDF** — Requiere librerías de parsing de PDF (PDFBox, iText, Tabula, etc.).
2. **Escritura a Excel** — Aquí POI podría usarse.

### Integración vía JPype

Teóricamente se podría invocar Java (POI + PDFBox) desde Python mediante JPype:

- **Complejidad alta:** Configuración de JVM, rutas, dependencias Java.
- **Beneficio marginal:** Nuestro stack actual (pdfplumber, camelot, img2table, openpyxl) ya resuelve ambos pasos.
- **Mantenibilidad:** Añade Java al stack Python existente.

### Recomendación

**Mantener el enfoque actual en Python:**

- `pdfplumber` — Tablas con líneas explícitas o inferidas por texto.
- `camelot` — Lattice (tablas con bordes) y stream (tablas sin bordes).
- `img2table` — PDFs escaneados con OCR (Tesseract).
- `openpyxl` — Generación de XLSX.

Las mejoras de la Fase 3 (afinado de parámetros de pdfplumber y Camelot) aportan más valor que una integración con Apache POI.

---

*Documento generado en el marco del plan de mejora de conversiones de la sección Documentos.*
