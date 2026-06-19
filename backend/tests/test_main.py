import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    """Verify that the health check endpoint returns 200 and indicates healthy status inside lifespan."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

def test_settings_loaded():
    """Verify that backend configuration settings are accessible and initialized."""
    from app.core.config import settings
    assert settings.app_name == "AutoApply AI API"
    assert settings.app_env in ["development", "testing", "production"]
    assert settings.allowed_origins is not None

def test_setup_logging_non_structured():
    """Verify standard (non-JSON) logging pathway works without errors."""
    from app.infrastructure.logging.logger import setup_logging
    from app.core.config import settings
    
    original = settings.structured_logging
    try:
        settings.structured_logging = False
        setup_logging()
    finally:
        settings.structured_logging = original
