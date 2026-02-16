import asyncio
import os
import sys

# Añadir el path del backend para importar los módulos necesarios
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import engine
from sqlalchemy import text

async def update_db_schema():
    print("Actualizando esquema de base de datos...")
    async with engine.begin() as conn:
        try:
            # Intentar añadir la columna can_view_payments
            await conn.execute(text("ALTER TABLE users ADD COLUMN can_view_payments BOOLEAN DEFAULT 0"))
            print("Columna 'can_view_payments' añadida con éxito.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("La columna 'can_view_payments' ya existe.")
            else:
                print(f"Error al añadir la columna: {e}")

if __name__ == "__main__":
    asyncio.run(update_db_schema())
