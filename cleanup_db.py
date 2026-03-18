import asyncio
import os
import sys
from pathlib import Path

# Add backend to path to import app modules
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.append(str(BACKEND_DIR))

from sqlalchemy import delete, select
from app.core.database import AsyncSessionLocal as SessionLocal
from app.models.user import User
from app.models.payment import Payment
from app.models.conversion import Conversion
from app.models.pdf_tool_use import PdfToolUse
from app.models.anonymous_session import AnonymousSession
from app.models.document import Document
from app.models.admin_audit_log import AdminAuditLog
from app.models.manuscript_format import ManuscriptFormat


STORAGE_UPLOADS = BACKEND_DIR / "storage" / "uploads"
STORAGE_CONVERTED = BACKEND_DIR / "storage" / "converted"
STORAGE_FORMATTED = BACKEND_DIR / "storage" / "formatted"

# Also clean the nested backend/backend/storage that exists from old deployment
NESTED_BACKEND_DIR = BACKEND_DIR / "backend"
NESTED_STORAGE_UPLOADS = NESTED_BACKEND_DIR / "storage" / "uploads"
NESTED_STORAGE_CONVERTED = NESTED_BACKEND_DIR / "storage" / "converted"


async def cleanup_database():
    print("🚀 Starting database cleanup...")
    async with SessionLocal() as db:
        try:
            # 1. Get superusers to protect them
            result = await db.execute(select(User).where(User.is_superuser == True))
            superusers = result.scalars().all()
            superuser_ids = [u.id for u in superusers]
            
            print(f"🛡️  Found {len(superusers)} superusers to protect: {[u.email for u in superusers]}")

            # 2. Delete Payments
            print("💰 Deleting all payments...")
            await db.execute(delete(Payment))
            
            # 3. Delete Conversions
            print("🔄 Deleting all conversions...")
            await db.execute(delete(Conversion))
            
            # 4. Delete PDF Tool Uses
            print("📄 Deleting all PDF tool uses...")
            await db.execute(delete(PdfToolUse))

            # 5. Delete Documents
            print("📂 Deleting all documents...")
            await db.execute(delete(Document))

            # 6. Delete Anonymous Sessions
            print("👤 Deleting all anonymous sessions...")
            await db.execute(delete(AnonymousSession))

            # 7. Delete Audit Logs
            print("📝 Deleting all audit logs...")
            await db.execute(delete(AdminAuditLog))

            # 8. Delete Manuscript Formats
            print("📄 Deleting all manuscript format records...")
            await db.execute(delete(ManuscriptFormat))

            # 8. Delete Users (except superadmins)
            print("👥 Deleting users (except superadmins)...")
            await db.execute(delete(User).where(User.id.not_in(superuser_ids)))

            # 9. Reset free counts for superadmins just in case
            for su in superusers:
                su.free_conversion_count = 0
                su.is_premium = False
                su.premium_plan_id = None
                db.add(su)

            await db.commit()
            print("✨ Database cleanup completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error during cleanup: {str(e)}")
            import traceback
            traceback.print_exc()


def cleanup_storage_dirs():
    print("🧹 Cleaning storage directories (uploads, converted)...")
    removed = 0
    dirs_to_clean = [
        STORAGE_UPLOADS, STORAGE_CONVERTED, STORAGE_FORMATTED,
        NESTED_STORAGE_UPLOADS, NESTED_STORAGE_CONVERTED,
    ]
    for dir_path in dirs_to_clean:
        if not dir_path.exists():
            continue
        for entry in list(dir_path.iterdir()):
            if entry.is_file():
                entry.unlink()
                removed += 1
                print(f"  Removed file: {entry.relative_to(BACKEND_DIR)}")
            elif entry.is_dir():
                # Remove all files inside the directory tree
                for f in entry.rglob("*"):
                    if f.is_file():
                        f.unlink()
                        removed += 1
                # Remove directories from deepest to root
                for d in sorted(entry.rglob("*"), key=lambda x: -len(x.parts)):
                    if d.is_dir():
                        d.rmdir()
                entry.rmdir()
                removed += 1
    print(f"✨ Storage cleanup completed. Items removed: {removed}")


def main():
    asyncio.run(cleanup_database())
    cleanup_storage_dirs()


if __name__ == "__main__":
    main()
