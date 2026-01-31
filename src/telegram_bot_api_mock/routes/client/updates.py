"""Client API routes for retrieving updates and message history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import Message, TelegramResponse, Update
from telegram_bot_api_mock.state import ServerState

router = APIRouter(prefix="/client", tags=["client"])


@router.get("/getUpdates")
async def client_get_updates(
    bot_token: Annotated[str, Query()],
    chat_id: Annotated[int, Query()],
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[list[Update]]:
    """Get messages sent BY the bot to a specific chat.

    This returns messages the bot sent to the user, not updates for the bot.
    Useful for tests to verify what the bot responded with.

    Args:
        bot_token: The bot token.
        chat_id: The chat ID to get messages for.
        state: The server state.

    Returns:
        TelegramResponse containing list of updates (messages wrapped in Update objects).
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Get messages for the chat that were sent by the bot
    stored_messages = bot_state.get_messages_for_chat(chat_id)

    # Filter to only bot messages and wrap in Update objects
    bot_updates = [
        Update(update_id=msg.message_id, message=msg.raw_message)
        for msg in stored_messages
        if msg.is_bot_message
    ]

    return TelegramResponse(ok=True, result=bot_updates)


@router.get("/getUpdatesHistory")
async def client_get_updates_history(
    bot_token: Annotated[str, Query()],
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[list[Update]]:
    """Get all updates history for a bot.

    Returns all updates that were created for this bot, including ones that
    have already been delivered. This is useful for testing to see the full
    history of what updates were generated.

    Args:
        bot_token: The bot token.
        state: The server state.

    Returns:
        TelegramResponse containing list of all updates for the bot.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Get all updates (including delivered ones)
    updates = [stored.update for stored in bot_state.pending_updates]

    return TelegramResponse(ok=True, result=updates)
