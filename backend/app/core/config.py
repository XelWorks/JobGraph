from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import secrets


class Settings(BaseSettings):
    app_name: str = "AutoApply AI API"
    app_env: str = "development"
    debug: bool = True
    allowed_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    valkey_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_user: str = "minioadmin"
    minio_password: str = os.environ.get("MINIO_PASSWORD", "CHANGE_THIS_TO_STRONG_PASSWORD")
    minio_bucket: str = "jobgraph"
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "mock-key-for-now")
    gemini_model: str = "gemini-1.5-flash"
    master_encryption_key: str = os.environ.get("MASTER_ENCRYPTION_KEY", secrets.token_hex(32))
    jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY", secrets.token_hex(32))
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    api_key: str = os.environ.get("API_KEY", secrets.token_urlsafe(32))
    log_level: str = "INFO"
    structured_logging: bool = True
    
    # Autonomous mode settings
    autonomous_mode_enabled: bool = True
    max_applications_per_day: int = 50
    application_interval_seconds: int = 300  # 5 minutes between applications
    job_discovery_interval_seconds: int = 1800  # 30 minutes between job scans
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 60
    rate_limit_delay_seconds: int = 30  # Delay between portal requests
    session_refresh_interval_hours: int = 12
    daily_report_enabled: bool = True
    daily_report_hour: int = 8  # 8 AM UTC
    
    # Rate limiting per portal
    linkedin_rate_limit_seconds: int = 60
    naukri_rate_limit_seconds: int = 60
    glassdoor_rate_limit_seconds: int = 60
    greenhouse_rate_limit_seconds: int = 30
    lever_rate_limit_seconds: int = 30
    
    # Account creation settings
    auto_create_accounts: bool = True
    default_password_length: int = 16

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
