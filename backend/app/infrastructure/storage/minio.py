import logging

from app.core.config import settings
from minio import Minio
from minio.error import S3Error

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

    def put_object(self, object_name: str, data, length: int, content_type: str = "application/octet-stream") -> None:
        """Upload an object/file to the default MinIO bucket."""
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                data,
                length,
                content_type=content_type,
            )
        except S3Error as e:
            logger.error(f"Failed to upload object {object_name} to MinIO: {e}")
            raise

    def get_presigned_url(self, object_name: str) -> str:
        """Generate a secure pre-signed GET URL for an object, valid for 15 minutes."""
        from datetime import timedelta
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(minutes=15)
            )
        except S3Error as e:
            logger.error(f"Failed to generate pre-signed URL for {object_name}: {e}")
            raise

storage = MinioStorage()
