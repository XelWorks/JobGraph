import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import api_router
from app.core.config import settings
from app.infrastructure.db.session import engine
from app.infrastructure.logging.logger import setup_logging
from app.infrastructure.storage.minio import storage

logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI application lifespan manager for startup and shutdown events."""
    # 1. Setup logging on startup
    setup_logging()
    logger.info(
        "app_startup",
        extra={
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "allowed_origins": settings.allowed_origins,
        }
    )

    # 2. Bootstrap infrastructure & create tables
    try:
        # Trigger import of domain models so SQLAlchemy registers them in Base.metadata
        from app.domain.auth import User  # noqa
        from app.domain.profile import UserProfile, Skill, Experience  # noqa
        from app.domain.job import JobPosting, MatchScore, Application  # noqa
        from app.domain.vault import SessionVault  # noqa
        from app.infrastructure.db.session import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("""
                DO $$
                BEGIN
                    ALTER TABLE IF EXISTS session_vault
                        ALTER COLUMN last_verified_at TYPE TIMESTAMPTZ USING last_verified_at AT TIME ZONE 'UTC',
                        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
                        ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
                EXCEPTION WHEN undefined_column THEN
                    NULL;
                END $$;
            """))

        await storage.bootstrap()
    except Exception as e:
        logger.error(f"infrastructure_bootstrap_failed: {e}")
        # In production, we might want to fail fast here depending on criticality

    yield
    # Cleanup on shutdown if needed
    logger.info("app_shutdown")

def create_app() -> FastAPI:
    """FastAPI application factory."""
    fastapi_app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # 2. Configure CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Register endpoints
    fastapi_app.include_router(api_router, prefix="/api/v1")

    @fastapi_app.get("/health", status_code=200)
    async def health_check() -> dict[str, str]:
        """Verify dynamic database and storage availability."""
        db_status = "healthy"
        storage_status = "healthy"

        # Check database connection
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"health_check_db_failed: {e}")
            db_status = "unhealthy"

        # Check storage connection
        try:
            # minio is synchronous, run in threadpool
            exists = await asyncio.to_thread(
                storage.client.bucket_exists, storage.bucket_name
            )
            if not exists:
                storage_status = "unhealthy"
        except Exception as e:
            logger.error(f"health_check_storage_failed: {e}")
            storage_status = "unhealthy"

        overall_status = "healthy" if db_status == "healthy" and storage_status == "healthy" else "unhealthy"

        return {
            "status": overall_status,
            "database": db_status,
            "storage": storage_status,
        }

    return fastapi_app

app = create_app()
