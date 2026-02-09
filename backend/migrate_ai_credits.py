"""
Migración: añadir ai_message_count a la tabla users (créditos del Asistente IA separados).

Ejecutar desde la raíz del proyecto: python backend/migrate_ai_credits.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine
from backend.app.core.config import settings


async def migrate():
    """Añade columna ai_message_count a users."""
    print("Ejecutando migración: ai_message_count...")

    async with engine.begin() as conn:
        if "sqlite" in settings.DATABASE_URL:
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN ai_message_count INTEGER DEFAULT 0"))
                print("  ✓ Añadida columna: ai_message_count")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - Columna ai_message_count ya existe, omitiendo")
                else:
                    raise
        else:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_message_count INTEGER DEFAULT 0"))
            print("  ✓ Ejecutado: ai_message_count")

    print("✓ Migración completada.")


if __name__ == "__main__":
    asyncio.run(migrate())
