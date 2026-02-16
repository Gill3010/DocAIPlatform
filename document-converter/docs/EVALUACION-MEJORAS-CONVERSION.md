# Evaluación: Mejoras de Calidad, Estabilidad y Fidelidad en Conversiones de Documentos

## 1. Estado actual del sistema

| Conversión        | Motor principal                    | Fallback                    | Observaciones                                      |
|------------------|-------------------------------------|-----------------------------|----------------------------------------------------|
| PDF → Word       | pdf2docx                            | pypdf + python-docx         | Tablas e imágenes razonables; PDF escaneados: pobre |
| Word → PDF       | LibreOffice                         | ReportLab                   | Buena fidelidad si LibreOffice disponible          |
| Excel → PDF      | LibreOffice / Docker                | ReportLab (con colores)     | Depende de LibreOffice en host o Docker            |
| PowerPoint → PDF | LibreOffice / Docker                | —                           | Depende de LibreOffice                             |
| PDF → Excel      | pdfplumber + PyMuPDF                | —                           | Una hoja por página; tablas complejas pueden fallar |
| PDF → PowerPoint | PyMuPDF (imagen por página)         | —                           | Conversión visual, no editable                     |
| PDF → TXT        | PyMuPDF                             | —                           | Placeholders [Imagen]                              |
| Word → TXT       | python-docx                         | —                           | Placeholders [Imagen]                              |
| TXT → Word       | python-docx                         | —                           | Simple, estable                                    |

---

## 2. Librerías adicionales recomendadas

### 2.1. ocrmypdf + Tesseract (alta prioridad)

**Función:** Añade OCR a PDFs escaneados antes de cualquier conversión.

**Justificación:**
- Muchos PDFs son escaneos sin texto seleccionable.
- pdf2docx, pdfplumber y pypdf no extraen texto de escaneos.
- OCRmyPDF añade una capa de texto invisible manteniendo el original (PDF/A).

**Beneficio:** PDF escaneados convertibles a Word, Excel y TXT con texto real.

**Coste:** $0 (open source). Tesseract necesita ~100 MB y ocr es intensivo en CPU.

**Implementación:** Media. Dependencias: `ocrmypdf`, Tesseract en el sistema. Integración: detectar PDF sin texto → ejecutar OCR → seguir con el flujo normal.

**Comando instalación:**
```bash
# Amazon Linux 2023
sudo dnf install tesseract tesseract-langpack-spa tesseract-langpack-eng
pip install ocrmypdf
```

---

### 2.2. camelot-py (media prioridad)

**Función:** Extracción de tablas en PDF→Excel para tablas complejas o sin bordes.

**Justificación:**
- pdfplumber es bueno para tablas con líneas.
- camelot-py mejora en tablas tipo "stream" (sin bordes) y ofrece métricas de calidad.
- Puede usarse como complemento o fallback en páginas problemáticas.

**Beneficio:** Mejor precisión en tablas complejas en PDF→Excel.

**Coste:** $0. Depende de opencv-python y ghostscript; añade ~50 MB.

**Implementación:** Media. Alternativa: probar pdfplumber primero, camelot solo en fallos o baja calidad.

---

### 2.3. pypdfium2 (ya en uso)

**Función:** Parser PDF de alto rendimiento. Usado internamente por ocrmypdf.

**Estado:** Ya está en `requirements.txt`. Puede usarse para detección rápida de si un PDF tiene texto (sin OCR).

---

## 3. APIs externas especializadas

### 3.1. Adobe PDF Services API (Extract API)

**Función:** PDF → datos estructurados (JSON) con alta fidelidad.

**Justificación:**
- Buena conservación de estructura (tablas, figuras, metadatos).
- Salida JSON que se puede transformar a DOCX/Excel con más precisión que muchas librerías.
- Soporte para PDF escaneados con OCR integrado.

**Beneficio:** Mejor calidad en PDF complejos, especialmente PDF→Excel y PDF→Word.

**Coste:** ~$0.05–0.15 por documento; plan gratuito limitado.

**Implementación:** Media–alta. Requiere API key, cliente HTTP, mapeo JSON → DOCX/Excel.

**Recomendación:** Solo si el volumen y la criticidad del negocio justifican el coste; no sustituir el stack actual, sino como opción premium.

---

### 3.2. Aspose.Words / Aspose.Cells Cloud

**Función:** Conversiones Office de alta fidelidad (PDF↔Word, PDF↔Excel, etc.).

**Justificación:**
- Calidad superior a pdf2docx y LibreOffice en muchos escenarios.
- API REST sencilla de integrar.

**Beneficio:** Mayor fidelidad de formato, tablas y estilos.

**Coste:** Planes desde ~$30/mes; facturación por documento en algunos planes.

**Implementación:** Media. Integración REST, manejo de errores y reintentos.

**Recomendación:** Alternativa si se prioriza calidad sobre coste; útil para flujos críticos o empresariales.

---

### 3.3. ConvertAPI

**Función:** API de conversión multi-formato.

**Justificación:**
- Actualizaciones recientes en OCR y tablas.
- Integración simple, pago por uso.

**Beneficio:** Menor carga de mantenimiento en comparación con soluciones propias.

**Coste:** Pago por conversión; planes desde ~$8/mes.

**Implementación:** Baja. Cliente HTTP y manejo de archivos.

---

## 4. Herramientas nativas en AWS

### 4.1. Amazon Textract

**Función:** OCR y extracción de texto, tablas y formularios.

**Justificación:**
- OCR de alta calidad para PDFs escaneados.
- Extracción de tablas estructuradas.
- Integración natural con el ecosistema AWS.

**Beneficio:** PDF escaneados convertibles con buena calidad, soporte multi-idioma y escalado.

**Coste:** ~$1.50 por 1000 páginas (Sync) o $0.0015 por página (Async). Límite 5 MB por documento en Sync.

**Implementación:** Media. Uso de boto3; flujo: S3 → Textract → post-procesado a DOCX/Excel/TXT.

**Recomendación:** Alternativa seria a ocrmypdf+Tesseract si ya se usa AWS y se quiere menos mantenimiento del stack de OCR. Útil para PDF→Excel y PDF→Word con escaneos.

---

### 4.2. Lambda + LibreOffice (Layer o Docker)

**Función:** LibreOffice en Lambda para conversiones Office→PDF, PDF→Office, etc.

**Justificación:**
- Escalado por petición sin servidores siempre encendidos.
- Evita dependencia de EC2 solo para LibreOffice.
- Layers preconstruidos (p. ej. shelfio/libreoffice-lambda-layer) permiten un despliegue rápido.

**Beneficio:** Mejor escalabilidad; pago por uso en lugar de instancias fijas.

**Coste:** ~$0.0000166667/GB-segundo + solicitudes; una conversión típica ~$0.01–0.05.

**Implementación:** Media–alta. Configuración de Lambda, S3, colas (SQS) si se usa asincronía.

**Recomendación:** Útil si se quiere mover conversiones de EC2 a Lambda para reducir coste fijo; requiere rediseñar el flujo actual.

---

### 4.3. ECS Fargate para conversiones pesadas

**Función:** Ya usáis ECS para algunas conversiones.

**Justificación:**
- Aislamiento por tarea.
- Escalado horizontal.
- Menos riesgo de afectar al backend principal.

**Beneficio:** Mayor estabilidad y escalabilidad para trabajos largos o pesados.

**Coste:** Fargate factura por vCPU/hora y memoria; más caro que EC2 reservado, más flexible.

**Recomendación:** Mantener y ampliar gradualmente según carga.

---

## 5. Mejoras de rendimiento y escalabilidad

### 5.1. Detección previa de PDF escaneado

**Acción:** Detectar si el PDF tiene texto antes de convertir.

**Implementación:** PyMuPDF `page.get_text()` o pypdfium2; si la página no tiene texto, marcar para OCR.

**Beneficio:** Evitar intentos de conversión directa en escaneos; ahorro de CPU y tiempo.

**Complejidad:** Baja.

---

### 5.2. Cache de conversiones idénticas

**Acción:** Cache (p. ej. Redis) con hash del archivo como clave.

**Implementación:** Calcular hash (SHA-256) del input; si existe en cache, devolver resultado sin reconvertir.

**Beneficio:** Menor carga en conversiones repetidas (mismos archivos, usuarios que re-convierten).

**Complejidad:** Media. Redis, límites de tamaño y TTL.

---

### 5.3. Cola asíncrona (Celery / SQS)

**Acción:** Conversiones largas en background con notificación al terminar.

**Justificación:** Ya hay conversiones síncronas locales para evitar timeouts de Cloudflare; una cola permite trabajos más largos sin bloquear el request.

**Beneficio:** Conversiones de muchos MB o muchas páginas sin timeouts; mejor experiencia para el usuario.

**Complejidad:** Media–alta. Infraestructura de cola, workers, estado y notificaciones.

---

### 5.4. Límites y prevalidación

**Acción:** Validar tamaño y número de páginas antes de convertir; rechazar o limitar archivos muy grandes.

**Beneficio:** Menor riesgo de OOM o bloqueos; mejor estabilidad.

**Complejidad:** Baja.

---

## 6. Cambiar o complementar el motor actual

| Opción                     | Recomendación | Motivo principal                                       |
|----------------------------|---------------|--------------------------------------------------------|
| Mantener pdf2docx          | Sí            | Buen equilibrio entre calidad y coste; actualizar versión |
| Mantener LibreOffice       | Sí            | Buena fidelidad; base del sistema actual               |
| Mantener pdfplumber        | Sí            | Buen rendimiento en tablas; complementar con camelot    |
| Añadir ocrmypdf + Tesseract| Sí            | Cubre PDF escaneados; bajo coste, impacto alto         |
| Añadir camelot             | Opcional      | Mejora PDF→Excel en tablas complejas                   |
| API externa (Adobe/Aspose) | Opcional      | Para casos premium si el presupuesto lo permite        |
| Textract                   | Opcional      | Si se prioriza AWS y se quieren menos dependencias OCR |

---

## 7. Plan de implementación sugerido

### Fase 1 (prioridad alta, ~1–2 semanas)

1. **OCR para PDF escaneados**
   - Instalar Tesseract y ocrmypdf.
   - Detectar PDF sin texto.
   - Flujo: PDF escaneado → OCR → conversión normal.
   - Coste: $0. Complejidad: media.

2. **Pre-detección de PDF con/sin texto**
   - Evitar conversión directa cuando no hay texto.
   - Coste: $0. Complejidad: baja.

### Fase 2 (prioridad media, ~2–4 semanas)

3. **camelot-py en PDF→Excel**
   - Fallback o modo alternativo cuando pdfplumber no detecte tablas.
   - Coste: $0. Complejidad: media.

4. **Cache de conversiones**
   - Redis (o similar) por hash de archivo.
   - Coste: bajo (Redis). Complejidad: media.

### Fase 3 (prioridad baja / según demanda)

5. **API externa premium**
   - Adobe o Aspose para clientes que necesiten máxima fidelidad.
   - Coste: variable. Complejidad: media.

6. **Amazon Textract**
   - Sustituir o complementar OCR local si se prioriza el ecosistema AWS.
   - Coste: por uso. Complejidad: media.

---

## 8. Resumen ejecutivo

| Mejora                      | Beneficio principal              | Coste   | Complejidad | Prioridad |
|----------------------------|----------------------------------|---------|-------------|-----------|
| ocrmypdf + Tesseract       | PDF escaneados convertibles      | $0      | Media       | Alta      |
| camelot-py                 | Tablas complejas en PDF→Excel     | $0      | Media       | Media     |
| Pre-detección PDF sin texto| Evitar conversiones fallidas     | $0      | Baja        | Alta      |
| Cache Redis                | Menor carga, más velocidad       | Bajo    | Media       | Media     |
| Adobe/Aspose API           | Máxima fidelidad                 | Medio   | Media       | Baja      |
| Amazon Textract            | OCR en la nube, escala AWS       | Por uso | Media       | Baja      |
| Lambda + LibreOffice       | Escalado serverless              | Bajo    | Alta        | Baja      |

El motor actual (pdf2docx, LibreOffice, pdfplumber, PyMuPDF) es sólido. Las mejoras más eficaces son **OCR para escaneos** y **mejoras en tablas PDF→Excel**, ambas con coste cero. Las APIs externas y los servicios AWS son útiles para escenarios específicos o casos premium.
