"""Configuration for the Telegram Bot API Mock server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration settings."""

    host: str = "0.0.0.0"
    port: int = 9000
    debug: bool = False

    model_config = {"env_prefix": "TELEGRAM_MOCK_"}


def get_settings() -> Settings:
    """Get the current settings."""
    return Settings()
