"""
Añade la columna can_access_admin_panel a la tabla users si no existe.
Ejecutar una vez desde la raíz: python -m backend.migrate_admin_panel
O desde backend: python migrate_admin_panel.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine


async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN can_access_admin_panel BOOLEAN DEFAULT 0")
            )
            print("✓ Column can_access_admin_panel added to users.")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Column can_access_admin_panel already exists.")
            else:
                raise


if __name__ == "__main__":
    asyncio.run(migrate())
