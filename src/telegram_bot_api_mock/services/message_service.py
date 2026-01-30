"""Message service for handling message operations."""

import time

from telegram_bot_api_mock.models import (
    Chat,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    User,
)
from telegram_bot_api_mock.state import ServerState


async def create_message(
    state: ServerState,
    bot_token: str,
    chat_id: int,
    text: str,
    from_user: User | None = None,
    reply_to_message_id: int | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    entities: list[MessageEntity] | None = None,
    parse_mode: str | None = None,  # noqa: ARG001
) -> Message:
    """Create a new message and store it in state.

    Args:
        state: The server state.
        bot_token: The bot token.
        chat_id: The chat ID where the message is sent.
        text: The message text.
        from_user: The user sending the message (defaults to bot user).
        reply_to_message_id: Optional message ID to reply to.
        reply_markup: Optional inline keyboard markup.
        entities: Optional message entities.
        parse_mode: Optional parse mode (HTML, Markdown, etc.).

    Returns:
        The created Message object.
    """
    # Generate a new message ID
    message_id = await state.id_generator.next_message_id()

    # Get the bot state to access bot user
    bot_state = await state.get_or_create_bot(bot_token)

    # If no from_user provided, use the bot user
    if from_user is None:
        from_user = bot_state.bot_user

    # Create the chat object (simple private chat for now)
    chat = Chat(
        id=chat_id,
        type="private",
    )

    # Get reply_to_message if specified
    reply_to_message: Message | None = None
    if reply_to_message_id is not None:
        stored_msg = bot_state.get_message(chat_id, reply_to_message_id)
        if stored_msg is not None:
            reply_to_message = stored_msg.raw_message

    # Create the message
    message = Message(
        message_id=message_id,
        date=int(time.time()),
        chat=chat,
        from_user=from_user,
        text=text,
        entities=entities,
        reply_markup=reply_markup,
        reply_to_message=reply_to_message,
    )

    # Store the message
    await state.add_message(bot_token, message, is_bot_message=from_user.is_bot)

    return message


async def edit_message(
    state: ServerState,
    bot_token: str,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message | None:
    """Edit an existing message.

    Args:
        state: The server state.
        bot_token: The bot token.
        chat_id: The chat ID where the message is.
        message_id: The message ID to edit.
        text: The new message text.
        reply_markup: Optional new inline keyboard markup.

    Returns:
        The edited Message object, or None if message not found.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Find the stored message
    stored_msg = bot_state.get_message(chat_id, message_id)
    if stored_msg is None:
        return None

    # Create an updated message
    old_message = stored_msg.raw_message
    edited_message = Message(
        message_id=old_message.message_id,
        date=old_message.date,
        chat=old_message.chat,
        from_user=old_message.from_user,
        text=text,
        entities=old_message.entities,
        reply_markup=reply_markup if reply_markup is not None else old_message.reply_markup,
        reply_to_message=old_message.reply_to_message,
        edit_date=int(time.time()),
    )

    # Update the stored message
    stored_msg.text = text
    stored_msg.raw_message = edited_message

    return edited_message


async def delete_message(
    state: ServerState,
    bot_token: str,
    chat_id: int,
    message_id: int,
) -> bool:
    """Delete a message.

    Args:
        state: The server state.
        bot_token: The bot token.
        chat_id: The chat ID where the message is.
        message_id: The message ID to delete.

    Returns:
        True if the message was deleted, False if not found.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    # Find and remove the message from history
    for i, msg in enumerate(bot_state.message_history):
        if msg.chat_id == chat_id and msg.message_id == message_id:
            bot_state.message_history.pop(i)
            return True

    return False
