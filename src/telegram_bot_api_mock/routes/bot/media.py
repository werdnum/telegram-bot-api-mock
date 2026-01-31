"""Bot API media routes."""

import json
import time
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import Response

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import (
    Chat,
    InlineKeyboardMarkup,
    Message,
    TelegramResponse,
)
from telegram_bot_api_mock.models.media_types import File as TelegramFile
from telegram_bot_api_mock.models.request_models import GetFileRequest, parse_reply_markup
from telegram_bot_api_mock.services import media_service
from telegram_bot_api_mock.state import ServerState

router = APIRouter()


async def _create_media_message(
    state: ServerState,
    bot_token: str,
    chat_id: int,
    caption: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    photo: list | None = None,
    document: dict | None = None,
    audio: dict | None = None,
    video: dict | None = None,
    voice: dict | None = None,
    animation: dict | None = None,
) -> Message:
    """Create a message with media content.

    Args:
        state: The server state.
        bot_token: The bot token.
        chat_id: The chat ID to send the message to.
        caption: Optional caption text.
        reply_markup: Optional inline keyboard markup.
        photo: Optional list of PhotoSize objects.
        document: Optional Document object as dict.
        audio: Optional Audio object as dict.
        video: Optional Video object as dict.
        voice: Optional Voice object as dict.
        animation: Optional Animation object as dict.

    Returns:
        The created Message object.
    """
    # Generate a new message ID
    message_id = await state.id_generator.next_message_id()

    # Get the bot state to access bot user
    bot_state = await state.get_or_create_bot(bot_token)

    # Create the chat object
    chat = Chat(
        id=chat_id,
        type="private",
    )

    # Create the message
    message = Message(
        message_id=message_id,
        date=int(time.time()),
        chat=chat,
        from_user=bot_state.bot_user,
        text=caption,
        reply_markup=reply_markup,
        photo=photo,
        document=document,
        audio=audio,
        video=video,
        voice=voice,
        animation=animation,
    )

    # Store the message
    await state.add_message(bot_token, message, is_bot_message=True)

    return message


def _parse_chat_id(chat_id: int | str) -> int:
    """Parse chat_id to int if it's a string."""
    if isinstance(chat_id, str):
        return int(chat_id)
    return chat_id


def _parse_markup(reply_markup: str | None) -> InlineKeyboardMarkup | None:
    """Parse reply_markup from JSON string if provided."""
    if reply_markup:
        parsed = parse_reply_markup(reply_markup)
        if isinstance(parsed, InlineKeyboardMarkup):
            return parsed
    return None


@router.post("/bot{token}/sendPhoto")
async def send_photo(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    photo: Annotated[UploadFile, File()],
    caption: Annotated[str | None, Form()] = None,
    parse_mode: Annotated[str | None, Form()] = None,  # noqa: ARG001
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a photo to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the photo to.
        photo: The photo file to send.
        caption: Optional photo caption.
        parse_mode: Optional parse mode for caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the photo content
    content = await photo.read()
    filename = photo.filename or "photo.jpg"

    # Create photo sizes
    photo_sizes = media_service.create_photo_sizes(state, content, filename)

    # Convert to list of dicts for the message
    photo_list = [ps.model_dump() for ps in photo_sizes]

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        photo=photo_list,
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendDocument")
async def send_document(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    document: Annotated[UploadFile, File()],
    caption: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a document to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the document to.
        document: The document file to send.
        caption: Optional document caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the document content
    content = await document.read()
    filename = document.filename or "document"
    mime_type = document.content_type or "application/octet-stream"

    # Create document object
    doc = media_service.create_document(state, content, filename, mime_type)

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        document=doc.model_dump(),
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendVideo")
async def send_video(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    video: Annotated[UploadFile, File()],
    duration: Annotated[int | None, Form()] = None,
    width: Annotated[int | None, Form()] = None,
    height: Annotated[int | None, Form()] = None,
    caption: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a video to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the video to.
        video: The video file to send.
        duration: Duration of the video in seconds.
        width: Video width.
        height: Video height.
        caption: Optional video caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the video content
    content = await video.read()
    filename = video.filename or "video.mp4"
    mime_type = video.content_type or "video/mp4"

    # Create video object
    vid = media_service.create_video(
        state=state,
        content=content,
        filename=filename,
        mime_type=mime_type,
        width=width or 0,
        height=height or 0,
        duration=duration or 0,
    )

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        video=vid.model_dump(),
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendAudio")
async def send_audio(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    audio: Annotated[UploadFile, File()],
    duration: Annotated[int | None, Form()] = None,
    performer: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    caption: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send an audio file to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the audio to.
        audio: The audio file to send.
        duration: Duration of the audio in seconds.
        performer: The performer of the audio.
        title: The title of the audio.
        caption: Optional audio caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the audio content
    content = await audio.read()
    filename = audio.filename or "audio.mp3"
    mime_type = audio.content_type or "audio/mpeg"

    # Create audio object
    aud = media_service.create_audio(
        state=state,
        content=content,
        filename=filename,
        mime_type=mime_type,
        duration=duration or 0,
        performer=performer,
        title=title,
    )

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        audio=aud.model_dump(),
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendVoice")
async def send_voice(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    voice: Annotated[UploadFile, File()],
    duration: Annotated[int | None, Form()] = None,
    caption: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send a voice note to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the voice note to.
        voice: The voice note file to send.
        duration: Duration of the voice note in seconds.
        caption: Optional voice note caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the voice content
    content = await voice.read()

    # Create voice object
    voi = media_service.create_voice(
        state=state,
        content=content,
        duration=duration or 0,
    )

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        voice=voi.model_dump(),
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendAnimation")
async def send_animation(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    animation: Annotated[UploadFile, File()],
    duration: Annotated[int | None, Form()] = None,
    width: Annotated[int | None, Form()] = None,
    height: Annotated[int | None, Form()] = None,
    caption: Annotated[str | None, Form()] = None,
    reply_markup: Annotated[str | None, Form()] = None,
) -> TelegramResponse[Message]:
    """Send an animation (GIF) to a chat.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the animation to.
        animation: The animation file to send.
        duration: Duration of the animation in seconds.
        width: Animation width.
        height: Animation height.
        caption: Optional animation caption.
        reply_markup: Optional JSON-encoded reply markup.

    Returns:
        TelegramResponse containing the sent message.
    """
    chat_id = _parse_chat_id(chat_id)
    parsed_markup = _parse_markup(reply_markup)

    # Read the animation content
    content = await animation.read()
    filename = animation.filename or "animation.gif"
    mime_type = animation.content_type or "image/gif"

    # Create animation object
    anim = media_service.create_animation(
        state=state,
        content=content,
        filename=filename,
        mime_type=mime_type,
        width=width or 0,
        height=height or 0,
        duration=duration or 0,
    )

    message = await _create_media_message(
        state=state,
        bot_token=token,
        chat_id=chat_id,
        caption=caption,
        reply_markup=parsed_markup,
        animation=anim.model_dump(),
    )

    return TelegramResponse(ok=True, result=message)


@router.post("/bot{token}/sendMediaGroup")
async def send_media_group(
    token: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
    chat_id: Annotated[int | str, Form()],
    media: Annotated[str, Form()],
) -> TelegramResponse[list[Message]]:
    """Send a group of photos or documents as an album.

    This is a simplified implementation that creates multiple messages.

    Args:
        token: The bot token.
        state: The server state.
        chat_id: The chat ID to send the media group to.
        media: JSON array of InputMedia objects.

    Returns:
        TelegramResponse containing the list of sent messages.
    """
    chat_id = _parse_chat_id(chat_id)

    # Parse the media JSON
    try:
        media_items = json.loads(media)
    except json.JSONDecodeError:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: invalid media JSON",
        )

    messages = []
    for item in media_items:
        # media_type = item.get("type", "photo")  # Not used in simplified implementation
        caption = item.get("caption")

        # For simplicity, create a placeholder message for each item
        # In a real implementation, you'd handle file uploads here
        message_id = await state.id_generator.next_message_id()
        bot_state = await state.get_or_create_bot(token)

        chat = Chat(id=chat_id, type="private")

        message = Message(
            message_id=message_id,
            date=int(time.time()),
            chat=chat,
            from_user=bot_state.bot_user,
            text=caption,
        )

        await state.add_message(token, message, is_bot_message=True)
        messages.append(message)

    return TelegramResponse(ok=True, result=messages)


async def _get_file_impl(
    token: str,
    state: ServerState,
    file_id: str,
) -> TelegramResponse[TelegramFile]:
    """Implementation of getFile logic."""
    # Try to get the file from storage
    file_data = media_service.get_media(state, file_id)

    if file_data is None:
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: file not found",
        )

    content, filename, _mime_type = file_data

    # Generate file_unique_id
    file_unique_id = media_service._generate_file_unique_id(file_id)

    # Create the file path that can be used to download
    file_path = f"files/{token}/{file_id}/{filename}"

    telegram_file = TelegramFile(
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_size=len(content),
        file_path=file_path,
    )

    return TelegramResponse(ok=True, result=telegram_file)


@router.get("/bot{token}/getFile")
@router.post("/bot{token}/getFile")
async def get_file(
    token: Annotated[str, Path()],
    request: Request,
    state: Annotated[ServerState, Depends(get_state)],
    file_id: Annotated[str | None, Query()] = None,
) -> TelegramResponse[TelegramFile]:
    """Get information about a file and prepare it for downloading.

    Args:
        token: The bot token.
        request: The incoming request.
        state: The server state.
        file_id: The file identifier to get info about (from query).

    Returns:
        TelegramResponse containing the File object.
    """
    actual_file_id = file_id

    # If not in query, try to get from body (JSON or Form)
    if not actual_file_id and request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                actual_file_id = body.get("file_id")
            except Exception:
                pass
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                form = await request.form()
                actual_file_id = form.get("file_id")
            except Exception:
                pass

    if not actual_file_id or not isinstance(actual_file_id, str):
        return TelegramResponse(
            ok=False,
            error_code=400,
            description="Bad Request: file_id is required",
        )

    return await _get_file_impl(token, state, actual_file_id)


@router.get("/file/bot{token}/{file_path:path}")
async def download_file(
    token: Annotated[str, Path()],
    file_path: Annotated[str, Path()],
    state: Annotated[ServerState, Depends(get_state)],
) -> Response:
    """Download a file by its path.

    This endpoint follows the standard Telegram Bot API format:
    /file/bot<token>/<file_path>

    Args:
        token: The bot token.
        file_path: The file path returned by getFile.
        state: The server state.

    Returns:
        The file content with appropriate content-type header.
    """
    # Extract file_id from the file_path
    # file_path format: files/{token}/{file_id}/{filename}
    parts = file_path.split("/")
    if len(parts) < 3 or parts[0] != "files" or parts[1] != token:
        return Response(
            content=b"Invalid file path",
            status_code=400,
            media_type="text/plain",
        )

    file_id = parts[2]

    # Try to get the file from storage
    file_data = media_service.get_media(state, file_id)

    if file_data is None:
        return Response(
            content=b"File not found",
            status_code=404,
            media_type="text/plain",
        )

    content, _filename, mime_type = file_data

    return Response(
        content=content,
        media_type=mime_type,
    )
