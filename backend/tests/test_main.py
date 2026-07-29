from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from fastapi.testclient import TestClient


def test_health_check_success():
    """Verify that the health check endpoint returns 200 and healthy status when connections work."""
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__.return_value = mock_conn

    with patch("app.main.engine", mock_engine), \
         patch("app.main.storage") as mock_storage, \
         TestClient(app) as client:

        mock_storage.client.bucket_exists.return_value = True
        mock_storage.bucket_name = "jobgraph"

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "database": "healthy",
            "storage": "healthy"
        }

def test_health_check_database_failure():
    """Verify health check correctly reports unhealthy database."""
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("DB Connection Refused")

    with patch("app.main.engine", mock_engine), \
         patch("app.main.storage") as mock_storage, \
         TestClient(app) as client:

        mock_storage.client.bucket_exists.return_value = True
        mock_storage.bucket_name = "jobgraph"

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "unhealthy",
            "database": "unhealthy",
            "storage": "healthy"
        }

def test_health_check_storage_failure():
    """Verify health check correctly reports unhealthy storage."""
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__.return_value = mock_conn

    with patch("app.main.engine", mock_engine), \
         patch("app.main.storage") as mock_storage, \
         TestClient(app) as client:

        mock_storage.client.bucket_exists.side_effect = Exception("S3 bucket not found")
        mock_storage.bucket_name = "jobgraph"

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "unhealthy",
            "database": "healthy",
            "storage": "unhealthy"
        }

def test_settings_loaded():
    """Verify that backend configuration settings are accessible and initialized."""
    from app.core.config import settings
    assert settings.app_name == "AutoApply AI API"
    assert settings.app_env in ["development", "testing", "production"]
    assert settings.allowed_origins is not None

def test_setup_logging_non_structured():
    """Verify standard (non-JSON) logging pathway works without errors."""
    from app.core.config import settings
    from app.infrastructure.logging.logger import setup_logging

    original = settings.structured_logging
    try:
        settings.structured_logging = False
        setup_logging()
    finally:
        settings.structured_logging = original
