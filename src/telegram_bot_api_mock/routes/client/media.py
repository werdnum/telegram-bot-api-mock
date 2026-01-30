"""Client API media routes for test simulation."""

import base64
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import (
    Chat,
    Message,
    TelegramResponse,
    Update,
    User,
)
from telegram_bot_api_mock.models.request_models import (
    ClientSendAudioRequest,
    ClientSendDocumentRequest,
    ClientSendPhotoRequest,
    ClientSendVideoRequest,
)
from telegram_bot_api_mock.services import media_service, webhook_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter(prefix="/client", tags=["client"])


def _get_default_user() -> User:
    """Get a default test user for client API requests."""
    return User(
        id=1,
        is_bot=False,
        first_name="Test User",
    )


async def _create_client_media_message(
    state: ServerState,
    bot_token: str,
    chat_id: int,
    from_user: User,
    caption: str | None = None,
    photo: list | None = None,
    document: dict | None = None,
    audio: dict | None = None,
    video: dict | None = None,
) -> Update:
    """Create a message with media and queue it as an update.

    Args:
        state: The server state.
        bot_token: The bot token.
        chat_id: The chat ID.
        from_user: The user sending the message.
        caption: Optional caption for the media.
        photo: Photo sizes list (for photos).
        document: Document dict (for documents).
        audio: Audio dict (for audio).
        video: Video dict (for video).

    Returns:
        The created Update containing the message.
    """
    bot_state = await state.get_or_create_bot(bot_token)

    message_id = await state.id_generator.next_message_id()

    chat = Chat(
        id=chat_id,
        type="private",
    )

    message = Message(
        message_id=message_id,
        date=int(time.time()),
        chat=chat,
        from_user=from_user,
        text=caption,
        photo=photo,
        document=document,
        audio=audio,
        video=video,
    )

    await state.add_message(bot_token, message, is_bot_message=False)

    update_id = await state.id_generator.next_update_id()

    update = Update(
        update_id=update_id,
        message=message,
    )

    await state.add_update(bot_token, update)

    if bot_state.webhook_url is not None:
        await webhook_service.deliver_update_background(
            state=state,
            bot_token=bot_token,
            update=update,
        )

    return update


@router.post("/sendPhoto")
async def client_send_photo(
    request: ClientSendPhotoRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending a photo to a bot.

    Args:
        request: The client send photo request with base64-encoded photo.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    try:
        content = base64.b64decode(request.photo)
    except Exception:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: invalid base64 encoding for photo",
        )

    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    filename = request.filename or "photo.jpg"
    photo_sizes = media_service.create_photo_sizes(state, content, filename)
    photo_list = [ps.model_dump() for ps in photo_sizes]

    update = await _create_client_media_message(
        state=state,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
        from_user=from_user,
        caption=request.caption,
        photo=photo_list,
    )

    return TelegramResponse(ok=True, result=update)


@router.post("/sendVideo")
async def client_send_video(
    request: ClientSendVideoRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending a video to a bot.

    Args:
        request: The client send video request with base64-encoded video.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    try:
        content = base64.b64decode(request.video)
    except Exception:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: invalid base64 encoding for video",
        )

    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    filename = request.filename or "video.mp4"
    video = media_service.create_video(
        state,
        content,
        filename,
        mime_type="video/mp4",
        width=request.width or 0,
        height=request.height or 0,
        duration=request.duration or 0,
    )

    update = await _create_client_media_message(
        state=state,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
        from_user=from_user,
        caption=request.caption,
        video=video.model_dump(),
    )

    return TelegramResponse(ok=True, result=update)


@router.post("/sendAudio")
async def client_send_audio(
    request: ClientSendAudioRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending an audio file to a bot.

    Args:
        request: The client send audio request with base64-encoded audio.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    try:
        content = base64.b64decode(request.audio)
    except Exception:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: invalid base64 encoding for audio",
        )

    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    filename = request.filename or "audio.mp3"
    audio = media_service.create_audio(
        state,
        content,
        filename,
        mime_type="audio/mpeg",
        duration=request.duration or 0,
        performer=request.performer,
        title=request.title,
    )

    update = await _create_client_media_message(
        state=state,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
        from_user=from_user,
        caption=request.caption,
        audio=audio.model_dump(),
    )

    return TelegramResponse(ok=True, result=update)


@router.post("/sendDocument")
async def client_send_document(
    request: ClientSendDocumentRequest,
    state: Annotated[ServerState, Depends(get_state)],
) -> TelegramResponse[Update]:
    """Simulate a user sending a document to a bot.

    Args:
        request: The client send document request with base64-encoded document.
        state: The server state.

    Returns:
        TelegramResponse containing the created Update.
    """
    try:
        content = base64.b64decode(request.document)
    except Exception:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: invalid base64 encoding for document",
        )

    if request.from_user is not None:
        from_user = User.model_validate(request.from_user.model_dump())
    else:
        from_user = _get_default_user()

    mime_type = request.mime_type or "application/octet-stream"
    document = media_service.create_document(
        state,
        content,
        request.filename,
        mime_type,
    )

    update = await _create_client_media_message(
        state=state,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
        from_user=from_user,
        caption=request.caption,
        document=document.model_dump(),
    )

    return TelegramResponse(ok=True, result=update)


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
