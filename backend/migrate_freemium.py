"""
Migration: Add anonymous conversion support (freemium flow)
- Creates anonymous_sessions table
- Adds anonymous_session_id to conversions
- Makes user_id nullable in conversions
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
        # Check if using SQLite
        if "sqlite" in settings.DATABASE_URL:
            # Create anonymous_sessions table (if not exists)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS anonymous_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    conversions_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Add anonymous_session_id to conversions (ignore if exists)
            try:
                await conn.execute(text(
                    "ALTER TABLE conversions ADD COLUMN anonymous_session_id VARCHAR(36)"
                ))
            except Exception as e:
                if "duplicate column" not in str(e).lower():
                    raise
            # SQLite allows NULL in user_id by default for FK columns
            print("✓ SQLite migration completed")
        else:
            # PostgreSQL / other
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS anonymous_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    conversions_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            try:
                await conn.execute(text(
                    "ALTER TABLE conversions ADD COLUMN anonymous_session_id VARCHAR(36)"
                ))
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise
            await conn.execute(text(
                "ALTER TABLE conversions ALTER COLUMN user_id DROP NOT NULL"
            ))
            print("✓ PostgreSQL migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
