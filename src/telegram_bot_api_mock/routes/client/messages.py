"""Client API routes for simulating user messages."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import (
    Chat,
    Message,
    MessageEntity,
    TelegramResponse,
    Update,
    User,
)
from telegram_bot_api_mock.models.request_models import (
    ClientSendCommandRequest,
    ClientSendMessageRequest,
)
from telegram_bot_api_mock.services import webhook_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter(prefix="/client", tags=["client"])


def _get_default_user() -> User:
    """Get a default test user for client API requests.

    Returns:
        A User object representing a test user.
    """
    return User(
        id=1,
        is_bot=False,
        first_name="Test User",
    )


def _user_from_dict(user_dict: dict | None) -> User:
    """Convert a user dictionary to a User object.

    Args:
        user_dict: The user dictionary from the request.

    Returns:
        A User object.
    """
    if user_dict is None:
        return _get_default_user()
    return User.model_validate(user_dict)


@router.post("/sendMessage")
async def client_send_message(
    request: ClientSendMessageRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending a message to a bot.

    This creates a message from the user, creates an Update with that message,
    and queues the Update for the bot. If a webhook is set, delivers the update
    to the webhook.

    Args:
        request: The client send message request.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    # Get or create the bot state
    bot_state = await state.get_or_create_bot(request.bot_token)

    # Get the from_user
    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    # Generate a new message ID
    message_id = await state.id_generator.next_message_id()

    # Create the chat object
    chat = Chat(
        id=request.chat_id,
        type="private",
    )

    # Create the message
    message = Message(
        message_id=message_id,
        date=int(time.time()),
        chat=chat,
        from_user=from_user,
        text=request.text,
    )

    # Store the message in history
    await state.add_message(request.bot_token, message, is_bot_message=False)

    # Generate a new update ID
    update_id = await state.id_generator.next_update_id()

    # Create the update
    update = Update(
        update_id=update_id,
        message=message,
    )

    # Store the update in the bot's pending updates
    await state.add_update(request.bot_token, update)

    # If webhook is configured, deliver the update
    if bot_state.webhook_url is not None:
        await webhook_service.deliver_update_background(
            state=state,
            bot_token=request.bot_token,
            update=update,
        )

    return TelegramResponse(ok=True, result=update)


@router.post("/sendCommand")
async def client_send_command(
    request: ClientSendCommandRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending a command to a bot.

    This is like sendMessage but the text must start with / and a command entity
    is added to the message.

    Args:
        request: The client send command request.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    # Validate command format
    command = request.command
    if not command.startswith("/"):
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: command must start with /",
        )

    # Get or create the bot state
    bot_state = await state.get_or_create_bot(request.bot_token)

    # Get the from_user
    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    # Generate a new message ID
    message_id = await state.id_generator.next_message_id()

    # Create the chat object
    chat = Chat(
        id=request.chat_id,
        type="private",
    )

    # Extract command name (e.g., /start from "/start hello")
    # The command entity covers just the command part
    command_parts = command.split(maxsplit=1)
    command_name = command_parts[0]
    command_length = len(command_name)

    # Create command entity
    command_entity = MessageEntity(
        type="bot_command",
        offset=0,
        length=command_length,
    )

    # Create the message
    message = Message(
        message_id=message_id,
        date=int(time.time()),
        chat=chat,
        from_user=from_user,
        text=command,
        entities=[command_entity],
    )

    # Store the message in history
    await state.add_message(request.bot_token, message, is_bot_message=False)

    # Generate a new update ID
    update_id = await state.id_generator.next_update_id()

    # Create the update
    update = Update(
        update_id=update_id,
        message=message,
    )

    # Store the update in the bot's pending updates
    await state.add_update(request.bot_token, update)

    # If webhook is configured, deliver the update
    if bot_state.webhook_url is not None:
        await webhook_service.deliver_update_background(
            state=state,
            bot_token=request.bot_token,
            update=update,
        )

    return TelegramResponse(ok=True, result=update)
