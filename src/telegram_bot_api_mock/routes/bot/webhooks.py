"""Webhook management routes for Telegram Bot API Mock."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import TelegramResponse
from telegram_bot_api_mock.services import webhook_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


@router.post("/bot{token}/setWebhook", response_model=TelegramResponse[bool])
async def set_webhook(
    token: str,
    url: str = Form(...),
    certificate: str | None = Form(None),  # noqa: ARG001
    ip_address: str | None = Form(None),
    max_connections: int = Form(40),
    allowed_updates: list[str] | None = Form(None),
    drop_pending_updates: bool = Form(False),
    secret_token: str | None = Form(None),
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Set a webhook URL for receiving updates.

    Args:
        token: The bot token from the URL path.
        url: HTTPS URL to send updates to.
        certificate: Optional public key certificate.
        ip_address: Optional fixed IP address.
        max_connections: Maximum allowed number of simultaneous HTTPS connections.
        allowed_updates: List of update types to receive.
        drop_pending_updates: Whether to drop pending updates.
        secret_token: Secret token for webhook verification.
        state: The server state (injected).

    Returns:
        TelegramResponse with True on success.
    """
    result = await webhook_service.set_webhook(
        state=state,
        bot_token=token,
        url=url,
        secret_token=secret_token,
        max_connections=max_connections,
        allowed_updates=allowed_updates,
        drop_pending_updates=drop_pending_updates,
        ip_address=ip_address,
    )

    return TelegramResponse(ok=True, result=result)


@router.post("/bot{token}/deleteWebhook", response_model=TelegramResponse[bool])
async def delete_webhook(
    token: str,
    drop_pending_updates: bool = Form(False),
    state: ServerState = Depends(get_state),
) -> TelegramResponse[bool]:
    """Delete the current webhook.

    Args:
        token: The bot token from the URL path.
        drop_pending_updates: Whether to drop pending updates.
        state: The server state (injected).

    Returns:
        TelegramResponse with True on success.
    """
    result = await webhook_service.delete_webhook(
        state=state,
        bot_token=token,
        drop_pending_updates=drop_pending_updates,
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
