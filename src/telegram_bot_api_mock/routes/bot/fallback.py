"""Fallback route for unimplemented bot API methods."""

from typing import Annotated

from fastapi import APIRouter, Path, Request

from telegram_bot_api_mock.models import TelegramResponse

router = APIRouter()


@router.api_route("/bot{token}/{method:path}", methods=["GET", "POST"])
async def fallback_method(
    token: Annotated[str, Path()],  # noqa: ARG001
    method: Annotated[str, Path()],  # noqa: ARG001
    request: Request,  # noqa: ARG001
) -> TelegramResponse[bool]:
    """Handle any unimplemented bot API method.

    This mimics Telegram's behavior of accepting any method name and returning
    a success response. In a real implementation, some methods would fail,
    but this fallback allows testing code paths that use unimplemented methods.

    Args:
        token: The bot token.
        method: The API method name.
        request: The incoming request.

    Returns:
        TelegramResponse with ok=True and result=True.
    """
    return TelegramResponse(ok=True, result=True)
