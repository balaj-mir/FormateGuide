"""
FormatGuard Configuration — All settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/formatguard"

    # Redis (Celery broker + cache)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Supabase Auth
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_SERVICE_KEY: str = "your-service-role-key"
    SUPABASE_JWT_SECRET: str = "your-jwt-secret"

    # S3 / Cloudflare R2 Storage
    AWS_ACCESS_KEY_ID: str = "your-r2-or-s3-key"
    AWS_SECRET_ACCESS_KEY: str = "your-r2-or-s3-secret"
    S3_BUCKET_NAME: str = "formatguard-documents"
    S3_ENDPOINT_URL: str = "https://your-account-id.r2.cloudflarestorage.com"

    # OpenAI
    OPENAI_API_KEY: str = "sk-..."

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # Application Limits
    MAX_FILE_SIZE_MB: int = 50
    DOCUMENT_RETENTION_DAYS: int = 30
    FREE_TIER_MONTHLY_CHECKS: int = 5
    STUDENT_PRO_MONTHLY_CHECKS: int = -1  # -1 = unlimited

    # Rate Limiting
    RATE_LIMIT_UPLOADS_PER_WINDOW: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 600  # 10 minutes

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://formatguard.com",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
