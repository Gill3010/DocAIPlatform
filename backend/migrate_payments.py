
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

async def migrate_payments():
    print("Starting migration: Payments Integration")
    async with engine.begin() as conn:
        
        # 1. Create Payments Table
        print("Creating payments table...")
        if "sqlite" in settings.DATABASE_URL:
             await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider VARCHAR NOT NULL,
                    transaction_id VARCHAR,
                    amount NUMERIC(10, 2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    status VARCHAR DEFAULT 'pending',
                    plan_id VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """))
        else:
            # Postgres
             await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    provider VARCHAR NOT NULL,
                    transaction_id VARCHAR,
                    amount NUMERIC(10, 2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'USD',
                    status VARCHAR DEFAULT 'pending',
                    plan_id VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
        print("✓ Created payments table")

        # 2. Add columns to users table
        columns = [
            ("is_premium", "BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE"),
            ("premium_plan_id", "VARCHAR", "VARCHAR"),
            ("subscription_end_date", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE"),
            ("paypal_payer_id", "VARCHAR", "VARCHAR"),
        ]

        for col_name, sqlite_type, pg_type in columns:
            col_type = sqlite_type if "sqlite" in settings.DATABASE_URL else pg_type
            try:
                # Check column existence (naive check)
                await conn.execute(text(f"SELECT {col_name} FROM users LIMIT 1"))
                print(f"✓ Column {col_name} already exists in users")
            except Exception:
                # If select fails, column likely missing
                try:
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    print(f"✓ Added column {col_name} to users")
                except Exception as e:
                    print(f"⚠ Could not add column {col_name}: {e}")

if __name__ == "__main__":
    # Ensure current directory is in path to find 'app'
    sys.path.insert(0, str(Path(__file__).parent))
    asyncio.run(migrate_payments())
