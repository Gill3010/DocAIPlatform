# README técnico para desarrolladores

Documento orientado a quien va a mantener o extender el código: arquitectura, capas, convenciones y cómo añadir funcionalidad.

---

## Stack y versiones

| Capa | Tecnología | Notas |
|------|------------|--------|
| Backend | Python 3.12, FastAPI | Async (asyncio, aiosqlite) |
| Base de datos | SQLite (SQLAlchemy + aiosqlite) | Ruta fija: `backend/sql_app.db` |
| Frontend | React 19, TypeScript, Vite 7 | Zustand, React Router 7 |
| Tests backend | pytest | `backend/tests/`, `pytest.ini` |
| Tests frontend | Vitest, React Testing Library, jsdom | `frontend/src/**/*.test.{ts,tsx}`, setup en `src/test/setup.ts` |

---

## Estructura del repositorio

```
backend/           # API FastAPI
  app/
    core/         # Config, DB, seguridad, excepciones, logging
    models/       # SQLAlchemy (User, Conversion, Document, etc.)
    routers/      # Endpoints por dominio (auth, convert, pdf_tools, users, ai, admin, documents)
    schemas/      # Pydantic (request/response)
    services/     # Lógica de negocio (ConversionService, UserService, AuthService, etc.)
    utils/        # Convertidores, estrategias PDF, helpers
  tests/          # pytest
  main.py         # App FastAPI, CORS, routers, exception handler

frontend/
  src/
    components/   # UI reutilizable (FileDropZone, ErrorBoundary, etc.)
    pages/        # Rutas (Convert, Dashboard, Admin, etc.)
    hooks/        # useFileSelection, useConversion, useConvertFormats, etc.
    services/
      api/        # Módulos API (request, auth, convert, users, errors, etc.)
      storageService.ts
    stores/       # Zustand (appStore)
    contexts/    # React context (ej. búsqueda)
    constants/   # Constantes (conversiones soportadas)
    types/       # Tipos TypeScript
    test/        # Setup Vitest (jest-dom)
  vite.config.ts # Incluye test (jsdom, setupFiles)
```

---

## Backend: capas y flujo

- **Routers** (`app/routers/`): reciben HTTP, validan con Pydantic/schemas, llaman a **services** o a `get_db`/`get_current_user`. No contienen lógica de negocio pesada.
- **Services** (`app/services/`): lógica de créditos, validaciones, creación de usuarios, conversiones, etc. Reciben `AsyncSession` y modelos.
- **Models** (`app/models/`): SQLAlchemy (User, Conversion, AnonymousSession, Document, AdminAuditLog, etc.).
- **Core**:
  - `config.py`: todas las constantes y configuración (Pydantic Settings desde `.env`). **No** usar valores mágicos en el código; leer de `settings`.
  - `exceptions.py`: jerarquía `AppException` (InvalidCredentials, NotFound, AnonymousLimitReached, etc.). Se mapean a HTTP en `main.py` con un único handler.
  - `security.py`: JWT, `get_current_user`, `get_current_admin_user`, `datetime.now(timezone.utc)` (no `utcnow()`).
  - `database.py`: sesión async, `get_db`.
- **Utils**:
  - `converter.py` + `converters/`: conversión de documentos (por tipo: image, office, pdf_docx, etc.).
  - `pdf_tool_strategies/`: cada herramienta PDF es una **estrategia** que extiende `PDFToolStrategy` (base), implementa `run(work_dir, files, form)` y devuelve `ToolResult`. El router de PDF tools delega en un ejecutor común que aplica créditos, work dir y respuesta.

Las respuestas de error HTTP se devuelven preferiblemente lanzando excepciones de `core.exceptions`; el handler global en `main.py` las convierte en JSON con el `detail` adecuado.

---

## Frontend: capas y flujo

- **Pages**: rutas (React Router). Componen la UI a partir de **components** y **hooks**.
- **Components**: UI reutilizable. Reciben props; no acceden directamente a la API sino mediante hooks o callbacks. Ej.: `FileDropZone`, `ErrorBoundary`.
- **Hooks**: encapsulan estado y llamadas API (ej. `useFileSelection`, `useConversion`, `useConvertFormats`). Las páginas usan estos hooks en lugar de duplicar lógica.
- **Services / API** (`services/api/`):
  - `request.ts`: `apiRequest<T>(endpoint, options)` centralizado; añade token, maneja 401 (logout), lanza `ApiError` con `statusCode` y `detail`.
  - `config.ts`: `API_URL` (desde `VITE_API_URL` o por defecto mismo host:8000).
  - `errors.ts`: `ApiError`, `apiErrorFromResponse`.
  - Módulos por dominio: `auth`, `convert`, `users`, `ai`, `admin`, `documents`, `pdfTools`; cada uno exporta funciones que llaman a `apiRequest` con el endpoint y método adecuados.
- **Storage**: `storageService.ts` para token y sesión anónima (localStorage/sessionStorage). El resto del código no usa `localStorage`/`sessionStorage` directamente.
- **Stores**: Zustand (`appStore`) para estado global (usuario, logout, etc.).
- **ErrorBoundary**: envuelve la app (p. ej. en `App.tsx`) para capturar errores de render y mostrar una UI de fallback en lugar de pantalla blanca.

---

## Tests

- **Backend**: desde la raíz del repo, `cd backend && pytest`. Tests en `backend/tests/` (conftest, test_config, test_auth_service, test_conversion_service, test_main).
- **Frontend**: `cd frontend && npm run test` (watch) o `npm run test:run` (una ejecución). Archivos `*.test.ts` / `*.test.tsx` en `src/`; entorno jsdom; setup en `src/test/setup.ts` (jest-dom). Ejemplos: `useConvertFormats.test.ts`, `FileDropZone.test.tsx`.

---

## Convenciones

- **Backend**: async/await; tipos con type hints; constantes y configuración en `config.py`; excepciones de dominio en `core.exceptions`; no usar `datetime.utcnow()` (usar `datetime.now(timezone.utc)`).
- **Frontend**: TypeScript estricto; llamadas HTTP solo vía `apiRequest` y módulos de `services/api`; token y sesión anónima solo vía `storageService`; componentes presentacionales y lógica en hooks donde tenga sentido.
- **API**: prefijo `/api/v1`; documentación en Swagger (`/api/v1/docs`) y ReDoc (`/api/v1/redoc`). Endpoints documentados con summary, description y responses (códigos de error).

---

## Cómo añadir funcionalidad

### Nuevo endpoint (backend)

1. Definir o reutilizar schemas en `app/schemas/`.
2. Si hay lógica de negocio (créditos, validaciones), añadirla en un **service** en `app/services/` y llamarla desde el router.
3. Añadir la ruta en el router adecuado (`app/routers/`). Si es un nuevo dominio, crear un nuevo router y registrarlo en `main.py` con `app.include_router(..., prefix=f"{settings.API_V1_STR}/...", tags=["..."])`.
4. Documentar en OpenAPI: `summary=`, `description=`, `responses={...}` en el decorator de la ruta.
5. Si aplica, lanzar excepciones de `core.exceptions` para errores de negocio.

### Nueva herramienta PDF (backend)

1. Crear una clase en `app/utils/pdf_tool_strategies/strategies.py` que extienda `PDFToolStrategy` (definida en `base.py`).
2. Implementar `run(self, work_dir: Path, files: Dict[str, bytes], form: Dict[str, Any]) -> ToolResult`. Dentro: validar inputs, llamar a la util existente en `pdf_tools.py` o a librerías (PyMuPDF, etc.), devolver `ToolResult` con `path`/`paths`/`text`, `filename` y `media_type`.
3. Registrar la estrategia en el `REGISTRY` (en el mismo archivo o en `pdf_tool_strategies/__init__.py`).
4. Añadir un endpoint en `app/routers/pdf_tools.py` que lea archivos/form, llame a `_execute_tool("nombre_herramienta", files_dict, form_dict, ...)` y use `PDF_TOOL_RESPONSES` para la documentación OpenAPI.

### Nuevo módulo o llamada API (frontend)

1. Si es un nuevo dominio: crear un archivo en `services/api/` (ej. `miDominio.ts`) que exporte funciones que llamen a `apiRequest<Respuesta>(endpoint, { method, body, ... })`.
2. Reutilizar `apiRequest` y no duplicar lógica de token o manejo de 401/errors; usar `ApiError` y `apiErrorFromResponse` desde `errors.ts`.
3. Si el frontend necesita un nuevo endpoint ya existente en el backend, añadir la función en el módulo API correspondiente y, si aplica, el tipo de respuesta en `types/` o en el mismo módulo.

### Nuevo componente o hook (frontend)

- **Componente**: carpeta bajo `components/NombreComponente/` con `NombreComponente.tsx` y `NombreComponente.css`; props tipadas; tests en `NombreComponente.test.tsx` si es relevante.
- **Hook**: archivo en `hooks/useNombre.ts`; tests en `hooks/useNombre.test.ts` cuando el hook sea fácil de aislar (p. ej. lógica pura o con render de componente si usa RTL).

---

## Documentación API

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

Todos los routers (auth, convert, pdf-tools, users, ai, admin, documents) tienen summary, description y códigos de respuesta documentados.

---

## Referencia rápida de configuración

- Backend: `backend/.env` (SECRET_KEY, DATABASE_URL opcional, LOG_LEVEL, OPENAI_API_KEY, OAuth, SUPERADMIN_EMAILS, etc.). Valores por defecto en `app/core/config.py`.
- Frontend: `frontend/.env` opcional con `VITE_API_URL` (por defecto mismo host, puerto 8000).

Para más detalle de instalación y uso general del producto, ver el [README principal](../README.md) en la raíz del repositorio.
