from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.routers import auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Document Conversion & AI Agent",
    version="0.1.0",
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite Frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "SaaS Document AI API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
