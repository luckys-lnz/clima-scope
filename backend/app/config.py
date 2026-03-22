"""
Configuration Management

Application settings and environment variables.
"""

import os
import json
from pathlib import Path
from typing import List, ClassVar
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

    # SUPABASE SETTINGS
    SUPABASE_URL: str = Field(
        default="",  # Will be required from .env
        env="SUPABASE_URL",
        description="Supabase project URL"
    )
    
    SUPABASE_SERVICE_KEY: str = Field(
        default="",  # Will be required from .env
        env="SUPABASE_SERVICE_KEY",
        description="Supabase service role key (for backend operations)"
    )
    
    SUPABASE_ANON_KEY: str = Field(
        default="",  # Will be required from .env
        env="SUPABASE_ANON_KEY", 
        description="Supabase anonymous key (for frontend operations)"
    )
    
    # Optional: Supabase Storage bucket name
    SUPABASE_STORAGE_BUCKET: str = Field(
        default="weather-reports",
        env="SUPABASE_STORAGE_BUCKET",
        description="Supabase Storage bucket for weather reports"
    )

    # County Data
    COUNTY_DATA_PATH: ClassVar[Path] = Path(__file__).parent / "data" / "counties.json"
    
    @classmethod
    def load_county_data(cls):
        with open(cls.COUNTY_DATA_PATH, "r") as f:
            return json.load(f)
    
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
