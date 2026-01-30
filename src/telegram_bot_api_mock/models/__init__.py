"""Pydantic models for Telegram types."""

from telegram_bot_api_mock.models.media_types import (
    Animation,
    Audio,
    Document,
    File,
    PhotoSize,
    Video,
    Voice,
)
from telegram_bot_api_mock.models.request_models import (
    AnswerCallbackQueryRequest,
    ClientSendCallbackRequest,
    ClientSendCommandRequest,
    ClientSendMessageRequest,
    ClientUserDict,
    DeleteMessageRequest,
    EditMessageTextRequest,
    GetUpdatesRequest,
    SendChatActionRequest,
    SendMessageRequest,
    SetWebhookRequest,
)
from telegram_bot_api_mock.models.response_models import TelegramResponse
from telegram_bot_api_mock.models.telegram_types import (
    Chat,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ReplyKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyMarkup,
    User,
)
from telegram_bot_api_mock.models.update_types import CallbackQuery, Update

__all__ = [
    # Telegram types
    "User",
    "Chat",
    "MessageEntity",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "ReplyKeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "ForceReply",
    "ReplyMarkup",
    "Message",
    # Media types
    "PhotoSize",
    "Document",
    "Audio",
    "Video",
    "Voice",
    "Animation",
    "File",
    # Update types
    "CallbackQuery",
    "Update",
    # Request models
    "SendMessageRequest",
    "EditMessageTextRequest",
    "DeleteMessageRequest",
    "AnswerCallbackQueryRequest",
    "SetWebhookRequest",
    "SendChatActionRequest",
    "GetUpdatesRequest",
    # Client request models
    "ClientSendMessageRequest",
    "ClientSendCommandRequest",
    "ClientSendCallbackRequest",
    "ClientUserDict",
    # Response models
    "TelegramResponse",
]
