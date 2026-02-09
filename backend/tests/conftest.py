"""
Pytest fixtures: in-memory SQLite DB and async session for service tests.
"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app.core.database import Base
from backend.app.models import User, Conversion, AnonymousSession, PdfToolUse, Document, DocumentPermission, AdminAuditLog  # noqa: F401 - register models with Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
AsyncSessionTest = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionTest() as session:
        yield session
        await session.rollback()
