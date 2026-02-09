"""
Marca un usuario existente como superadmin por email.
Uso: python set_superadmin.py <email>
Ejemplo: python set_superadmin.py admin@docai.com
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User
from sqlalchemy import select


async def set_superadmin(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {email}")
            return
        user.is_superuser = True
        user.can_access_admin_panel = True
        await db.commit()
        print(f"✓ {email} is now superadmin and can access the admin panel.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_superadmin.py <email>")
        sys.exit(1)
    asyncio.run(set_superadmin(sys.argv[1].strip()))
