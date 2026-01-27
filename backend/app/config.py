"""
Configuration Management

Application settings and environment variables.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Clima-scope API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        env="CORS_ORIGINS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/climascope",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis (optional)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    
    # PDF Generator
    PDF_GENERATOR_PATH: str = Field(
        default=str(Path(__file__).parent.parent.parent / "pdf_generator"),
        env="PDF_GENERATOR_PATH"
    )
    
    # AI Service
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    AI_PROVIDER: str = Field(default="openai", env="AI_PROVIDER")  # openai or anthropic
    
    # File Storage
    STORAGE_PATH: str = Field(
        default=str(Path(__file__).parent.parent.parent / "storage"),
        env="STORAGE_PATH"
    )
    PDF_STORAGE_PATH: str = Field(
        default=str(Path(__file__).parent.parent.parent / "storage" / "pdfs"),
        env="PDF_STORAGE_PATH"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure storage directories exist
Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.PDF_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
