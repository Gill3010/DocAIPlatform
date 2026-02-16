from pathlib import Path
from typing import List
import httpx

from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging_config import setup_logging, get_logger
from app.routers import auth, convert, pdf_tools, users, ai, admin, documents, payments, manuscript

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI): 
    setup_logging(settings.LOG_LEVEL)
    logger.info("Application starting")
    if settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.warning(
            "SECRET_KEY is the default value. Set SECRET_KEY in .env for production."
        )
    yield
    logger.info("Application shutdown")


OPENAPI_TAGS = [
    {"name": "auth", "description": "Registro, login (email/contraseña, Google, Facebook) y vinculación de sesión anónima."},
    {"name": "convert", "description": "Subida y conversión de documentos (usuarios autenticados y anónimos), historial y descarga."},
    {"name": "pdf-tools", "description": "Herramientas PDF: unir, dividir, rotar, comprimir, etc. Usan el mismo pool de créditos que las conversiones."},
    {"name": "users", "description": "Perfil de usuario, actualización y gestión de cuenta."},
    {"name": "ai", "description": "Asistente IA para documentos. Consume créditos del mismo pool que conversiones."},
    {"name": "admin", "description": "Panel de administración (solo superadmin)."},
    {"name": "documents", "description": "Documentos del usuario y colaboración."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API del backend para **conversión de documentos** y **asistente IA**. "
        "Autenticación JWT; usuarios registrados y anónimos con límites de créditos (freemium). "
        "Endpoints principales: `/auth` (login/registro), `/convert` (subir y convertir), `/pdf-tools` (herramientas PDF)."
    ),
    version="0.1.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)


def _cors_headers_for_request(request: Request) -> dict:
    """Build CORS headers from request Origin so 500/error responses are not blocked by browser."""
    origin = request.headers.get("origin", "").strip()
    if not origin:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
        "Access-Control-Allow-Headers": "*",
    }


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    if exc.status_code >= 500:
        logger.error("AppException %s: %s", exc.status_code, exc.detail)
    elif exc.status_code >= 400:
        logger.debug("AppException %s: %s", exc.status_code, exc.detail)
    headers = dict(_cors_headers_for_request(request)) if request else {}
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Ensure 500 responses include CORS headers so the browser shows the real error, not CORS."""
    logger.exception("Unhandled exception: %s", exc)
    headers = _cors_headers_for_request(request)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


# CORS configuration: mismos orígenes que el frontend (localhost + IP + dominio)
import os
_cors_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:8000",
    "https://docaiplatform.com",
    "https://www.docaiplatform.com",
    "http://docaiplatform.com",
    "http://www.docaiplatform.com",
]
# Añadir IP pública si está definida (p. ej. en EC2)
_public_host = os.environ.get("PUBLIC_HOST", "18.119.238.33").strip()
if _public_host:
    _cors_origins.extend([
        f"http://{_public_host}:5173",
        f"http://{_public_host}:5174",
        f"http://{_public_host}:8000",
    ])
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|[\d.]+|(www\.)?docaiplatform\.com)(:\d+)?/?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Credits-Remaining"],
)

# WebSocket proxy - use /ws/collab/ to avoid conflict with SPA route /collab/:id
@app.websocket("/ws/collab/{doc_name:path}")
async def websocket_proxy(websocket: WebSocket, doc_name: str):
    """
    Proxy WebSocket connections to the collaboration server
    """
    await websocket.accept()
    collab_url = f"ws://localhost:3001/{doc_name}"
    token = websocket.query_params.get('token')
    if token:
        collab_url += f"?token={token}"
    try:
        import websockets
        async with websockets.connect(collab_url) as collab_ws:
            async def forward_to_collab():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await collab_ws.send(data)
                except WebSocketDisconnect:
                    pass

            async def forward_to_client():
                try:
                    async for message in collab_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except Exception:
                    pass

            import asyncio
            await asyncio.gather(forward_to_collab(), forward_to_client())
    except Exception as e:
        logger.warning("WebSocket proxy error: %s", e)
    finally:
        await websocket.close()

# API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(convert.router, prefix=f"{settings.API_V1_STR}/convert", tags=["convert"])
app.include_router(pdf_tools.router, prefix=f"{settings.API_V1_STR}/pdf-tools", tags=["pdf-tools"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(manuscript.router, prefix=f"{settings.API_V1_STR}/manuscript", tags=["manuscript"])

# Root static files location
static_root = Path(__file__).resolve().parent / "static"
static_root.mkdir(parents=True, exist_ok=True)
(static_root / "uploads" / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

@app.get(
    "/health",
    summary="Health check",
    description="Comprueba que el backend está en marcha. Devuelve `status: healthy`.",
    responses={200: {"description": "Servicio disponible"}},
)
async def health_check():
    return {"status": "healthy"}

# Frontend serving logic
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

# Asset serving (priority)
assets_dir = frontend_dist / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Catch-all for SPA and other static files
@app.get("/{rest_of_path:path}")
async def serve_frontend(rest_of_path: str):
    # Skip API calls
    if rest_of_path.startswith("api/") or rest_of_path == "health":
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    # Check if a specific file exists in the root of dist
    file_path = frontend_dist / rest_of_path
    if rest_of_path and file_path.is_file():
        return FileResponse(str(file_path))
    
    # Default to index.html for SPA (including the root path)
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return JSONResponse(status_code=404, content={"error": "Frontend not found"})
