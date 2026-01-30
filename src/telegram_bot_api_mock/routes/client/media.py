"""Client API media routes for test simulation."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import TelegramResponse
from telegram_bot_api_mock.services import media_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter(prefix="/client", tags=["client"])


@router.get("/getMedia/{file_id}")
async def get_media(
    file_id: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
) -> Response:
    """Download media content by file_id.

    This endpoint allows test clients to download media that was sent by bots.

    Args:
        file_id: The unique identifier of the file to download.
        state: The server state.

    Returns:
        The file content with appropriate content-type header.
    """
    file_data = media_service.get_media(state, file_id)

    if file_data is None:
        return Response(
            content=b"File not found",
            status_code=404,
            media_type="text/plain",
        )

    content, filename, mime_type = file_data

    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/getChatActions")
async def get_chat_actions(
    state: Annotated[ServerState, Depends(get_state)],
    bot_token: Annotated[str, Query()],
    chat_id: Annotated[int, Query()],
) -> TelegramResponse[list[dict]]:
    """Get active chat actions for a specific chat.

    Chat actions expire after 5 seconds, so only recent actions are returned.

    Args:
        state: The server state.
        bot_token: The bot token to get actions for.
        chat_id: The chat ID to get actions for.

    Returns:
        TelegramResponse containing list of active chat actions.
    """
    bot_state = state.get_bot(bot_token)

    if bot_state is None:
        return TelegramResponse(ok=True, result=[])

    # Get the chat action if it exists and is not expired
    action = bot_state.get_chat_action(chat_id)

    if action is None:
        return TelegramResponse(ok=True, result=[])

    # Return the action as a dict
    return TelegramResponse(
        ok=True,
        result=[
            {
                "chat_id": action.chat_id,
                "action": action.action,
                "timestamp": action.timestamp,
            }
        ],
    )


@router.get("/getAllChatActions")
async def get_all_chat_actions(
    state: Annotated[ServerState, Depends(get_state)],
    bot_token: Annotated[str, Query()],
) -> TelegramResponse[list[dict]]:
    """Get all active chat actions for a bot.

    Chat actions expire after 5 seconds, so only recent actions are returned.

    Args:
        state: The server state.
        bot_token: The bot token to get actions for.

    Returns:
        TelegramResponse containing list of all active chat actions.
    """
    bot_state = state.get_bot(bot_token)

    if bot_state is None:
        return TelegramResponse(ok=True, result=[])

    current_time = time.time()
    active_actions = []

    # Filter out expired actions (older than 5 seconds)
    for chat_id, action in list(bot_state.chat_actions.items()):
        if current_time - action.timestamp <= 5:
            active_actions.append(
                {
                    "chat_id": action.chat_id,
                    "action": action.action,
                    "timestamp": action.timestamp,
                }
            )
        else:
            # Clean up expired action
            del bot_state.chat_actions[chat_id]

    return TelegramResponse(ok=True, result=active_actions)
