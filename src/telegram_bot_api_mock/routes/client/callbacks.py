"""Client API routes for simulating callback queries."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import CallbackQuery, TelegramResponse, Update, User
from telegram_bot_api_mock.models.request_models import ClientSendCallbackRequest
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


@router.post("/sendCallback")
async def client_send_callback(
    request: ClientSendCallbackRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user clicking an inline button (callback query).

    This creates a CallbackQuery and Update, queues the Update for the bot,
    and delivers to webhook if configured.

    Args:
        request: The client send callback request.
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

    # Find the message being clicked
    stored_message = bot_state.get_message(request.chat_id, request.message_id)
    if stored_message is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: message not found",
        )

    # Generate a new callback query ID
    callback_query_id = await state.id_generator.next_callback_query_id()

    # Create the callback query
    # Note: We use model_validate with a dict to handle the "from" alias properly
    callback_query = CallbackQuery.model_validate(
        {
            "id": str(callback_query_id),
            "from": from_user.model_dump(),
            "message": stored_message.raw_message.model_dump(by_alias=True),
            "chat_instance": str(request.chat_id),
            "data": request.callback_data,
        }
    )

    # Generate a new update ID
    update_id = await state.id_generator.next_update_id()

    # Create the update
    update = Update(
        update_id=update_id,
        callback_query=callback_query,
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
