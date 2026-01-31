"""Bot API message routes."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Request
from fastapi.responses import JSONResponse

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


def error_response(error_code: int, description: str) -> JSONResponse:
    """Create an error response with the appropriate HTTP status code.

    Args:
        error_code: The Telegram error code (also used as HTTP status code).
        description: The error description.

    Returns:
        JSONResponse with the error details and appropriate HTTP status code.
    """
    return JSONResponse(
        status_code=error_code,
        content={
            "ok": False,
            "error_code": error_code,
            "description": description,
        },
    )


def parse_reply_parameters(reply_parameters: str | None) -> int | None:
    """Parse reply_parameters JSON string to extract message_id.

    Args:
        reply_parameters: JSON string like '{"message_id": 123}'

    Returns:
        The message_id if found, None otherwise.
    """
    if not reply_parameters:
        return None
    try:
        data = json.loads(reply_parameters)
        if isinstance(data, dict) and "message_id" in data:
            return int(data["message_id"])
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return None


@router.post("/bot{token}/sendMessage")
async def send_message(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str | None, Form()] = None,
    text: Annotated[str | None, Form()] = None,
    parse_mode: Annotated[str | None, Form()] = None,
    reply_to_message_id: Annotated[int | None, Form()] = None,
    reply_parameters: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a message to a chat.

    Supports both Form data and JSON body.
    """
    actual_chat_id = chat_id
    actual_text = text
    actual_parse_mode = parse_mode
    actual_reply_to_message_id = reply_to_message_id
    actual_reply_parameters = reply_parameters
    actual_reply_markup_input = reply_markup
    entities = None

    # Handle JSON body
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            req_model = SendMessageRequest.model_validate(body)
            actual_chat_id = req_model.chat_id
            actual_text = req_model.text
            actual_parse_mode = req_model.parse_mode
            actual_reply_to_message_id = req_model.reply_to_message_id
            # Note: SendMessageRequest already parses reply_markup
            if isinstance(req_model.reply_markup, InlineKeyboardMarkup):
                parsed_markup = req_model.reply_markup
            else:
                parsed_markup = None
            entities = req_model.entities
            # For JSON, we use the parsed markup directly
            actual_reply_markup_input = None
        except Exception:
            pass
    else:
        # Handle Form data parsing for markup
        parsed_markup = None
        if actual_reply_markup_input:
            parsed_markup = parse_reply_markup(actual_reply_markup_input)
            if parsed_markup is not None and not isinstance(parsed_markup, InlineKeyboardMarkup):
                parsed_markup = None

    if actual_chat_id is None or actual_text is None:
        return error_response(400, "Bad Request: chat_id and text are required")

    # Narrow types for typechecker
    final_chat_id: int
    if isinstance(actual_chat_id, str):
        final_chat_id = int(actual_chat_id)
    else:
        final_chat_id = actual_chat_id

    # Handle both legacy reply_to_message_id and new reply_parameters format
    if actual_reply_to_message_id is None and actual_reply_parameters:
        actual_reply_to_message_id = parse_reply_parameters(actual_reply_parameters)

    message = await message_service.create_message(
        state=state,
        bot_token=token,
        chat_id=final_chat_id,
        text=actual_text,
        parse_mode=actual_parse_mode,
        reply_to_message_id=actual_reply_to_message_id,
        reply_markup=parsed_markup,
        entities=entities,
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/editMessageText", response_model=None)
async def edit_message_text(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    text: Annotated[str | None, Form()] = None,
    chat_id: Annotated[int | str | None, Form()] = None,
    message_id: Annotated[int | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message | bool] | JSONResponse:
    """Edit a message text. Supports Form and JSON."""
    actual_text = text
    actual_chat_id = chat_id
    actual_message_id = message_id
    actual_reply_markup_input = reply_markup
    parsed_markup = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            req_model = EditMessageTextRequest.model_validate(body)
            actual_text = req_model.text
            actual_chat_id = req_model.chat_id
            actual_message_id = req_model.message_id
            parsed_markup = req_model.reply_markup
        except Exception:
            pass
    else:
        if actual_reply_markup_input:
            markup = parse_reply_markup(actual_reply_markup_input)
            if isinstance(markup, InlineKeyboardMarkup):
                parsed_markup = markup

    if actual_text is None or actual_chat_id is None or actual_message_id is None:
        return error_response(400, "Bad Request: text, chat_id and message_id are required")

    # Narrow types for typechecker
    final_chat_id: int
    if isinstance(actual_chat_id, str):
        final_chat_id = int(actual_chat_id)
    else:
        final_chat_id = actual_chat_id

    message = await message_service.edit_message(
        state=state,
        bot_token=token,
        chat_id=final_chat_id,
        message_id=actual_message_id,
        text=actual_text,
        reply_markup=parsed_markup,
    )

    if message is None:
        return error_response(400, "Bad Request: message not found")

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/deleteMessage", response_model=None)
async def delete_message(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str | None, Form()] = None,
    message_id: Annotated[int | None, Form()] = None,
) -> TelegramResponse[bool] | JSONResponse:
    """Delete a message. Supports Form and JSON."""
    actual_chat_id = chat_id
    actual_message_id = message_id

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            req_model = DeleteMessageRequest.model_validate(body)
            actual_chat_id = req_model.chat_id
            actual_message_id = req_model.message_id
        except Exception:
            pass

    if actual_chat_id is None or actual_message_id is None:
        return error_response(400, "Bad Request: chat_id and message_id are required")

    # Narrow types for typechecker
    final_chat_id: int
    if isinstance(actual_chat_id, str):
        final_chat_id = int(actual_chat_id)
    else:
        final_chat_id = actual_chat_id

    result = await message_service.delete_message(
        state=state,
        bot_token=token,
        chat_id=final_chat_id,
        message_id=actual_message_id,
    )

    if not result:
        return error_response(400, "Bad Request: message not found")

    return TelegramResponse(ok=True, result=True)
