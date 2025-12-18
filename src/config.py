"""
Application Configuration Module
Loads and validates environment variables
"""

import os
from pydantic_settings import BaseSettings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # ============ Database ============
    mongodb_uri: str = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017/email_assistant"
    )
    database_name: str = os.getenv("DATABASE_NAME", "email_assistant")
    mongodb_user: str = os.getenv("MONGODB_USER", "")
    mongodb_password: str = os.getenv("MONGODB_PASSWORD", "")
    
    # ============ Google OAuth ============
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/auth/google/callback"
    )
    
    # ============ OpenAI ============
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_api_base: str = os.getenv(
        "OPENAI_API_BASE",
        "https://api.openai.com/v1"
    )
    
    # ============ Stripe ============
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_id_pro: str = os.getenv("STRIPE_PRICE_ID_PRO", "")
    stripe_price_id_business: str = os.getenv("STRIPE_PRICE_ID_BUSINESS", "")
    
    # ============ Redis ============
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # ============ Email Sync ============
    email_sync_limit: int = int(os.getenv("EMAIL_SYNC_LIMIT", "50"))
    email_sync_interval_minutes: int = int(
        os.getenv("EMAIL_SYNC_INTERVAL_MINUTES", "15")
    )
    email_batch_size: int = int(os.getenv("EMAIL_BATCH_SIZE", "20"))
    
    # ============ JWT & Security ============
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "your-super-secret-jwt-key-change-in-production"
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )
    
    # ============ CORS ============
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",  # Allow IP address as well
        "http://localhost:5173",
        "http://localhost:8000"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # ============ Email Service ============
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@emailassistant.com")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "Email Assistant")
    
    # ============ Application ============
    app_name: str = os.getenv("APP_NAME", "Email Assistant")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ============ API Settings ============
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    
    # ============ Rate Limiting ============
    rate_limit_enabled: bool = True
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period_seconds: int = int(
        os.getenv("RATE_LIMIT_PERIOD_SECONDS", "60")
    )
    
    # ============ File Storage ============
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate critical settings on startup"""
        if self.environment == "production":
            if self.jwt_secret_key == "your-super-secret-jwt-key-change-in-production":
                raise ValueError(
                    "JWT_SECRET_KEY must be changed for production environment"
                )
            if not self.openai_api_key:
                logger.warning("OPENAI_API_KEY not set in production")
            if not self.stripe_secret_key:
                logger.warning("STRIPE_SECRET_KEY not set in production")
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)
            logger.info(f"Created upload directory: {self.upload_dir}")


# Create global settings instance
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger.info(f"Application initialized: {settings.app_name} v{settings.app_version}")
logger.info(f"Environment: {settings.environment}")
logger.info(f"Debug mode: {settings.debug}")