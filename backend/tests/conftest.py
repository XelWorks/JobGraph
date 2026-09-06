import asyncio
import os

import pytest
from minio import Minio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def _db_available() -> bool:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:jobgraph_dev_password@localhost:5432/jobgraph",
    )
    try:
        engine = create_async_engine(db_url, future=True)

        async def _probe() -> None:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        asyncio.run(_probe())
        return True
    except Exception:
        return False


def _minio_available() -> bool:
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000").replace("http://", "").replace("https://", "")
    access_key = os.getenv("MINIO_USER", "minioadmin")
    secret_key = os.getenv("MINIO_PASSWORD", "minioadmin")
    try:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        client.bucket_exists("jobgraph")
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if os.getenv("JOBGRAPH_RUN_INFRA_TESTS") == "1":
        return

    infra_missing = not _db_available() or not _minio_available()
    skip_infra = pytest.mark.skip(
        reason="integration tests require local Postgres/MinIO services; start Docker services or set JOBGRAPH_RUN_INFRA_TESTS=1"
    )

    for item in items:
        path = str(item.fspath)
        if "/integration/" in path or "test_persistence.py" in path:
            if infra_missing:
                item.add_marker(skip_infra)
