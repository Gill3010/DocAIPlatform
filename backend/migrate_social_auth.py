"""
Migración: añadir soporte para autenticación social (Google, Facebook)

Añade a la tabla users:
- auth_provider (default: 'email')
- provider_user_id (nullable)

Ejecutar desde la raíz del proyecto: python backend/migrate_social_auth.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine
from backend.app.core.config import settings


async def migrate():
    """Añade columnas para auth social a la tabla users existente."""
    print("Ejecutando migración: auth_provider, provider_user_id...")

    async with engine.begin() as conn:
        if "sqlite" in settings.DATABASE_URL:
            # SQLite: ALTER TABLE ADD COLUMN (no soporta IF NOT EXISTS en columnas)
            migrations = [
                ("auth_provider", "ALTER TABLE users ADD COLUMN auth_provider VARCHAR DEFAULT 'email'"),
                ("provider_user_id", "ALTER TABLE users ADD COLUMN provider_user_id VARCHAR"),
            ]
            for col_name, sql in migrations:
                try:
                    await conn.execute(text(sql))
                    print(f"  ✓ Añadida columna: {col_name}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  - Columna {col_name} ya existe, omitiendo")
                    else:
                        raise
        else:
            # PostgreSQL, MySQL, etc.
            migrations = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR DEFAULT 'email'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_user_id VARCHAR",
            ]
            for sql in migrations:
                await conn.execute(text(sql))
                print(f"  ✓ Ejecutado: {sql[:60]}...")

    print("✓ Migración completada.")


if __name__ == "__main__":
    asyncio.run(migrate())
