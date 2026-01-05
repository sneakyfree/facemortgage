from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "FaceMortgage API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://facemortgage:facemortgage_dev@localhost:5432/facemortgage"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id_basic: Optional[str] = None
    stripe_price_id_professional: Optional[str] = None
    stripe_price_id_premium: Optional[str] = None

    # Frontend URL (for Stripe redirects)
    frontend_url: str = "http://localhost:3000"

    # External Data Provider
    data_provider: str = "datagod"  # datagod, reeder, modex, corelogic
    data_provider_api_key: Optional[str] = None
    data_provider_base_url: Optional[str] = None
    data_cache_ttl_hours: int = 24

    # WebRTC
    turn_server_url: Optional[str] = None
    turn_server_username: Optional[str] = None
    turn_server_credential: Optional[str] = None

    # Email (SendGrid)
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@facemortgage.com"

    # SMS (Twilio)
    twilio_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone: Optional[str] = None

    # Video Storage
    video_storage_path: str = "./uploads/videos"
    video_max_size_mb: int = 100
    video_max_duration_seconds: int = 60

    # Cloud Storage (S3/R2)
    storage_backend: str = "local"  # local, s3, r2
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    s3_endpoint_url: Optional[str] = None  # For R2 or S3-compatible storage
    s3_public_url_base: Optional[str] = None  # CDN or public URL prefix

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
