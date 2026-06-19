import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings
from app.infrastructure.logging.logger import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    @fastapi_app.get("/health", status_code=200)
    async def health_check() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"status": "healthy"}

    return fastapi_app

app = create_app()
