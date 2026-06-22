import logging
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

class MinioStorage:
    def __init__(self) -> None:
        # Parse endpoint to remove protocol if present (minio client expects host:port)
        endpoint = settings.minio_endpoint.replace("http://", "").replace("https://", "")
        secure = settings.minio_endpoint.startswith("https://")
        
        self.client = Minio(
            endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password.get_secret_value() if hasattr(settings.minio_password, 'get_secret_value') else settings.minio_password,
            secure=secure,
        )
        self.bucket_name = settings.minio_bucket

    async def bootstrap(self) -> None:
        """Initialize storage by ensuring the default bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Creating MinIO bucket: {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
            else:
                logger.info(f"MinIO bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to bootstrap MinIO: {e}")
            raise

storage = MinioStorage()
