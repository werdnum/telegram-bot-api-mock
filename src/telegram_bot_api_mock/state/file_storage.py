"""In-memory file storage for uploaded media."""

import uuid
from dataclasses import dataclass


@dataclass
class StoredFile:
    """Represents a stored file with its metadata."""

    content: bytes
    filename: str
    mime_type: str


class FileStorage:
    """In-memory storage for uploaded files.

    Stores files by unique file_id and allows retrieval of file content
    along with metadata.
    """

    def __init__(self) -> None:
        """Initialize an empty file storage."""
        self._files: dict[str, StoredFile] = {}

    def store_file(self, content: bytes, filename: str, mime_type: str) -> str:
        """Store a file and return its unique file_id.

        Args:
            content: The binary content of the file.
            filename: The original filename.
            mime_type: The MIME type of the file.

        Returns:
            A unique file_id string that can be used to retrieve the file.
        """
        file_id = str(uuid.uuid4())
        self._files[file_id] = StoredFile(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )
        return file_id

    def get_file(self, file_id: str) -> tuple[bytes, str, str] | None:
        """Retrieve a file by its file_id.

        Args:
            file_id: The unique identifier of the file.

        Returns:
            A tuple of (content, filename, mime_type) if found, None otherwise.
        """
        stored = self._files.get(file_id)
        if stored is None:
            return None
        return (stored.content, stored.filename, stored.mime_type)

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from storage.

        Args:
            file_id: The unique identifier of the file to delete.

        Returns:
            True if the file was deleted, False if it wasn't found.
        """
        if file_id in self._files:
            del self._files[file_id]
            return True
        return False

    def clear(self) -> None:
        """Remove all files from storage."""
        self._files.clear()

    @property
    def count(self) -> int:
        """Return the number of stored files."""
        return len(self._files)
