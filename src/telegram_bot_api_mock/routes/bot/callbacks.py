"""Callback query routes for Telegram Bot API Mock."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Form

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import TelegramResponse
from telegram_bot_api_mock.state import AnsweredCallback, ServerState

router = APIRouter()


@router.post("/bot{token}/answerCallbackQuery", response_model=TelegramResponse[bool])
async def answer_callback_query(
    token: str,
    callback_query_id: str = Form(...),
    text: str | None = Form(None),
    show_alert: bool = Form(False),
    url: str | None = Form(None),
    cache_time: int = Form(0),  # noqa: ARG001
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Answer a callback query from an inline keyboard.

    Args:
        token: The bot token from the URL path.
        callback_query_id: Unique identifier for the query to be answered.
        text: Text of the notification (max 200 characters).
        show_alert: If True, show an alert instead of a notification.
        url: URL to open (for games).
        cache_time: Time in seconds to cache the result.
        state: The server state (injected).

    Returns:
        TelegramResponse with True on success.
    """
    bot_state = await state.get_or_create_bot(token)

    # Store the answered callback
    answered = AnsweredCallback(
        callback_query_id=callback_query_id,
        text=text,
        show_alert=show_alert,
        url=url,
        answered_at=time.time(),
    )

    bot_state.answered_callbacks[callback_query_id] = answered

    return TelegramResponse(ok=True, result=True)
