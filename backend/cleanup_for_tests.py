"""
Limpieza controlada del entorno para pruebas.
- Conserva SOLO el super admin: admin@docaiplatform.com
- Elimina todos los demás usuarios, conversiones, documentos, sesiones anónimas,
  pdf_tool_uses, admin_audit_log.
- Resetea créditos del super admin (free_conversion_count, ai_message_count) a 0.
- Elimina todos los archivos en storage (uploads, converted, pdf_tools) y avatares.
Ejecutar desde raíz: python backend/cleanup_for_tests.py
"""
import asyncio
import sys
from pathlib import Path

# Run from project root: PYTHONPATH includes .
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from backend.app.core.database import AsyncSessionLocal

# Email del único usuario a conservar
SUPERADMIN_EMAIL = "admin@docaiplatform.com"

# Rutas de almacenamiento (relativas al backend)
BACKEND_DIR = Path(__file__).resolve().parent
STORAGE_UPLOADS = BACKEND_DIR / "storage" / "uploads"
STORAGE_CONVERTED = BACKEND_DIR / "storage" / "converted"
STORAGE_PDF_TOOLS = BACKEND_DIR / "storage" / "pdf_tools"
STATIC_AVATARS = BACKEND_DIR / "static" / "uploads" / "avatars"


async def cleanup_database():
    async with AsyncSessionLocal() as db:
        # 1) Verificar que existe el super admin a conservar
        r = await db.execute(
            text("SELECT id, is_superuser, can_access_admin_panel FROM users WHERE email = :email"),
            {"email": SUPERADMIN_EMAIL},
        )
        row = r.fetchone()
        if not row:
            print(f"⚠ ERROR: No existe el usuario {SUPERADMIN_EMAIL}")
            print("  Créalo antes de ejecutar este script (registro o comando).")
            print("  Luego márcalo como superadmin: python backend/set_superadmin.py " + SUPERADMIN_EMAIL)
            sys.exit(1)

        superadmin_id, is_superuser, can_access_admin = row[0], bool(row[1]), bool(row[2])
        print(f"✓ Super admin a conservar: {SUPERADMIN_EMAIL} (id={superadmin_id})")

        # Asegurar que tenga privilegios de superadmin
        if not is_superuser or not can_access_admin:
            await db.execute(
                text("UPDATE users SET is_superuser = 1, can_access_admin_panel = 1 WHERE id = :id"),
                {"id": superadmin_id},
            )
            print("  → Privilegios de superadmin actualizados.")

        # 2) Eliminar en orden por dependencias
        await db.execute(text("DELETE FROM document_permissions"))
        await db.execute(text("DELETE FROM documents"))
        await db.execute(text("DELETE FROM conversions"))
        await db.execute(text("DELETE FROM pdf_tool_uses"))
        await db.execute(text("DELETE FROM admin_audit_log"))
        await db.execute(text("DELETE FROM anonymous_sessions"))

        # 3) Eliminar todos los usuarios excepto el super admin
        await db.execute(text("DELETE FROM users WHERE id != :id"), {"id": superadmin_id})

        # 4) Resetear créditos del super admin (conversiones e IA) a 0
        await db.execute(
            text("UPDATE users SET free_conversion_count = 0, ai_message_count = 0 WHERE id = :id"),
            {"id": superadmin_id},
        )

        await db.commit()
        print("✓ Base de datos limpiada: document_permissions, documents, conversions,")
        print("  pdf_tool_uses, admin_audit_log, anonymous_sessions eliminados.")
        print("✓ Créditos del super admin (conversiones e IA) reseteados a 0.")
        print(f"✓ Solo permanece el usuario: {SUPERADMIN_EMAIL}")


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
