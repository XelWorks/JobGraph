from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoApply AI API"
    app_env: str = "development"
    debug: bool = True
    allowed_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobgraph"
    valkey_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    gemini_api_key: str = "mock-key-for-now"
    master_encryption_key: str = "CHANGE_THIS_TO_RANDOM_HEX_32_BYTES"
    api_key: str = "CHANGE_THIS_TO_RANDOM_32_CHAR_STRING"
    log_level: str = "INFO"
    structured_logging: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
