from pydantic_settings import BaseSettings
import os
from pathlib import Path

# Get the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Document AI"
    API_V1_STR: str = "/api/v1"
    
    # Database: ruta absoluta a backend/sql_app.db para que siempre sea la misma
    _db_path = BACKEND_DIR / "sql_app.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_db_path}")
    
    # Límites freemium
    FREE_TIER_CONVERSIONS_LIMIT: int = 5  # Total para usuarios registrados
    ANONYMOUS_CONVERSIONS_LIMIT: int = 3  # Límite para usuarios anónimos
    MAX_FILE_SIZE_MB: int = 10  # Tamaño máximo de archivo en MB
    
    # Límites de AI Assistant (comparte pool con conversiones)
    FREE_TIER_AI_CREDITS: int = 5  # Mismo pool que conversiones para usuarios registrados
    ANONYMOUS_AI_LIMIT: int = 3  # Mismo límite que conversiones para anónimos

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"  # Origen del frontend para redirect_uri

    # Facebook (Meta) OAuth
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    # Cloudflare Turnstile (CAPTCHA)
    TURNSTILE_SECRET_KEY: str = ""

    # Admin: emails que siempre se consideran superadmin (separados por coma)
    SUPERADMIN_EMAILS: str = ""

    # Logging: nivel por defecto (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"
    DATABASE_ECHO: bool = False  # True para ver SQL en consola (desarrollo)

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'

settings = Settings()

# Set OpenAI API key as environment variable for the openai library
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
