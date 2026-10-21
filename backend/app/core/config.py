from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_secret_key: str = Field(..., min_length=32)
    access_token_minutes: int = Field(default=30, ge=5, le=1440)
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_cors_origins: str = Field(default="http://localhost:5173")

    # Database
    database_url: str

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0")

    # Encryption
    encryption_key: str

    # WhatsApp
    whatsapp_mock_mode: bool = Field(default=True)
    whatsapp_app_id: str = Field(default="")
    whatsapp_app_secret: str = Field(default="")
    whatsapp_webhook_verify_token: str = Field(default="")

    # AI
    openai_api_key: str = Field(default="")
    ai_provider: str = Field(default="mock")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v


settings = Settings()
