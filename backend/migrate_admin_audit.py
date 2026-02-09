"""
Crea la tabla admin_audit_log.
Ejecutar una vez: python backend/migrate_admin_audit.py (con venv activado y PYTHONPATH)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.core.database import engine


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                action VARCHAR(64) NOT NULL,
                resource_type VARCHAR(32) NOT NULL,
                resource_id VARCHAR(64),
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_log_admin_user_id ON admin_audit_log (admin_user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_log_action ON admin_audit_log (action)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_admin_audit_log_created_at ON admin_audit_log (created_at)"))
    print("✓ Table admin_audit_log created.")


if __name__ == "__main__":
    asyncio.run(migrate())
