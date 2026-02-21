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
    
    # Formatos Premium (requieren plan Básico o superior)
    PREMIUM_FORMATS: list[str] = ["xml", "dwg", "dxf"]

    # Mejoras de conversión (sin costo)
    USE_OCR_FOR_SCANNED_PDF: bool = True   # OCR para PDF escaneados
    USE_CAMELOT_FALLBACK: bool = True      # Fallback camelot en PDF→Excel

    # Word-to-JATS Ensemble (conversión avanzada docx→xml para OJS)
    USE_JATS_ENSEMBLE: bool = False        # True = usar flujo docx→xml (Bedrock o local)
    GROBID_URL: str = ""                    # URL de GROBID (ej. http://localhost:8070)
    USE_BEDROCK_FOR_JATS: bool = False      # True = intentar Bedrock primero; fallback a local si falla
    BEDROCK_REGION: str = "us-east-1"       # Región para Bedrock (Claude; distinta de ECS si aplica)
    BEDROCK_MODEL_ID: str = "anthropic.claude-sonnet-4-20250514-v1:0"  # Claude Sonnet 4 (disponible en us-east-2)

    # ECS Fargate converter (nuevo sistema)
    USE_ECS_CONVERTER: bool = True  # True = usar ECS; False = convertir local
    AWS_REGION: str = "us-east-2"
    AWS_ACCOUNT_ID: str = "766092484543"
    ECS_CLUSTER_NAME: str = "document-converter-cluster"
    ECS_TASK_FAMILY: str = "document-converter-task"
    ECS_INPUT_BUCKET: str = ""  # Vacío = docai-converter-input-{ACCOUNT_ID}
    ECS_OUTPUT_BUCKET: str = ""
    ECS_SUBNET_ID: str = "subnet-0c38f7efc1eabdb37"
    ECS_SECURITY_GROUP_ID: str = "sg-025ec46598dcb44ed"

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 días
    
    # OpenAI
    OPENAI_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"  # Origen del frontend para redirect_uri

    # Facebook (Meta) OAuth
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    # Email transaccional (verificación, recuperación contraseña)
    # Resend (prioridad 1 si RESEND_API_KEY está definido)
    RESEND_API_KEY: str = ""  # re_xxxx desde dashboard.resend.com
    # Amazon SES (prioridad 2, fallback cuando Resend no está configurado)
    SES_FROM_EMAIL: str = ""  # Remitente compartido (ej. noreply@docaiplatform.com); debe estar verificado en el proveedor activo
    SES_ENABLED: bool = False  # True cuando SES está configurado
    AWS_SES_REGION: str = "us-east-1"  # Región donde verificaste la identidad en SES

    # Cloudflare Turnstile (CAPTCHA)
    TURNSTILE_SECRET_KEY: str = ""

    # Payments - PayPal
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: str = "sandbox"  # 'sandbox' or 'live'

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
