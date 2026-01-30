"""Update types for Telegram Bot API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from telegram_bot_api_mock.models.telegram_types import Message, User


class CallbackQuery(BaseModel):
    """Represents an incoming callback query from a callback button."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_user: User = Field(alias="from")
    message: Message | None = None
    inline_message_id: str | None = None
    chat_instance: str
    data: str | None = None
    game_short_name: str | None = None


class Update(BaseModel):
    """Represents an incoming update."""

    model_config = ConfigDict(populate_by_name=True)

    update_id: int
    message: Message | None = None
    edited_message: Message | None = None
    channel_post: Message | None = None
    edited_channel_post: Message | None = None
    callback_query: CallbackQuery | None = None
