import pytest
from backend.app.core.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.PROJECT_NAME == "RedThread"
    assert settings.VERSION == "1.0.0"
    assert settings.APP_ENV in ("development", "production", "testing")
    assert settings.MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024
    assert "application/pdf" in settings.ALLOWED_MIME_TYPES
    assert "text/csv" in settings.ALLOWED_MIME_TYPES


def test_database_url_assembly():
    settings = Settings(
        POSTGRES_SERVER="db.example.com",
        POSTGRES_PORT=5432,
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_DB="testdb",
        DATABASE_URL=None,
        SYNC_DATABASE_URL=None,
    )
    assert settings.DATABASE_URL == "postgresql+asyncpg://testuser:testpassword@db.example.com:5432/testdb"
    assert settings.SYNC_DATABASE_URL == "postgresql+psycopg2://testuser:testpassword@db.example.com:5432/testdb"


def test_celery_broker_url_assembly():
    settings = Settings(
        REDIS_URL="redis://redis.internal:6379/1",
        CELERY_BROKER_URL=None,
        CELERY_RESULT_BACKEND=None,
    )
    assert settings.CELERY_BROKER_URL == "redis://redis.internal:6379/1"
    assert settings.CELERY_RESULT_BACKEND == "redis://redis.internal:6379/1"
