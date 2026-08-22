"""应用配置（pydantic-settings + .env）。"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    database_url: str = Field(
        default="mysql+pymysql://wms:wms@127.0.0.1:3306/wms?charset=utf8mb4",
        alias="DATABASE_URL",
    )
    health_check_db: bool = Field(default=True, alias="HEALTH_CHECK_DB")
    health_check_db_timeout_seconds: float = Field(
        default=2.0,
        alias="HEALTH_CHECK_DB_TIMEOUT_SECONDS",
    )

    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expire_minutes: int = Field(default=480, alias="JWT_ACCESS_EXPIRE_MINUTES")

    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
