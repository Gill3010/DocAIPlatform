"""
Migración: añadir avatar_url a la tabla users para foto de perfil.

Ejecutar desde la raíz del proyecto: python backend/migrate_avatar.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine
from backend.app.core.config import settings


async def migrate():
    """Añade columna avatar_url a users."""
    print("Ejecutando migración: avatar_url...")

    async with engine.begin() as conn:
        if "sqlite" in settings.DATABASE_URL:
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
                print("  ✓ Añadida columna: avatar_url")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - Columna avatar_url ya existe, omitiendo")
                else:
                    raise
        else:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR"))
            print("  ✓ Ejecutado: avatar_url")

    print("✓ Migración completada.")


if __name__ == "__main__":
    asyncio.run(migrate())
