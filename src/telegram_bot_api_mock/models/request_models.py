"""Request models for Telegram Bot API endpoints."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from telegram_bot_api_mock.models.telegram_types import (
    ForceReply,
    InlineKeyboardMarkup,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def parse_reply_markup(
    value: Any,
) -> InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None:
    """Parse reply_markup from JSON string if needed."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parse_reply_markup(parsed)
    if isinstance(
        value, InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply
    ):
        return value
    if isinstance(value, dict):
        # Determine type based on keys
        if "inline_keyboard" in value:
            return InlineKeyboardMarkup.model_validate(value)
        elif "keyboard" in value:
            return ReplyKeyboardMarkup.model_validate(value)
        elif "remove_keyboard" in value:
            return ReplyKeyboardRemove.model_validate(value)
        elif "force_reply" in value:
            return ForceReply.model_validate(value)
    return None


class SendMessageRequest(BaseModel):
    """Request model for sendMessage endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    chat_id: int | str
    text: str
    parse_mode: str | None = None
    entities: list[MessageEntity] | None = None
    disable_web_page_preview: bool | None = None
    disable_notification: bool | None = None
    protect_content: bool | None = None
    reply_to_message_id: int | None = None
    allow_sending_without_reply: bool | None = None
    reply_markup: (
        InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None
    ) = None

    @field_validator("reply_markup", mode="before")
    @classmethod
    def parse_reply_markup_field(
        cls, value: Any
    ) -> InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None:
        """Parse reply_markup from JSON string if needed."""
        return parse_reply_markup(value)


class EditMessageTextRequest(BaseModel):
    """Request model for editMessageText endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    chat_id: int | str | None = None
    message_id: int | None = None
    inline_message_id: str | None = None
    text: str
    parse_mode: str | None = None
    entities: list[MessageEntity] | None = None
    disable_web_page_preview: bool | None = None
    reply_markup: InlineKeyboardMarkup | None = None

    @field_validator("reply_markup", mode="before")
    @classmethod
    def parse_reply_markup_field(cls, value: Any) -> InlineKeyboardMarkup | None:
        """Parse reply_markup from JSON string if needed."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return cls.parse_reply_markup_field(parsed)
        if isinstance(value, InlineKeyboardMarkup):
            return value
        if isinstance(value, dict) and "inline_keyboard" in value:
            return InlineKeyboardMarkup.model_validate(value)
        return None


class DeleteMessageRequest(BaseModel):
    """Request model for deleteMessage endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    chat_id: int | str
    message_id: int


class AnswerCallbackQueryRequest(BaseModel):
    """Request model for answerCallbackQuery endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    callback_query_id: str
    text: str | None = None
    show_alert: bool | None = None
    url: str | None = None
    cache_time: int | None = None


class SetWebhookRequest(BaseModel):
    """Request model for setWebhook endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    url: str
    certificate: str | None = None
    ip_address: str | None = None
    max_connections: int | None = None
    allowed_updates: list[str] | None = None
    drop_pending_updates: bool | None = None
    secret_token: str | None = None


class SendChatActionRequest(BaseModel):
    """Request model for sendChatAction endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    chat_id: int | str
    action: str


class GetUpdatesRequest(BaseModel):
    """Request model for getUpdates endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    offset: int | None = None
    limit: int | None = None
    timeout: int | None = None
    allowed_updates: list[str] | None = None


# Client API request models (for test simulation)


class ClientUserDict(BaseModel):
    """User dictionary for client API requests."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    is_bot: bool = False
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class ClientSendMessageRequest(BaseModel):
    """Request model for client sendMessage endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    bot_token: str
    chat_id: int
    text: str
    from_user: ClientUserDict | None = None


class ClientSendCommandRequest(BaseModel):
    """Request model for client sendCommand endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    bot_token: str
    chat_id: int
    command: str
    from_user: ClientUserDict | None = None


class ClientSendCallbackRequest(BaseModel):
    """Request model for client sendCallback endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    bot_token: str
    chat_id: int
    message_id: int
    callback_data: str
    from_user: ClientUserDict | None = None
