"""Webhook management routes for Telegram Bot API Mock."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form, Request

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import SetWebhookRequest, TelegramResponse
from telegram_bot_api_mock.services import webhook_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


@router.post("/bot{token}/setWebhook", response_model=TelegramResponse[bool])
async def set_webhook(
    token: str,
    request: Request,
    url: str | None = Form(None),
    certificate: str | None = Form(None),  # noqa: ARG001
    ip_address: str | None = Form(None),
    max_connections: int = Form(40),
    allowed_updates: list[str] | None = Form(None),
    drop_pending_updates: bool = Form(False),
    secret_token: str | None = Form(None),
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Set a webhook URL for receiving updates. Supports Form and JSON."""
    actual_url = url
    actual_secret_token = secret_token
    actual_max_connections = max_connections
    actual_allowed_updates = allowed_updates
    actual_drop_pending_updates = drop_pending_updates
    actual_ip_address = ip_address

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            req_model = SetWebhookRequest.model_validate(body)
            actual_url = req_model.url
            actual_secret_token = req_model.secret_token
            actual_max_connections = req_model.max_connections or 40
            actual_allowed_updates = req_model.allowed_updates
            actual_drop_pending_updates = req_model.drop_pending_updates or False
            actual_ip_address = req_model.ip_address
        except Exception:
            pass

    if not actual_url:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: url is required",
        )

    result = await webhook_service.set_webhook(
        state=state,
        bot_token=token,
        url=actual_url,
        secret_token=actual_secret_token,
        max_connections=actual_max_connections,
        allowed_updates=actual_allowed_updates,
        drop_pending_updates=actual_drop_pending_updates,
        ip_address=actual_ip_address,
    )

    return TelegramResponse(ok=True, result=result)


@router.post("/bot{token}/deleteWebhook", response_model=TelegramResponse[bool])
async def delete_webhook(
    token: str,
    request: Request,
    drop_pending_updates: bool = Form(False),
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Delete the current webhook. Supports Form and JSON."""
    actual_drop_pending_updates = drop_pending_updates

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            actual_drop_pending_updates = body.get("drop_pending_updates", False)
        except Exception:
            pass

    result = await webhook_service.delete_webhook(
        state=state,
        bot_token=token,
        drop_pending_updates=actual_drop_pending_updates,
    )

    return TelegramResponse(ok=True, result=result)


@router.api_route(
    "/bot{token}/getWebhookInfo",
    methods=["GET", "POST"],
    response_model=TelegramResponse[dict[str, Any]],
)
async def get_webhook_info(
    token: str,
    state: ServerState = Depends(get_state),
) -> TelegramResponse[dict[str, Any]]:
    """Get current webhook status.

    Args:
        token: The bot token from the URL path.
        state: The server state (injected).

    Returns:
        TelegramResponse with WebhookInfo object.
    """
    result = await webhook_service.get_webhook_info(
        state=state,
        bot_token=token,
    )

    return TelegramResponse(ok=True, result=result)
