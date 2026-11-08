from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Warkari"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "Multilingual, voice-first AI assistance platform for Varkari pilgrims "
        "participating in the Pandharpur Wari."
    )
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # API Keys & Third-party integrations
    GNANI_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./warkari.db"

    # Security & Tracking
    SECRET_KEY: str = "warkari_prototype_default_secret_key_change_in_production_2026"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            self.FRONTEND_URL.rstrip("/"),
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
        if self.ALLOWED_ORIGINS:
            for extra in self.ALLOWED_ORIGINS.split(","):
                clean = extra.strip().rstrip("/")
                if clean and clean not in origins:
                    origins.append(clean)
        return list(dict.fromkeys(origins))

    model_config = SettingsConfigDict(
        # Check both backend/.env and root .env dynamically regardless of execution working directory
        env_file=(str(BASE_DIR / ".env"), str(BASE_DIR.parent / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
