import asyncio
from backend.app.core.database import engine, Base
from backend.app.models.user import User

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database Initialized Successfully")

if __name__ == "__main__":
    asyncio.run(init_db())
