# Estado de integración Word ↔ XML JATS (17 feb 2025)

## Respuesta directa

**Sí.** Todo está integrado en **un solo sistema** para las conversiones Word ↔ XML JATS en la web (docaiplatform.com).

**La web usa Bedrock cuando hay tokens.** Con `USE_BEDROCK_FOR_JATS=true` (en .env), la conversión Word→XML intenta Bedrock primero y hace fallback automático a local si falla (sin tokens, error, etc.).

---

## Qué está integrado (UN sistema, la web)

| Componente | Estado | Ubicación |
|------------|--------|-----------|
| **Word → XML** (docx→xml) | ✅ Integrado | `word_to_jats_service` → Bedrock (si tokens) o `DocxToJATSConverter` (fallback) |
| **XML → Word** (xml→docx) | ✅ Integrado | `backend/app/utils/converters/jats_converters.py` → `JatsToDocxConverter` |
| Frontend (cards, selector) | ✅ Integrado | `frontend/src/constants/conversions.ts` (docx↔xml) |
| Configuración | ✅ Activa | `USE_JATS_ENSEMBLE=true` en `backend/.env` |
| Rutas de descarga | ✅ Corregido | Rutas absolutas + fix Unicode en nombres de archivo |

**Flujo web:** Usuario sube en docaiplatform.com → backend/convert.py → word_to_jats_service (docx→xml) o registry (xml→docx) → archivo convertido → descarga.

---

## Flujo Word → XML en la web

- **Con tokens (Bedrock disponible):** usa Claude para conversión de mayor calidad
- **Sin tokens o error:** fallback automático a `DocxToJATSConverter` (local)
- **Config:** `USE_BEDROCK_FOR_JATS=true` en `.env`

---

## Qué es cada cosa (para que no haya confusión)

| Proyecto / carpeta | ¿Qué es? | ¿Usado por la web? | ¿Usa Bedrock? |
|--------------------|----------|--------------------|---------------|
| **backend/** | API de docaiplatform.com | ✅ Sí | ❌ No (para Word↔XML) |
| **frontend/** | UI de docaiplatform.com | ✅ Sí | ❌ No |
| **word-to-jats/** | Infraestructura CDK (Lambdas, GROBID, Bedrock) | ❌ No | Sí (opcional) |
| **docai-platform/** | CLI con procesamiento con IA | ❌ No | ✅ Sí |

- **Web:** Un solo flujo: backend + frontend, sin Bedrock.
- **docai-platform (CLI):** Herramienta aparte que sí usa Bedrock; ahí aplican las 24h de tokens.

---

## Verificación rápida

1. **Word → XML en la web:** Entra a docaiplatform.com/convert, elige Word → XML, sube un .docx y descarga el resultado. No necesitas esperar 24h.
2. **XML → Word en la web:** Mismo flujo con un .xml como origen.

---

## Resumen

- ✅ Todo lo implementado hoy está integrado en la web.
- ✅ No hay dos sistemas separados para Word ↔ XML JATS en docaiplatform.com.
- ✅ Puedes probar las conversiones **ya**.
- ⏳ La espera de 24h afecta solo al CLI (`docai-platform`), que usa Bedrock. La web no depende de eso para Word ↔ XML.
