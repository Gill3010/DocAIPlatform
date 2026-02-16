
import asyncio
from sqlalchemy.future import select
from app.core.database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

async def check_user():
    async with AsyncSession(engine) as db:
        result = await db.execute(select(User).where(User.email == 'innovaproyectos507@gmail.com'))
        user = result.scalars().first()
        if user:
            print(f"STATUS_CHECK: email={user.email}, is_premium={user.is_premium}, plan={user.premium_plan_id}")
        else:
            print("STATUS_CHECK: User not found")

if __name__ == "__main__":
    asyncio.run(check_user())
