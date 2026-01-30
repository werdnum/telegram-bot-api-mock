"""Media types for Telegram Bot API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PhotoSize(BaseModel):
    """Represents one size of a photo or a file/sticker thumbnail."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int | None = None


class Document(BaseModel):
    """Represents a general file."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    thumbnail: PhotoSize | None = None


class Audio(BaseModel):
    """Represents an audio file."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    duration: int
    performer: str | None = None
    title: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    thumbnail: PhotoSize | None = None


class Video(BaseModel):
    """Represents a video file."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    thumbnail: PhotoSize | None = None


class Voice(BaseModel):
    """Represents a voice note."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    duration: int
    mime_type: str | None = None
    file_size: int | None = None


class Animation(BaseModel):
    """Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound)."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    thumbnail: PhotoSize | None = None


class File(BaseModel):
    """Represents a file ready to be downloaded."""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_unique_id: str
    file_size: int | None = None
    file_path: str | None = None
