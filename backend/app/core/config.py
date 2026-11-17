import os
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "RedThread"
    VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "redthread"
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "postgres")
        password = data.get("POSTGRES_PASSWORD", "postgres")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "redthread")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "postgres")
        password = data.get("POSTGRES_PASSWORD", "postgres")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "redthread")
        return f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v.strip():
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    # Object Storage (S3 / MinIO)
    S3_ENDPOINT_URL: Optional[str] = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "redthread-documents"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # Security & JWT Sessions
    JWT_SECRET_KEY: str = "redthread-insecure-dev-secret-key-change-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cryptography (Argon2id)
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536  # 64 MB
    ARGON2_PARALLELISM: int = 4

    # AI & Graph Integration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    COGNEE_API_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Ingestion constraints
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "message/rfc822",
        "text/csv",
    ]


settings = Settings()
