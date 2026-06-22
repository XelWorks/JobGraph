import asyncio
from sqlalchemy import text
from app.infrastructure.db.session import engine
from minio import Minio
from app.core.config import settings

async def check():
    print("Checking DB...")
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            print(f"DB Result: {res.scalar()}")
    except Exception as e:
        print(f"DB Error: {e}")

    print("Checking MinIO...")
    try:
        endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
        client = Minio(endpoint, access_key=settings.minio_user, secret_key=settings.minio_password, secure=False)
        buckets = client.list_buckets()
        print(f"MinIO Buckets: {len(buckets)}")
    except Exception as e:
        print(f"MinIO Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
