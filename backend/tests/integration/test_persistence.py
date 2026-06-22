import pytest
from sqlalchemy import text
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.storage.minio import storage

@pytest.mark.asyncio
async def test_postgresql_connection():
    """Verify PostgreSQL connection using a simple SELECT 1 query."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")

@pytest.mark.asyncio
async def test_minio_connection():
    """Verify MinIO connection by checking bucket existence."""
    try:
        # storage.bootstrap() is called in app lifespan, 
        # but for testing we can call it directly or just check exists
        exists = storage.client.bucket_exists(storage.bucket_name)
        # If it doesn't exist, try to create it to verify write permission
        if not exists:
            storage.client.make_bucket(storage.bucket_name)
            assert storage.client.bucket_exists(storage.bucket_name)
        else:
            assert True
    except Exception as e:
        pytest.fail(f"MinIO connection failed: {e}")
