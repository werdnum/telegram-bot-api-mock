"""Bot API update routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import GetUpdatesRequest, TelegramResponse, Update, User
from telegram_bot_api_mock.services import update_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


@router.api_route("/bot{token}/getUpdates", methods=["GET", "POST"])
async def get_updates(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    offset: Annotated[int | None, Form()] = None,
    limit: Annotated[int | None, Form()] = None,
    timeout: Annotated[int | None, Form()] = None,
) -> TelegramResponse[list[Update]]:
    """Get pending updates for the bot.

    Args:
        token: The bot token.
        state: The server state.
        offset: Only return updates with update_id >= offset.
        limit: Maximum number of updates to return.
        timeout: Timeout for long polling (not implemented).

    Returns:
        TelegramResponse containing list of updates.
    """
    updates = await update_service.get_updates(
        state=state,
        bot_token=token,
        offset=offset,
        limit=limit,
        timeout=timeout,
    )

    return TelegramResponse(ok=True, result=updates)


@router.post("/bot{token}/getUpdates", include_in_schema=False)
async def get_updates_json(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    request: GetUpdatesRequest,
) -> TelegramResponse[list[Update]]:
    """Get pending updates for the bot (JSON body version)."""
    updates = await update_service.get_updates(
        state=state,
        bot_token=token,
        offset=request.offset,
        limit=request.limit,
        timeout=request.timeout,
    )

    return TelegramResponse(ok=True, result=updates)


@router.api_route("/bot{token}/getMe", methods=["GET", "POST"])
async def get_me(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[User]:
    """Get information about the bot.

    Args:
        token: The bot token.
        state: The server state.

    Returns:
        TelegramResponse containing the bot user.
    """
    bot_state = await state.get_or_create_bot(token)

    return TelegramResponse(ok=True, result=bot_state.bot_user)
