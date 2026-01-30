import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_user():
    async with AsyncSessionLocal() as db:
        # Create new user
        hashed_password = get_password_hash('Admin123!')
        new_user = User(
            email='admin@docai.com',
            full_name='Administrador DocAI',
            hashed_password=hashed_password,
            is_active=True,
            free_conversion_count=0
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(f'✅ Usuario creado exitosamente:')
        print(f'   Email: {new_user.email}')
        print(f'   Nombre: {new_user.full_name}')
        print(f'   Contraseña: Admin123!')
        print(f'   Créditos usados: {new_user.free_conversion_count}/10')
        print(f'   Créditos disponibles: {10 - new_user.free_conversion_count}')

if __name__ == "__main__":
    asyncio.run(create_user())
