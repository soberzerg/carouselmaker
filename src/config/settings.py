from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings. Loaded via python-dotenv from .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="POSTGRES_")

    user: str = "carousel"
    password: SecretStr = SecretStr("carousel_secret")
    host: str = "localhost"
    port: int = 5432
    db: str = "carouselmaker"

    @property
    def async_url(self) -> str:
        pwd = quote_plus(self.password.get_secret_value())
        return f"postgresql+asyncpg://{self.user}:{pwd}@{self.host}:{self.port}/{self.db}"

    @property
    def sync_url(self) -> str:
        pwd = quote_plus(self.password.get_secret_value())
        return f"postgresql+psycopg2://{self.user}:{pwd}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="REDIS_")

    url: str = "redis://localhost:6379/0"


class S3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="S3_")

    endpoint_url: str = "http://localhost:9000"
    access_key: SecretStr = SecretStr("minioadmin")
    secret_key: SecretStr = SecretStr("minioadmin")
    bucket: str = "carousels"
    region: str = "us-east-1"


class TelegramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="TELEGRAM_")

    bot_token: SecretStr = SecretStr("")
    webhook_url: str = ""
    webhook_secret: SecretStr = SecretStr("change-me")


class AnthropicSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="ANTHROPIC_")

    api_key: SecretStr = SecretStr("")
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096


class GeminiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="GEMINI_")

    api_key: SecretStr = SecretStr("")
    model: str = "gemini-2.5-flash-image"
    max_concurrency: int = 3


class YooKassaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="YOOKASSA_")

    shop_id: str = "000000"
    secret_key: SecretStr = SecretStr("")
    webhook_secret: SecretStr = SecretStr("")


class Settings(BaseSettings):
    """Application settings. Nested settings rely on python-dotenv to load .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_debug: bool = False
    app_log_level: str = "INFO"
    admin_api_key: SecretStr = SecretStr("change-me")

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    s3: S3Settings = Field(default_factory=S3Settings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    yookassa: YooKassaSettings = Field(default_factory=YooKassaSettings)

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @model_validator(mode="after")
    def _reject_default_secrets_in_production(self) -> Settings:
        if not self.is_dev:
            if self.admin_api_key.get_secret_value() == "change-me":
                msg = "admin_api_key must be changed from default in non-dev environments"
                raise ValueError(msg)
            if self.telegram.webhook_secret.get_secret_value() == "change-me":
                msg = "telegram.webhook_secret must be changed from default in non-dev environments"
                raise ValueError(msg)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
