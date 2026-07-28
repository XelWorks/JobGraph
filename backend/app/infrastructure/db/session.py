import logging
import sys
from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""
    pass

# Create async engine
# Note: settings.database_url should be in the format: postgresql+asyncpg://user:pass@host:port/db
# For testing (detected via pytest in sys.modules), use NullPool to avoid "Future attached to a different loop" errors
poolclass = NullPool if "pytest" in sys.modules else None

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
    poolclass=poolclass,
)

# Create session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for async database sessions."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
