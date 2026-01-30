"""Update service for handling Telegram updates."""

from telegram_bot_api_mock.models import Message, Update
from telegram_bot_api_mock.state import ServerState


async def create_update_for_message(
    state: ServerState,
    bot_token: str,
    message: Message,
) -> Update:
    """Create an update for a message and queue it for the bot.

    Args:
        state: The server state.
        bot_token: The bot token.
        message: The message to create an update for.

    Returns:
        The created Update object.
    """
    # Generate a new update ID
    update_id = await state.id_generator.next_update_id()

    # Create the update
    update = Update(
        update_id=update_id,
        message=message,
    )

    # Store the update in the bot's pending updates
    await state.add_update(bot_token, update)

    return update


async def get_updates(
    state: ServerState,
    bot_token: str,
    offset: int | None = None,
    limit: int | None = None,
    timeout: int | None = None,  # noqa: ARG001
) -> list[Update]:
    """Get pending updates for a bot.

    When offset is provided, updates with update_id < offset are discarded.

    Args:
        state: The server state.
        bot_token: The bot token.
        offset: Only return updates with update_id >= offset.
        limit: Maximum number of updates to return (default 100).
        timeout: Timeout in seconds for long polling (not implemented for now).

    Returns:
        List of pending updates.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # If offset is provided, mark updates before it as delivered
    if offset is not None:
        bot_state.mark_updates_delivered(offset - 1)
        bot_state.clear_delivered_updates()

    # Get pending updates
    stored_updates = bot_state.get_pending_updates(limit=limit or 100, offset=offset)

    # Return the Update objects
    return [stored.update for stored in stored_updates]
