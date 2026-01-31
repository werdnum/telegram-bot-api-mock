"""Bot API chat action routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Request
from fastapi.responses import JSONResponse

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import SendChatActionRequest, TelegramResponse
from telegram_bot_api_mock.routes.bot.request_parsing import is_json_content_type, parse_json_body
from telegram_bot_api_mock.state import ServerState

router = APIRouter()

# Valid chat actions as defined by Telegram API
VALID_CHAT_ACTIONS = {
    "typing",
    "upload_photo",
    "record_video",
    "upload_video",
    "record_voice",
    "upload_voice",
    "upload_document",
    "choose_sticker",
    "find_location",
    "record_video_note",
    "upload_video_note",
}


def _parse_chat_id(chat_id: int | str) -> int:
    """Parse chat_id to int if it's a string."""
    if isinstance(chat_id, str):
        return int(chat_id)
    return chat_id


@router.post("/bot{token}/sendChatAction", response_model=None)
async def send_chat_action(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str | None, Form()] = None,
    action: Annotated[str | None, Form()] = None,
) -> TelegramResponse[bool] | JSONResponse:
    """Send a chat action to indicate bot activity. Supports Form and JSON."""
    actual_chat_id = chat_id
    actual_action = action

    if is_json_content_type(request):
        parsed = await parse_json_body(request, SendChatActionRequest)
        if parsed.error:
            return parsed.error
        req_model = parsed.model
        assert req_model is not None  # Type narrowing
        actual_chat_id = req_model.chat_id
        actual_action = req_model.action

    if actual_chat_id is None or actual_action is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: chat_id and action are required",
        )

    actual_chat_id = _parse_chat_id(actual_chat_id)

    # Validate the action
    if actual_action not in VALID_CHAT_ACTIONS:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description=f"Bad Request: invalid action '{actual_action}'",
        )

    # Get the bot state and store the action
    bot_state = await state.get_or_create_bot(token)
    bot_state.set_chat_action(actual_chat_id, actual_action)

    return TelegramResponse(ok=True, result=True)
