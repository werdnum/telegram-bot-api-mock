"""Core Telegram types models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Represents a Telegram user or bot."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class Chat(BaseModel):
    """Represents a Telegram chat."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    type: Literal["private", "group", "supergroup", "channel"]
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class MessageEntity(BaseModel):
    """Represents one special entity in a text message."""

    model_config = ConfigDict(populate_by_name=True)

    type: str
    offset: int
    length: int
    url: str | None = None
    user: User | None = None
    language: str | None = None


class InlineKeyboardButton(BaseModel):
    """Represents one button of an inline keyboard."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    url: str | None = None
    callback_data: str | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: str | None = None


class InlineKeyboardMarkup(BaseModel):
    """Represents an inline keyboard that appears next to a message."""

    model_config = ConfigDict(populate_by_name=True)

    inline_keyboard: list[list[InlineKeyboardButton]]


class ReplyKeyboardButton(BaseModel):
    """Represents one button of a reply keyboard."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    request_contact: bool | None = None
    request_location: bool | None = None


class ReplyKeyboardMarkup(BaseModel):
    """Represents a custom keyboard with reply options."""

    model_config = ConfigDict(populate_by_name=True)

    keyboard: list[list[ReplyKeyboardButton]]
    resize_keyboard: bool | None = None
    one_time_keyboard: bool | None = None
    selective: bool | None = None


class ReplyKeyboardRemove(BaseModel):
    """Request to remove the custom keyboard."""

    model_config = ConfigDict(populate_by_name=True)

    remove_keyboard: bool = True
    selective: bool | None = None


class ForceReply(BaseModel):
    """Request to show a reply interface to the user."""

    model_config = ConfigDict(populate_by_name=True)

    force_reply: bool = True
    input_field_placeholder: str | None = None
    selective: bool | None = None


# Type alias for reply markup union
ReplyMarkup = InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply


class Message(BaseModel):
    """Represents a message."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    date: int
    chat: Chat
    from_user: User | None = Field(default=None, alias="from")
    text: str | None = None
    entities: list[MessageEntity] | None = None
    reply_markup: InlineKeyboardMarkup | None = None
    reply_to_message: Message | None = None
    edit_date: int | None = None
    # Media fields - to be populated when media types are used
    photo: list | None = None  # list[PhotoSize]
    document: dict | None = None  # Document
    audio: dict | None = None  # Audio
    video: dict | None = None  # Video
    voice: dict | None = None  # Voice
    animation: dict | None = None  # Animation
