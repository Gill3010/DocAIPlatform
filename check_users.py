import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User))
        users = res.scalars().all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"- ID: {u.id}, Email: {u.email}, Superuser: {u.is_superuser}")

if __name__ == "__main__":
    asyncio.run(check())
