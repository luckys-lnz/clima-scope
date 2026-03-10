"""
Configuration Management

Application settings and environment variables.
"""

import os
import json
from pathlib import Path
from typing import Any, List, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_ROOT / ".env"), str(PROJECT_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application
    APP_NAME: str = "Clima-scope API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
        env="CORS_ORIGINS"
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value: Any) -> bool:
        """Accept common string values (e.g. 'release') for DEBUG."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return bool(value)

        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "debug", "development", "dev"}:
            return True
        if text in {"0", "false", "no", "off", "release", "production", "prod", ""}:
            return False

        raise ValueError("DEBUG must be a boolean-like value.")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> str:
        """Support comma-separated or JSON-array CORS origins."""
        if isinstance(value, (list, tuple)):
            return ",".join(str(origin).strip() for origin in value if str(origin).strip())

        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return ",".join(str(origin).strip() for origin in parsed if str(origin).strip())
                except json.JSONDecodeError:
                    pass
            return raw

        return str(value)
    
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

    # Station Data Auto Fetch (TAHMO/KMD)
    AUTO_STATION_FETCH_ENABLED: bool = Field(default=True, env="AUTO_STATION_FETCH_ENABLED")
    TAHMO_BASE_URL: str = Field(default="", env="TAHMO_BASE_URL")
    TAHMO_API_KEY: str = Field(default="", env="TAHMO_API_KEY")
    KMD_BASE_URL: str = Field(default="", env="KMD_BASE_URL")
    KMD_API_KEY: str = Field(default="", env="KMD_API_KEY")
    STATION_FETCH_TIMEOUT_SECONDS: int = Field(default=30, env="STATION_FETCH_TIMEOUT_SECONDS")
    
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
    
# Create settings instance
settings = Settings()

# Ensure storage directories exist
Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.PDF_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
