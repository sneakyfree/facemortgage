import os
import secrets
import warnings
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "FaceMortgage API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Sentry (Error Tracking)
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1  # 10% of transactions for performance monitoring
    sentry_profiles_sample_rate: float = 0.1  # 10% of sampled transactions for profiling

    # Database
    database_url: str = "postgresql+asyncpg://facemortgage:facemortgage_dev@localhost:5432/facemortgage"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    slow_query_threshold: float = 0.5  # Log queries taking longer than this (in seconds)

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security - SECRET_KEY must be set via environment variable
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Cookie settings
    cookie_secure: bool = True  # Set to False for local development without HTTPS
    cookie_samesite: str = "lax"  # "lax", "strict", or "none"
    cookie_domain: Optional[str] = None  # None = current domain only

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is strong enough for production."""
        # Check if running in production without a proper secret key
        env = os.getenv("ENVIRONMENT", "development")

        if not v or v in ("", "your-secret-key-change-in-production", "dev-secret-key-change-in-production-12345"):
            if env == "production":
                raise ValueError(
                    "SECRET_KEY must be set to a strong random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            # Generate a random key for development
            warnings.warn(
                "SECRET_KEY not set - using auto-generated key. "
                "This is fine for development but must be set for production.",
                UserWarning
            )
            return secrets.token_urlsafe(64)

        if len(v) < 32:
            if env == "production":
                raise ValueError("SECRET_KEY must be at least 32 characters long for production")
            warnings.warn("SECRET_KEY is less than 32 characters - consider using a longer key", UserWarning)

        return v

    # CORS - configured via environment for flexibility
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id_basic: Optional[str] = None
    stripe_price_id_professional: Optional[str] = None
    stripe_price_id_premium: Optional[str] = None

    # Frontend URL (for Stripe redirects)
    frontend_url: str = "http://localhost:3000"

    # External Data Provider
    data_provider: str = "datagod"  # datagod, redr, modex, corelogic
    data_provider_api_key: Optional[str] = None
    data_provider_base_url: Optional[str] = None
    data_cache_ttl_hours: int = 24
    data_provider_timeout: int = 30  # HTTP timeout in seconds
    data_provider_retry_attempts: int = 3  # Number of retry attempts
    data_provider_fallback_enabled: bool = True  # Enable fallback chain

    # Provider-specific settings
    datagod_api_key: Optional[str] = None
    datagod_base_url: str = "https://api.datagod.com/v1"
    corelogic_api_key: Optional[str] = None
    corelogic_api_secret: Optional[str] = None
    corelogic_base_url: str = "https://api.corelogic.com/v2"
    redr_api_key: Optional[str] = None
    redr_base_url: str = "https://api.redr.io/v1"
    modex_api_key: Optional[str] = None
    modex_base_url: str = "https://api.modex.com/v1"

    # WebRTC
    turn_server_url: Optional[str] = None
    turn_server_username: Optional[str] = None
    turn_server_credential: Optional[str] = None

    # LiveKit (optional - for scalable video infrastructure)
    livekit_url: Optional[str] = None  # wss://your-project.livekit.cloud
    livekit_api_key: Optional[str] = None
    livekit_api_secret: Optional[str] = None
    use_livekit: bool = False  # Toggle between custom WebRTC and LiveKit

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
