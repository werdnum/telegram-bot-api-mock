"""Thread-safe ID generation for the mock server."""

import asyncio


class IDGenerator:
    """Thread-safe ID generator for various Telegram entities.

    Uses asyncio.Lock to ensure thread-safe ID generation in async contexts.
    """

    def __init__(self) -> None:
        """Initialize the ID generator with starting values."""
        self._message_id = 0
        self._update_id = 0
        self._file_id = 0
        self._callback_query_id = 0
        self._lock = asyncio.Lock()

    async def next_message_id(self) -> int:
        """Generate the next sequential message ID.

        Returns:
            The next message ID (starting from 1).
        """
        async with self._lock:
            self._message_id += 1
            return self._message_id

    async def next_update_id(self) -> int:
        """Generate the next sequential update ID.

        Returns:
            The next update ID (starting from 1).
        """
        async with self._lock:
            self._update_id += 1
            return self._update_id

    async def next_file_id(self) -> int:
        """Generate the next sequential file ID number.

        Returns:
            The next file ID number (starting from 1).
        """
        async with self._lock:
            self._file_id += 1
            return self._file_id

    async def next_callback_query_id(self) -> int:
        """Generate the next sequential callback query ID number.

        Returns:
            The next callback query ID number (starting from 1).
        """
        async with self._lock:
            self._callback_query_id += 1
            return self._callback_query_id

    def reset(self) -> None:
        """Reset all counters to zero (for testing purposes)."""
        self._message_id = 0
        self._update_id = 0
        self._file_id = 0
        self._callback_query_id = 0
