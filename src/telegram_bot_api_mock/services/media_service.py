"""Media service for handling media file operations."""

import hashlib

from telegram_bot_api_mock.models.media_types import (
    Animation,
    Audio,
    Document,
    PhotoSize,
    Video,
    Voice,
)
from telegram_bot_api_mock.state import ServerState


def _generate_file_unique_id(file_id: str) -> str:
    """Generate a unique ID that's different from file_id.

    Uses a hash of the file_id to create a shorter, unique identifier.

    Args:
        file_id: The file ID to hash.

    Returns:
        A unique identifier string.
    """
    return hashlib.sha256(file_id.encode()).hexdigest()[:16]


def store_media(
    state: ServerState,
    content: bytes,
    filename: str,
    mime_type: str,
) -> tuple[str, str]:
    """Store media content and return file identifiers.

    Args:
        state: The server state.
        content: The binary content of the file.
        filename: The original filename.
        mime_type: The MIME type of the file.

    Returns:
        A tuple of (file_id, file_unique_id).
    """
    file_id = state.file_storage.store_file(content, filename, mime_type)
    file_unique_id = _generate_file_unique_id(file_id)
    return file_id, file_unique_id


def get_media(
    state: ServerState,
    file_id: str,
) -> tuple[bytes, str, str] | None:
    """Retrieve media content by file_id.

    Args:
        state: The server state.
        file_id: The unique identifier of the file.

    Returns:
        A tuple of (content, filename, mime_type) if found, None otherwise.
    """
    return state.file_storage.get_file(file_id)


def create_photo_sizes(
    state: ServerState,
    content: bytes,
    filename: str,
) -> list[PhotoSize]:
    """Create PhotoSize objects representing different sizes of a photo.

    In a real Telegram server, multiple sizes would be generated.
    For the mock, we create simulated sizes with the same content.

    Args:
        state: The server state.
        content: The binary content of the photo.
        filename: The original filename.

    Returns:
        A list of PhotoSize objects representing different photo sizes.
    """
    # Simulate different photo sizes (small, medium, large)
    sizes = [
        {"width": 90, "height": 90, "suffix": "s"},  # thumbnail
        {"width": 320, "height": 320, "suffix": "m"},  # medium
        {"width": 800, "height": 800, "suffix": "x"},  # large
    ]

    photo_sizes = []
    for size_info in sizes:
        # Store each "size" (in mock, we store the same content)
        file_id = state.file_storage.store_file(
            content,
            f"{filename}_{size_info['suffix']}",
            "image/jpeg",
        )
        file_unique_id = _generate_file_unique_id(file_id)

        photo_sizes.append(
            PhotoSize(
                file_id=file_id,
                file_unique_id=file_unique_id,
                width=int(size_info["width"]),
                height=int(size_info["height"]),
                file_size=len(content),
            )
        )

    return photo_sizes


def create_document(
    state: ServerState,
    content: bytes,
    filename: str,
    mime_type: str,
) -> Document:
    """Create a Document object for an uploaded file.

    Args:
        state: The server state.
        content: The binary content of the document.
        filename: The original filename.
        mime_type: The MIME type of the document.

    Returns:
        A Document object representing the uploaded file.
    """
    file_id, file_unique_id = store_media(state, content, filename, mime_type)

    return Document(
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_name=filename,
        mime_type=mime_type,
        file_size=len(content),
    )


def create_audio(
    state: ServerState,
    content: bytes,
    filename: str,
    mime_type: str,
    duration: int = 0,
    performer: str | None = None,
    title: str | None = None,
) -> Audio:
    """Create an Audio object for an uploaded audio file.

    Args:
        state: The server state.
        content: The binary content of the audio.
        filename: The original filename.
        mime_type: The MIME type of the audio.
        duration: Duration of the audio in seconds.
        performer: The performer of the audio.
        title: The title of the audio.

    Returns:
        An Audio object representing the uploaded file.
    """
    file_id, file_unique_id = store_media(state, content, filename, mime_type)

    return Audio(
        file_id=file_id,
        file_unique_id=file_unique_id,
        duration=duration,
        performer=performer,
        title=title,
        file_name=filename,
        mime_type=mime_type,
        file_size=len(content),
    )


def create_video(
    state: ServerState,
    content: bytes,
    filename: str,
    mime_type: str,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
) -> Video:
    """Create a Video object for an uploaded video file.

    Args:
        state: The server state.
        content: The binary content of the video.
        filename: The original filename.
        mime_type: The MIME type of the video.
        width: Video width.
        height: Video height.
        duration: Duration of the video in seconds.

    Returns:
        A Video object representing the uploaded file.
    """
    file_id, file_unique_id = store_media(state, content, filename, mime_type)

    return Video(
        file_id=file_id,
        file_unique_id=file_unique_id,
        width=width,
        height=height,
        duration=duration,
        file_name=filename,
        mime_type=mime_type,
        file_size=len(content),
    )


def create_voice(
    state: ServerState,
    content: bytes,
    duration: int = 0,
) -> Voice:
    """Create a Voice object for an uploaded voice note.

    Args:
        state: The server state.
        content: The binary content of the voice note.
        duration: Duration of the voice note in seconds.

    Returns:
        A Voice object representing the uploaded voice note.
    """
    # Voice notes are typically ogg/opus format
    file_id, file_unique_id = store_media(state, content, "voice.ogg", "audio/ogg")

    return Voice(
        file_id=file_id,
        file_unique_id=file_unique_id,
        duration=duration,
        mime_type="audio/ogg",
        file_size=len(content),
    )


def create_animation(
    state: ServerState,
    content: bytes,
    filename: str,
    mime_type: str,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
) -> Animation:
    """Create an Animation object for an uploaded GIF or animated file.

    Args:
        state: The server state.
        content: The binary content of the animation.
        filename: The original filename.
        mime_type: The MIME type of the animation.
        width: Animation width.
        height: Animation height.
        duration: Duration of the animation in seconds.

    Returns:
        An Animation object representing the uploaded file.
    """
    file_id, file_unique_id = store_media(state, content, filename, mime_type)

    return Animation(
        file_id=file_id,
        file_unique_id=file_unique_id,
        width=width,
        height=height,
        duration=duration,
        file_name=filename,
        mime_type=mime_type,
        file_size=len(content),
    )
