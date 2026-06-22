import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.storage.minio import MinioStorage

@pytest.mark.asyncio
async def test_minio_bootstrap_creates_bucket_if_missing():
    """Verify that bootstrap creates a bucket if it does not exist."""
    with patch("app.infrastructure.storage.minio.Minio") as MockMinio:
        mock_client = MockMinio.return_value
        mock_client.bucket_exists.return_value = False
        
        storage = MinioStorage()
        await storage.bootstrap()
        
        mock_client.bucket_exists.assert_called_once_with(storage.bucket_name)
        mock_client.make_bucket.assert_called_once_with(storage.bucket_name)

@pytest.mark.asyncio
async def test_minio_bootstrap_skips_if_bucket_exists():
    """Verify that bootstrap skips creation if bucket already exists."""
    with patch("app.infrastructure.storage.minio.Minio") as MockMinio:
        mock_client = MockMinio.return_value
        mock_client.bucket_exists.return_value = True
        
        storage = MinioStorage()
        await storage.bootstrap()
        
        mock_client.bucket_exists.assert_called_once_with(storage.bucket_name)
        mock_client.make_bucket.assert_not_called()
