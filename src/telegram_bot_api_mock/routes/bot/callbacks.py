"""Callback query routes for Telegram Bot API Mock."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Form, Request

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import AnswerCallbackQueryRequest, TelegramResponse
from telegram_bot_api_mock.state import AnsweredCallback, ServerState

router = APIRouter()


@router.post("/bot{token}/answerCallbackQuery", response_model=TelegramResponse[bool])
async def answer_callback_query(
    token: str,
    request: Request,
    callback_query_id: str | None = Form(None),
    text: str | None = Form(None),
    show_alert: bool = Form(False),
    url: str | None = Form(None),
    cache_time: int = Form(0),  # noqa: ARG001
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Answer a callback query from an inline keyboard. Supports Form and JSON."""
    actual_callback_query_id = callback_query_id
    actual_text = text
    actual_show_alert = show_alert
    actual_url = url

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            req_model = AnswerCallbackQueryRequest.model_validate(body)
            actual_callback_query_id = req_model.callback_query_id
            actual_text = req_model.text
            actual_show_alert = req_model.show_alert or False
            actual_url = req_model.url
        except Exception:
            pass

    if not actual_callback_query_id:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: callback_query_id is required",
        )

    bot_state = await state.get_or_create_bot(token)

    # Store the answered callback
    answered = AnsweredCallback(
        callback_query_id=actual_callback_query_id,
        text=actual_text,
        show_alert=actual_show_alert,
        url=actual_url,
        answered_at=time.time(),
    )

    bot_state.answered_callbacks[actual_callback_query_id] = answered

    return TelegramResponse(ok=True, result=True)
