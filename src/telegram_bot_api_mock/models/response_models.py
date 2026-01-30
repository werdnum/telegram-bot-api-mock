"""Response models for Telegram Bot API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TelegramResponse[T](BaseModel):
    """Generic response wrapper for Telegram Bot API responses."""

    model_config = ConfigDict(populate_by_name=True)

    ok: bool
    result: T | None = None
    error_code: int | None = None
    description: str | None = None
