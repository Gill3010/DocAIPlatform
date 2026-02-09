"""
Añade índices a conversions y pdf_tool_uses para listados y filtros.
Ejecutar una vez: python backend/migrate_indexes.py (con venv y PYTHONPATH desde raíz del proyecto).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine


async def migrate():
    async with engine.begin() as conn:
        # conversions: user_id, created_at, status (para historial y admin)
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversions_user_id ON conversions (user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversions_created_at ON conversions (created_at)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversions_status ON conversions (status)"))
        # pdf_tool_uses: user_id, tool_name, created_at
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pdf_tool_uses_user_id ON pdf_tool_uses (user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pdf_tool_uses_tool_name ON pdf_tool_uses (tool_name)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pdf_tool_uses_created_at ON pdf_tool_uses (created_at)"))
    print("✓ Indexes on conversions and pdf_tool_uses created (or already exist).")


if __name__ == "__main__":
    asyncio.run(migrate())
