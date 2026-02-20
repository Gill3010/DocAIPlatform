# Integración Word-to-JATS con DocAI Platform

## Estado: Implementado e Integrado

**Cambio aplicado:** El servicio `word_to_jats_service` ahora usa directamente `DocxToJATSConverter`, que produce JATS XML completo (metadatos, resumen, secciones, tablas, referencias, imágenes) compatible con OJS. No depende de GROBID/Pandoc/Bedrock para funcionar.

La integración está activa. Para habilitarla:

### 1. Configuración (.env o variables de entorno)

```env
USE_JATS_ENSEMBLE=true
GROBID_URL=http://localhost:8070   # Opcional: URL de GROBID si está desplegado
```

### 2. Ruta del módulo word-to-jats

El backend busca el módulo en `../word-to-jats/src` (relativo al directorio del proyecto).
Asegúrate de que el directorio `word-to-jats` exista junto a `backend`:

```
/home/ec2-user/
├── backend/
├── frontend/
├── word-to-jats/   # Módulo ensemble
```

### 3. Comportamiento

- **USE_JATS_ENSEMBLE=true**: Al convertir docx→xml, se usa el nuevo flujo (JatsMerger + GROBID opcional + Pandoc opcional).
- **USE_JATS_ENSEMBLE=false** (por defecto): Se usa el convertidor `DocxToJATSConverter` existente.

### 4. Dependencias del ensemble

- **GROBID** (opcional): Si `GROBID_URL` está definida y el servicio responde, se usa para metadatos y bibliografía.
- **Pandoc** (opcional): Si está instalado (`apt install pandoc`), se usa para estructura de contenido.
- **python-docx**: Siempre disponible, usado como fallback para título y párrafos.
