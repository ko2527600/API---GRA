"""Application configuration from environment variables"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",
    )
    
    # Application
    APP_NAME: str = "GRA External Integration API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/gra_api"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Security
    API_SECRET_KEY: str = "your-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    RATE_LIMIT_ENABLED: bool = True
    
    # GRA API
    GRA_API_BASE_URL: str = "https://apitest.e-vatgh.com"
    GRA_API_TIMEOUT: int = 30
    GRA_API_RETRIES: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Async Processing
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_ENABLED: bool = True
    
    # Retry Configuration
    MAX_RETRIES: int = 5
    RETRY_BACKOFF_BASE: int = 1
    RETRY_BACKOFF_MAX: int = 3600
    
    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_TIN_VALIDATION: int = 86400
    CACHE_TTL_HEALTH_CHECK: int = 300
    
    # Webhooks
    WEBHOOK_ENABLED: bool = True
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_BACKOFF_BASE: int = 1
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555
    AUDIT_LOG_MASK_SENSITIVE: bool = True
    
    # Data Retention
    SUBMISSION_RETENTION_DAYS: int = 2555
    WEBHOOK_LOG_RETENTION_DAYS: int = 90
    
    # Submission Processing
    SUBMISSION_PROCESSING_TIMEOUT: int = 300
    SUBMISSION_POLLING_INTERVAL: int = 5
    SUBMISSION_POLLING_MAX_ATTEMPTS: int = 60
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value"""
        valid_envs = ["development", "staging", "production", "testing"]
        if v not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v):
        """Validate JWT algorithm"""
        valid_algorithms = ["HS256", "HS512", "RS256"]
        if v not in valid_algorithms:
            raise ValueError(f"ALGORITHM must be one of {valid_algorithms}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Failed to load settings: {e}")
    # Create with explicit values
    settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/API_s_GRA",
        ENCRYPTION_KEY="your-encryption-key-change-in-production",
        API_SECRET_KEY="your-secret-key-change-in-production"
    )


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
