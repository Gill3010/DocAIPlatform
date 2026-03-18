"""
Migration: Create manuscript_formats table for Manuscript Formatter (Beta) history.
Run once from project root: python backend/migrate_manuscript_format.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine
from backend.app.core.config import settings


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS manuscript_formats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original_filename VARCHAR NOT NULL,
                file_size FLOAT NOT NULL,
                output_file_path VARCHAR,
                status VARCHAR DEFAULT 'completed',
                error_message VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_manuscript_formats_user_id ON manuscript_formats(user_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_manuscript_formats_created_at ON manuscript_formats(created_at)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_manuscript_formats_status ON manuscript_formats(status)"
        ))
        print("✓ manuscript_formats migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
