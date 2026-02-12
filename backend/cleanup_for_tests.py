"""
Limpieza controlada del entorno para pruebas.
- Elimina todos los usuarios excepto superadministradores (is_superuser=True).
- Elimina todas las conversiones, documentos, sesiones anónimas, pdf_tool_uses y audit log.
- Elimina todos los archivos en storage (uploads, converted, pdf_tools) y avatares.
No modifica lógica ni configuraciones. Ejecutar desde raíz: python backend/cleanup_for_tests.py
"""
import asyncio
import sys
from pathlib import Path

# Run from project root: PYTHONPATH includes .
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal


# Rutas de almacenamiento (relativas al backend)
BACKEND_DIR = Path(__file__).resolve().parent
STORAGE_UPLOADS = BACKEND_DIR / "storage" / "uploads"
STORAGE_CONVERTED = BACKEND_DIR / "storage" / "converted"
STORAGE_PDF_TOOLS = BACKEND_DIR / "storage" / "pdf_tools"
STATIC_AVATARS = BACKEND_DIR / "static" / "uploads" / "avatars"


async def cleanup_database():
    async with AsyncSessionLocal() as db:
        # 1) Superadministradores a conservar (solo lectura con SQL)
        r = await db.execute(text("SELECT id FROM users WHERE is_superuser = 1"))
        superadmin_ids = [row[0] for row in r.fetchall()]
        if not superadmin_ids:
            print("⚠ No hay ningún usuario con is_superuser=True. No se eliminará ningún usuario.")
            print("  Para tener un superadmin: python backend/set_superadmin.py <email>")
        else:
            print(f"✓ Superadministradores a conservar: {superadmin_ids}")

        # 2) Eliminar en orden por dependencias
        await db.execute(text("DELETE FROM document_permissions"))
        await db.execute(text("DELETE FROM documents"))
        await db.execute(text("DELETE FROM conversions"))
        await db.execute(text("DELETE FROM pdf_tool_uses"))
        await db.execute(text("DELETE FROM admin_audit_log"))
        await db.execute(text("DELETE FROM anonymous_sessions"))

        if superadmin_ids:
            placeholders = ",".join(str(i) for i in superadmin_ids)
            await db.execute(text(f"DELETE FROM users WHERE id NOT IN ({placeholders})"))

        await db.commit()
        print("✓ Base de datos: document_permissions, documents, conversions, pdf_tool_uses, admin_audit_log, anonymous_sessions limpiados.")
        print("✓ Usuarios no superadministrador eliminados.")


def cleanup_storage_dirs():
    """Elimina todo el contenido de los directorios de almacenamiento, manteniendo las carpetas."""
    removed = 0
    for dir_path in (STORAGE_UPLOADS, STORAGE_CONVERTED, STORAGE_PDF_TOOLS, STATIC_AVATARS):
        if not dir_path.exists():
            continue
        for f in list(dir_path.iterdir()):
            if f.is_file():
                f.unlink()
                removed += 1
                print(f"  Eliminado: {f.relative_to(BACKEND_DIR)}")
            elif f.is_dir():
                for f2 in f.rglob("*"):
                    if f2.is_file():
                        f2.unlink()
                        removed += 1
                for d in sorted(f.rglob("*"), key=lambda x: -len(x.parts)):
                    if d.is_dir():
                        d.rmdir()
                f.rmdir()
                removed += 1
    print(f"✓ Archivos/carpetas de almacenamiento eliminados: {removed}")


def main():
    print("=== Limpieza para pruebas ===\n")
    asyncio.run(cleanup_database())
    print("\n--- Limpieza de archivos en disco ---")
    cleanup_storage_dirs()
    print("\n=== Limpieza completada. Sistema listo para pruebas. ===")


if __name__ == "__main__":
    main()
