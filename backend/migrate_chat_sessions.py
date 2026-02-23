"""
Migration: Create ai_chat_sessions and ai_chat_messages tables for AI Agent.
Uses distinct names to avoid conflict with existing chat_sessions (documents/collab).
Run once from project root: python backend/migrate_chat_sessions.py
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
        if "sqlite" in settings.DATABASE_URL:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_chat_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER,
                    anonymous_session_id VARCHAR(36),
                    title VARCHAR(256),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_chat_messages (
                    id VARCHAR(36) PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_sessions_user_id ON ai_chat_sessions(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_sessions_anonymous_session_id ON ai_chat_sessions(anonymous_session_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_messages_session_id ON ai_chat_messages(session_id)"))
            print("✓ AI chat sessions migration completed (SQLite)")
        else:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_chat_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    anonymous_session_id VARCHAR(36),
                    title VARCHAR(256),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_chat_messages (
                    id VARCHAR(36) PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_sessions_user_id ON ai_chat_sessions(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_sessions_anonymous_session_id ON ai_chat_sessions(anonymous_session_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_chat_messages_session_id ON ai_chat_messages(session_id)"))
            print("✓ AI chat sessions migration completed (PostgreSQL)")


if __name__ == "__main__":
    asyncio.run(migrate())
