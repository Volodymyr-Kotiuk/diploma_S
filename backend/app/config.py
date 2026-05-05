import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AutoInfraDiag")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./autoinfradiag.db")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    cors_origins: str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173")
    public_backend_url: str = os.getenv(
        "PUBLIC_BACKEND_URL",
        os.getenv("BACKEND_PUBLIC_URL", os.getenv("RENDER_EXTERNAL_URL", "")),
    )
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    agent_version: str = "1.0.0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
