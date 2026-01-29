"""
Script to update database schema with new Conversion table
Run this after adding new models
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.database import engine, Base
from backend.app.models import User, Conversion

async def update_database():
    """Create new tables"""
    print("Creating new tables...")
    async with engine.begin() as conn:
        # This will create only tables that don't exist yet
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables updated successfully!")

if __name__ == "__main__":
    asyncio.run(update_database())
