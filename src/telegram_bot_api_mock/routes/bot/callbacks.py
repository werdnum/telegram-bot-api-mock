"""Callback query routes for Telegram Bot API Mock."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import AnswerCallbackQueryRequest, TelegramResponse
from telegram_bot_api_mock.routes.bot.request_parsing import is_json_content_type, parse_json_body
from telegram_bot_api_mock.state import AnsweredCallback, ServerState

router = APIRouter()


@router.post("/bot{token}/answerCallbackQuery", response_model=None)
async def answer_callback_query(
    token: str,
    request: Request,
    callback_query_id: str | None = Form(None),
    text: str | None = Form(None),
    show_alert: bool = Form(False),
    url: str | None = Form(None),
    cache_time: int = Form(0),  # noqa: ARG001 - Telegram API parameter not used in mock
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool] | JSONResponse:
    """Answer a callback query from an inline keyboard. Supports Form and JSON."""
    actual_callback_query_id = callback_query_id
    actual_text = text
    actual_show_alert = show_alert
    actual_url = url

    if is_json_content_type(request):
        parsed = await parse_json_body(request, AnswerCallbackQueryRequest)
        if parsed.error:
            return parsed.error
        req_model = parsed.model
        assert req_model is not None  # Type narrowing
        actual_callback_query_id = req_model.callback_query_id
        actual_text = req_model.text
        actual_show_alert = req_model.show_alert or False
        actual_url = req_model.url

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
