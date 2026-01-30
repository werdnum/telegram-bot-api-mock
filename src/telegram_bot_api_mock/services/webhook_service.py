"""Webhook management service for Telegram Bot API Mock."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from telegram_bot_api_mock.models import Update
from telegram_bot_api_mock.state import ServerState, WebhookConfig

logger = logging.getLogger(__name__)


async def set_webhook(
    state: ServerState,
    bot_token: str,
    url: str,
    secret_token: str | None = None,
    max_connections: int = 40,
    allowed_updates: list[str] | None = None,
    drop_pending_updates: bool = False,
    ip_address: str | None = None,
) -> bool:
    """Set a webhook URL for a bot.

    Args:
        state: The server state.
        bot_token: The bot token.
        url: The webhook URL to set.
        secret_token: Optional secret token for webhook verification.
        max_connections: Maximum allowed number of simultaneous HTTPS connections.
        allowed_updates: List of update types to receive.
        drop_pending_updates: Whether to drop pending updates.
        ip_address: Fixed IP address for webhook requests.

    Returns:
        True if the webhook was set successfully.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Create webhook configuration
    webhook_config = WebhookConfig(
        url=url,
        secret_token=secret_token,
        max_connections=max_connections,
        allowed_updates=allowed_updates,
        ip_address=ip_address,
    )

    # Update bot state
    bot_state.webhook_url = url
    bot_state.webhook_secret = secret_token
    bot_state.webhook_config = webhook_config

    # Drop pending updates if requested
    if drop_pending_updates:
        bot_state.pending_updates.clear()

    logger.info(f"Webhook set for bot {bot_token}: {url}")
    return True


async def delete_webhook(
    state: ServerState,
    bot_token: str,
    drop_pending_updates: bool = False,
) -> bool:
    """Delete the webhook for a bot.

    Args:
        state: The server state.
        bot_token: The bot token.
        drop_pending_updates: Whether to drop pending updates.

    Returns:
        True if the webhook was deleted successfully.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Clear webhook configuration
    bot_state.webhook_url = None
    bot_state.webhook_secret = None
    bot_state.webhook_config = None

    # Drop pending updates if requested
    if drop_pending_updates:
        bot_state.pending_updates.clear()

    logger.info(f"Webhook deleted for bot {bot_token}")
    return True


async def get_webhook_info(
    state: ServerState,
    bot_token: str,
) -> dict[str, Any]:
    """Get webhook information for a bot.

    Args:
        state: The server state.
        bot_token: The bot token.

    Returns:
        A dictionary containing webhook information.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    config = bot_state.webhook_config

    if config is None:
        return {
            "url": "",
            "has_custom_certificate": False,
            "pending_update_count": len(bot_state.pending_updates),
        }

    return {
        "url": config.url,
        "has_custom_certificate": config.has_custom_certificate,
        "pending_update_count": len(bot_state.pending_updates),
        "ip_address": config.ip_address,
        "max_connections": config.max_connections,
        "allowed_updates": config.allowed_updates,
        "last_error_date": config.last_error_date,
        "last_error_message": config.last_error_message,
        "last_synchronization_error_date": config.last_synchronization_error_date,
    }


async def deliver_update(
    state: ServerState,
    bot_token: str,
    update: Update,
) -> bool:
    """Deliver an update to the bot's webhook URL.

    This function sends the update via HTTP POST to the configured webhook URL.
    Delivery is non-blocking and failures are logged but not raised.

    Args:
        state: The server state.
        bot_token: The bot token.
        update: The update to deliver.

    Returns:
        True if the update was delivered successfully, False otherwise.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    if bot_state.webhook_url is None:
        logger.debug(f"No webhook URL configured for bot {bot_token}")
        return False

    webhook_url = bot_state.webhook_url
    webhook_secret = bot_state.webhook_secret

    # Build headers
    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }
    if webhook_secret:
        headers["X-Telegram-Bot-Api-Secret-Token"] = webhook_secret

    # Serialize the update
    update_json = update.model_dump_json(by_alias=True, exclude_none=True)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                webhook_url,
                content=update_json,
                headers=headers,
            )

        if response.status_code == 200:
            logger.debug(f"Update {update.update_id} delivered to {webhook_url}")
            return True
        else:
            error_msg = f"Webhook returned status {response.status_code}: {response.text}"
            logger.warning(f"Failed to deliver update {update.update_id}: {error_msg}")

            # Update error info in webhook config
            if bot_state.webhook_config:
                bot_state.webhook_config.last_error_date = int(time.time())
                bot_state.webhook_config.last_error_message = error_msg

            return False

    except httpx.RequestError as e:
        error_msg = f"Request error: {e}"
        logger.warning(f"Failed to deliver update {update.update_id}: {error_msg}")

        # Update error info in webhook config
        if bot_state.webhook_config:
            bot_state.webhook_config.last_error_date = int(time.time())
            bot_state.webhook_config.last_error_message = error_msg

        return False


async def deliver_update_background(
    state: ServerState,
    bot_token: str,
    update: Update,
) -> None:
    """Deliver an update to the bot's webhook URL in the background.

    This function schedules the delivery as a background task, making it
    non-blocking for the main flow.

    Args:
        state: The server state.
        bot_token: The bot token.
        update: The update to deliver.
    """
    asyncio.create_task(deliver_update(state, bot_token, update))
