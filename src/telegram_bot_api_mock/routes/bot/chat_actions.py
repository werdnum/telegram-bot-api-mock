"""Bot API chat action routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import TelegramResponse
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


@router.post("/bot{token}/sendChatAction")
async def send_chat_action(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    action: Annotated[str, Form()],
) -> TelegramResponse[bool]:
    """Send a chat action to indicate bot activity.

    Use this method when you need to tell the user that something is happening
    on the bot's side. The status is set for 5 seconds or less.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the action to.
        action: The action to send (e.g., "typing", "upload_photo").

    Returns:
        TelegramResponse containing True on success.
    """
    chat_id = _parse_chat_id(chat_id)

    # Validate the action
    if action not in VALID_CHAT_ACTIONS:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description=f"Bad Request: invalid action '{action}'",
        )

    # Get the bot state and store the action
    bot_state = await state.get_or_create_bot(token)
    bot_state.set_chat_action(chat_id, action)

    return TelegramResponse(ok=True, result=True)
