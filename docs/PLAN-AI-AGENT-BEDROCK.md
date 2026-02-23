# Plan de Implementación: AI Agent Pro (Amazon Bedrock)

## Análisis de Estructura Actual

### A. Frontend: `src/components/AIAssistantFAB/`

| Archivo | Líneas | Responsabilidad |
|---------|--------|-----------------|
| `AIAssistantFAB.tsx` | ~282 | Componente único del asistente. Estado local para mensajes, input, créditos. Sin persistencia ni historial. |
| `AIAssistantFAB.css` | ~386 | Estilos del panel dockeado, header, mensajes, input, FAB. |

**Estado actual:**
- Mensajes en `useState<Message[]>` (no persistidos).
- Llamada a `apiService.sendChatMessage(message)` sin `sessionId` ni `chatId`.
- Respuesta mostrada como texto plano (sin Markdown ni enlaces clicables).
- Sin panel lateral para chats.
- Sin subida de archivos.
- Sin componente "Nuevo Chat".

---

### B. Backend: `backend/app/routers/ai.py`

| Endpoint | Método | Función |
|----------|--------|---------|
| `/ai/chat` | POST | Recibe `{ message }`, responde con `{ message, credits_remaining }`. Usa OpenAI `gpt-4o-mini`. |
| `/ai/credits` | GET | Devuelve créditos restantes (auth/anónimo). |

**Estado actual:**
- Cliente OpenAI directo en el router.
- Sin `ai_agent_service` dedicado.
- Sin modelos `ChatSession` ni `ChatMessage`.
- Sin soporte para archivos adjuntos.
- Prompt de sistema básico, sin contexto de herramientas ni URLs.

---

### C. APIs y dependencias existentes

| Recurso | Ubicación | Uso |
|---------|-----------|-----|
| `api/ai.ts` | `frontend/src/services/api/ai.ts` | `sendChatMessage`, `getAICredits` |
| `ai_service.py` | `backend/app/services/ai_service.py` | Créditos (check, consume, get) |
| Bedrock | `bedrock_jats_service.py`, `config.py` | `BEDROCK_REGION`, `BEDROCK_MODEL_ID` ya usados |
| Conversiones/PDF tools | `frontend/src/constants/conversions.ts` | `getDashboardConversions()`, `PDF_TOOLS`, URLs: `/convert?from=&to=`, `/pdf-tools?tool=` |

---

## Plan de Ejecución Paso a Paso

### Fase 1: Backend – Servicio Bedrock y modelo de datos

#### 1.1 Crear `app/services/ai_agent_service.py`

**Objetivo:** Servicio modular que encapsula la comunicación con Bedrock.

**Contenido mínimo:**
- Cliente `bedrock-runtime` usando `boto3` y credenciales/región de `settings` (sin hardcode).
- Función `invoke_claude(messages: list[dict], system_prompt: str, max_tokens: int) -> str`.
- Formato de mensajes compatible con API Claude en Bedrock (`anthropic_version`, `content` como array).
- Manejo de excepciones con mensajes de error claros.

**Configuración:**
- `settings.BEDROCK_REGION` (ya existe: `us-east-2` en `.env`).
- `settings.BEDROCK_MODEL_ID` (ya existe: `anthropic.claude-sonnet-4-20250514-v1:0`).
- Variable nueva opcional: `AI_AGENT_BEDROCK_MODEL_ID` para permitir modelo distinto del JATS.

---

#### 1.2 Modelos de base de datos: `ChatSession` y `ChatMessage`

**Ubicación:** `backend/app/models/` (archivos nuevos: `chat_session.py` y `chat_message.py`, o un solo `ai_chat.py`).

**ChatSession:**
- `id` (UUID)
- `user_id` (FK a User, nullable para anónimos)
- `anonymous_session_id` (nullable, para anónimos)
- `title` (str, opcional, ej. primera pregunta truncada)
- `created_at`, `updated_at`

**ChatMessage:**
- `id` (UUID)
- `session_id` (FK a ChatSession)
- `role` (user | assistant)
- `content` (texto)
- `created_at`
- Opcional: `attachments` (JSON) para metadata de archivos analizados

**Migraciones:**
- Crear tabla `chat_sessions` y `chat_messages`.
- Actualizar `app/models/__init__.py` para registrar los modelos.

---

#### 1.3 Actualizar `ai.py` router

**Cambios:**
- Eliminar import de OpenAI.
- Inyectar `ai_agent_service` para generar respuestas.
- Mantener `ai_service` para créditos (check, consume).
- Endpoints nuevos:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `POST /ai/chat` | Extender | Aceptar `session_id?`, `message`, `attachment_ids?`. Si no hay `session_id`, crear sesión. Persistir user/assistant messages. |
| `GET /ai/credits` | Sin cambios | Igual que ahora. |
| `GET /ai/sessions` | Nuevo | Lista de `ChatSession` del usuario/anónimo. |
| `GET /ai/sessions/{id}` | Nuevo | Mensajes de una sesión. |
| `POST /ai/sessions` | Nuevo | Crear sesión vacía (Nuevo Chat). |
| `DELETE /ai/sessions/{id}` | Nuevo | Eliminar sesión (opcional). |
| `POST /ai/upload` | Nuevo | Subir archivo (PDF, DOCX, TXT). Almacenar en disco temporal/S3. Devolver `attachment_id` para incluir en `/ai/chat`. |

**Restricción:** Solo modificar el router `ai.py` y archivos del módulo asistente. No tocar convert, pdf-tools, auth, payments.

---

#### 1.4 Sistema de prompts y Smart Links

**Ubicación:** Construcción del system prompt dentro de `ai_agent_service` o en un módulo `ai_agent_prompts.py`.

**Contenido del system prompt:**
- Descripción del asistente (documentos, conversiones, PDF tools).
- Lista de herramientas disponibles (conversiones + PDF tools) extraída de constantes o endpoint interno.
- Formato de URLs internas:
  - Conversión: `/convert?from={source}&to={target}` (ej. `from=pdf&to=docx`).
  - PDF tools: `/pdf-tools?tool={id}` (ej. `tool=unir-pdf`).
  - Otras: `/pricing`, `/dashboard`, `/history`, `/format-manuscript`.
- Instrucción: "Cuando recomiendes una herramienta, incluye el enlace en Markdown: [Texto](url)."

---

#### 1.5 Análisis de documentos (RAG básico)

**Flujo:**
1. Usuario sube archivo vía `POST /ai/upload`.
2. Backend extrae texto (PDF: PyMuPDF/pdfplumber, DOCX: python-docx, TXT: directo).
3. Se guarda el texto extraído asociado al `attachment_id`.
4. En `POST /ai/chat`, si hay `attachment_ids`, el servicio concatena el texto extraído y lo incluye en el contexto del último mensaje del usuario.
5. Claude recibe: "El usuario ha adjuntado el siguiente contenido:\n{texto}\n\nPregunta: {message}".

---

### Fase 2: Frontend – UI del asistente

#### 2.1 Panel lateral de chats (sidebar interno)

**Ubicación:** Dentro del panel `ai-chat-panel` del AIAssistantFAB.

**Componentes:**
- `ChatSessionSidebar.tsx`: lista de sesiones, botón "Nuevo Chat".
- Al hacer clic en una sesión: cargar mensajes desde API.
- Al hacer clic en "Nuevo Chat": crear sesión vacía y limpiar mensajes locales.

---

#### 2.2 Extender API frontend (`api/ai.ts`)

**Funciones nuevas:**
- `getChatSessions(anonymousSessionId?: string)`
- `getChatSession(sessionId, anonymousSessionId?)`
- `createChatSession(anonymousSessionId?)`
- `deleteChatSession(sessionId, anonymousSessionId?)`
- `sendChatMessage(message, sessionId?, attachmentIds?, anonymousSessionId?)`
- `uploadChatAttachment(file: File, anonymousSessionId?)` → `attachment_id`

---

#### 2.3 Estado de sesión activa

- Estado: `activeSessionId: string | null`.
- Al enviar mensaje sin sesión: backend crea sesión y devuelve `session_id`; frontend actualiza `activeSessionId` y refresca lista.
- Al abrir sesión existente: `GET /ai/sessions/{id}`, cargar mensajes en `messages`.

---

#### 2.4 Renderizado Markdown y Smart Links

- Añadir librería: `react-markdown` (o similar) para renderizar respuestas del asistente.
- Los enlaces `[texto](url)` se renderizan como `<a href="/convert?from=pdf&to=docx">` (rutas relativas).
- Usar `Link` de react-router o `href` con base correcta para SPA.

---

#### 2.5 Carga de archivos en el chat

- Botón de adjuntar (clip/paperclip) junto al input.
- Input `type="file"` aceptando PDF, DOCX, TXT.
- Al seleccionar: llamar `uploadChatAttachment`, recibir `attachment_id`.
- Mostrar preview (nombre, icono) debajo del input.
- Incluir `attachmentIds` en `sendChatMessage` al enviar.

---

#### 2.6 Estilos y UX

- Mantener estética actual (premium, fluida).
- Sidebar colapsable en móvil si hace falta.
- Transiciones suaves al cambiar de sesión.

---

### Fase 3: Integración y pruebas

#### 3.1 Desactivar OpenAI en el módulo AI

- Quitar `OPENAI_API_KEY` como dependencia del asistente.
- Mantener `ai_service` (créditos) sin cambios.

---

#### 3.2 Variables de entorno

- `BEDROCK_REGION`, `BEDROCK_MODEL_ID` (ya existen).
- Opcional: `AI_AGENT_BEDROCK_MODEL_ID` si se quiere modelo distinto.
- Verificar que la instancia tenga permisos IAM para Bedrock (`bedrock:InvokeModel`).

---

#### 3.3 Criterios de aceptación (checklist)

| # | Criterio | Verificación |
|---|----------|---------------|
| 1 | El asistente responde con Amazon Bedrock (Claude 3) | Invocar chat y comprobar respuesta. |
| 2 | Crear, ver y alternar entre chats | Sidebar con sesiones, "Nuevo Chat", carga de mensajes. |
| 3 | URLs dinámicas funcionan al clic | Respuesta con `[Unir PDF](/pdf-tools?tool=unir-pdf)` → clic navega. |
| 4 | Análisis de archivos cargados | Subir PDF/DOCX, preguntar sobre contenido → respuesta coherente. |
| 5 | Resto del sistema sin cambios | Conversiones, PDF tools, auth, pagos sin errores. |

---

## Estructura de Archivos Propuesta

```
backend/
  app/
    models/
      chat_session.py      # Nuevo
      chat_message.py      # Nuevo
    services/
      ai_agent_service.py  # Nuevo
      ai_service.py        # Sin cambios (créditos)
    routers/
      ai.py                # Modificar (Bedrock, sesiones, upload)

frontend/
  src/
    components/
      AIAssistantFAB/
        AIAssistantFAB.tsx       # Modificar (sesiones, Markdown, archivos)
        AIAssistantFAB.css      # Modificar (sidebar, adjuntos)
        ChatSessionSidebar.tsx   # Nuevo
    services/
      api/
        ai.ts                  # Extender (sesiones, upload)
    constants/
      aiTools.ts               # Nuevo (opcional: mapa de herramientas para el backend)
```

---

## Estado de Implementación (2025-02-22)

✅ Completado:
- ai_agent_service.py + ai_agent_tools.py (Bedrock, Claude 3, Smart Links)
- Modelos ChatSession y ChatMessage + migrate_chat_sessions.py
- Router ai.py: Bedrock, sesiones (list/get/create), chat con historial, upload
- Frontend: api/ai.ts extendido, ChatSessionSidebar, AIAssistantFAB con Markdown y adjuntos
- react-markdown para enlaces clicables (rutas internas como Link)

---

## Orden de Implementación Sugerido

1. **Backend**
   - 1.1 `ai_agent_service.py` (Bedrock)
   - 1.2 Modelos `ChatSession` y `ChatMessage` + migración
   - 1.3 Extender router `ai.py`: chat con sesiones, system prompt con herramientas
   - 1.4 Endpoints de sesiones (list, get, create)
   - 1.5 Upload y extracción de texto
   - 1.6 Inyección de contexto de archivos en el chat

2. **Frontend**
   - 2.1 Extender `api/ai.ts`
   - 2.2 `ChatSessionSidebar` y estado de sesión activa
   - 2.3 Integrar sidebar en `AIAssistantFAB`
   - 2.4 Renderizado Markdown con `react-markdown`
   - 2.5 Carga y envío de archivos

3. **Validación**
   - Probar cada criterio de aceptación
   - Verificar que conversiones, PDF tools, auth y pagos siguen funcionando

---

## Notas Adicionales

- **Aislamiento:** No modificar `conversion_request_service`, `convert.py`, `pdf_tools`, `auth`, `payments`.
- **Créditos:** El consumo de créditos (ai_service) se mantiene igual; solo cambia el proveedor de IA.
- **Historial de conversiones:** La página `/history` (historial de documentos) no se toca; el historial de chats vive solo en el asistente.
- **AWS:** Usar credenciales y región existentes. La instancia EC2 ya usa IAM; confirmar permisos Bedrock.
