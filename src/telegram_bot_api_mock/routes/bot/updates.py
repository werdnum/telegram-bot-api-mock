"""Bot API update routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Request

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import GetUpdatesRequest, TelegramResponse, Update, User
from telegram_bot_api_mock.services import update_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


@router.api_route("/bot{token}/getUpdates", methods=["GET", "POST"])
async def get_updates(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    offset: Annotated[int | None, Form()] = None,
    limit: Annotated[int | None, Form()] = None,
    timeout: Annotated[int | None, Form()] = None,
) -> TelegramResponse[list[Update]]:
    """Get pending updates for the bot. Supports Form and JSON."""
    actual_offset = offset
    actual_limit = limit
    actual_timeout = timeout

    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                req_model = GetUpdatesRequest.model_validate(body)
                actual_offset = req_model.offset if req_model.offset is not None else actual_offset
                actual_limit = req_model.limit if req_model.limit is not None else actual_limit
                actual_timeout = req_model.timeout if req_model.timeout is not None else actual_timeout
            except Exception:
                pass

    updates = await update_service.get_updates(
        state=state,
        bot_token=token,
        offset=actual_offset,
        limit=actual_limit,
        timeout=actual_timeout,
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
