import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# A単adir el directorio actual al path para poder importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def migrate():
    print(f"Connecting to {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # 1. Crear tabla organizations
        print("Creating organizations table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        """))
        
        # 2. A単adir organización a la tabla users
        print("Adding organization_id to users table...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id)"))
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("Column organization_id already exists.")
            else:
                print(f"Note: {e}")
        
    print("Migration completed successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
