import asyncio
from sqlalchemy import text
from backend.app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # We use a try-except block for ALTER TABLE in case columns already exist
        try:
            await conn.execute(text("ALTER TABLE documents ADD COLUMN initial_content TEXT"))
            print("Column 'initial_content' added to 'documents' table.")
        except Exception:
            print("Column 'initial_content' might already exist or table doesn't exist yet.")

        # Ensure tables exist with all columns
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                original_format VARCHAR(50),
                content BLOB,
                initial_content TEXT,
                owner_id INTEGER REFERENCES users(id),
                is_public BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
    print("Migration finished.")

if __name__ == "__main__":
    asyncio.run(migrate())
