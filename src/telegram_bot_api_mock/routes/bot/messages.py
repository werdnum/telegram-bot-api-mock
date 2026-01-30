"""Bot API message routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import (
    DeleteMessageRequest,
    EditMessageTextRequest,
    InlineKeyboardMarkup,
    Message,
    SendMessageRequest,
    TelegramResponse,
)
from telegram_bot_api_mock.models.request_models import parse_reply_markup
from telegram_bot_api_mock.services import message_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


@router.post("/bot{token}/sendMessage")
async def send_message(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    text: Annotated[str, Form()],
    parse_mode: Annotated[str | None, Form()] = None,
    reply_to_message_id: Annotated[int | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a message to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the message to.
        text: The message text.
        parse_mode: Optional parse mode.
        reply_to_message_id: Optional message ID to reply to.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    # Parse chat_id to int if it's a string
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    # Parse reply_markup from JSON string if provided
    parsed_markup = None
    if reply_markup:
        parsed_markup = parse_reply_markup(reply_markup)
        if parsed_markup is not None and not isinstance(parsed_markup, InlineKeyboardMarkup):
            # For sendMessage, we accept any ReplyMarkup but only store InlineKeyboardMarkup
            # since that's what the Message model supports
            parsed_markup = None

    message = await message_service.create_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_message_id,
        reply_markup=parsed_markup,
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendMessage", include_in_schema=False)
async def send_message_json(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    request: SendMessageRequest,
) -> TelegramResponse[Message]:
    """Send a message to a chat (JSON body version).

    This handler accepts JSON body instead of form data.
    """
    # Parse chat_id to int if it's a string
    chat_id = request.chat_id
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    # Extract InlineKeyboardMarkup if that's what was provided
    reply_markup = None
    if isinstance(request.reply_markup, InlineKeyboardMarkup):
        reply_markup = request.reply_markup

    message = await message_service.create_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        text=request.text,
        parse_mode=request.parse_mode,
        reply_to_message_id=request.reply_to_message_id,
        reply_markup=reply_markup,
        entities=request.entities,
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/editMessageText")
async def edit_message_text(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    text: Annotated[str, Form()],
    chat_id: Annotated[int | str | None, Form()] = None,
    message_id: Annotated[int | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message | bool]:
    """Edit a message text.

    Args:
        token: The bot token.
        state: The server state.
        text: The new message text.
        chat_id: The chat ID where the message is.
        message_id: The message ID to edit.
        reply_markup: Optional JSON-encoded inline keyboard markup.

    Returns:
        TelegramResponse containing the edited message or True.
    """
    if chat_id is None or message_id is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: chat_id and message_id are required",
        )

    # Parse chat_id to int if it's a string
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    # Parse reply_markup from JSON string if provided
    parsed_markup = None
    if reply_markup:
        markup = parse_reply_markup(reply_markup)
        if isinstance(markup, InlineKeyboardMarkup):
            parsed_markup = markup

    message = await message_service.edit_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=parsed_markup,
    )

    if message is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: message not found",
        )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/editMessageText", include_in_schema=False)
async def edit_message_text_json(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    request: EditMessageTextRequest,
) -> TelegramResponse[Message | bool]:
    """Edit a message text (JSON body version)."""
    if request.chat_id is None or request.message_id is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: chat_id and message_id are required",
        )

    # Parse chat_id to int if it's a string
    chat_id = request.chat_id
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    message = await message_service.edit_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        message_id=request.message_id,
        text=request.text,
        reply_markup=request.reply_markup,
    )

    if message is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: message not found",
        )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/deleteMessage")
async def delete_message(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    message_id: Annotated[int, Form()],
) -> TelegramResponse[bool]:
    """Delete a message.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID where the message is.
        message_id: The message ID to delete.

    Returns:
        TelegramResponse containing True on success.
    """
    # Parse chat_id to int if it's a string
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    result = await message_service.delete_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        message_id=message_id,
    )

    if not result:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: message not found",
        )

    return TelegramResponse(ok=True, result=True)


@router.post("/bot{token}/deleteMessage", include_in_schema=False)
async def delete_message_json(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    request: DeleteMessageRequest,
) -> TelegramResponse[bool]:
    """Delete a message (JSON body version)."""
    # Parse chat_id to int if it's a string
    chat_id = request.chat_id
    if isinstance(chat_id, str):
        chat_id = int(chat_id)

    result = await message_service.delete_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        message_id=request.message_id,
    )

    if not result:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: message not found",
        )

    return TelegramResponse(ok=True, result=True)
