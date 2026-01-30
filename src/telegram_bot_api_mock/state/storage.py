"""Main state management for the mock server."""

import asyncio
import time
from dataclasses import dataclass, field

from telegram_bot_api_mock.models import Message, Update, User
from telegram_bot_api_mock.state.counters import IDGenerator
from telegram_bot_api_mock.state.file_storage import FileStorage


@dataclass
class StoredMessage:
    """Represents a stored message in the server's history."""

    message_id: int
    chat_id: int
    text: str | None
    date: int
    is_bot_message: bool
    raw_message: Message
    from_user_id: int | None = None


@dataclass
class StoredUpdate:
    """Represents a stored update for delivery to bots."""

    update_id: int
    update: Update
    delivered: bool = False


@dataclass
class ChatAction:
    """Represents a chat action (typing indicator, etc.)."""

    chat_id: int
    action: str
    timestamp: float


@dataclass
class AnsweredCallback:
    """Represents an answered callback query."""

    callback_query_id: str
    text: str | None
    show_alert: bool
    url: str | None
    answered_at: float


@dataclass
class WebhookConfig:
    """Webhook configuration for a bot."""

    url: str
    secret_token: str | None = None
    max_connections: int = 40
    allowed_updates: list[str] | None = None
    ip_address: str | None = None
    has_custom_certificate: bool = False
    last_error_date: int | None = None
    last_error_message: str | None = None
    last_synchronization_error_date: int | None = None


@dataclass
class BotState:
    """State for a single bot instance.

    Manages webhook configuration, pending updates, and message history
    for a specific bot token.
    """

    token: str
    bot_user: User
    webhook_url: str | None = None
    webhook_secret: str | None = None
    webhook_config: WebhookConfig | None = None
    pending_updates: list[StoredUpdate] = field(default_factory=list)
    message_history: list[StoredMessage] = field(default_factory=list)
    chat_actions: dict[int, ChatAction] = field(default_factory=dict)
    answered_callbacks: dict[str, AnsweredCallback] = field(default_factory=dict)

    def add_update(self, update: StoredUpdate) -> None:
        """Add an update to the pending updates queue.

        Args:
            update: The update to add.
        """
        self.pending_updates.append(update)

    def get_pending_updates(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[StoredUpdate]:
        """Get pending updates, optionally filtered by offset and limit.

        Args:
            limit: Maximum number of updates to return.
            offset: Only return updates with update_id >= offset.

        Returns:
            List of pending updates matching the criteria.
        """
        updates = self.pending_updates

        if offset is not None:
            updates = [u for u in updates if u.update_id >= offset]

        if limit is not None:
            updates = updates[:limit]

        return updates

    def mark_updates_delivered(self, up_to_update_id: int) -> None:
        """Mark all updates up to the given update_id as delivered.

        Args:
            up_to_update_id: Mark all updates with update_id <= this as delivered.
        """
        for update in self.pending_updates:
            if update.update_id <= up_to_update_id:
                update.delivered = True

    def clear_delivered_updates(self) -> None:
        """Remove all updates that have been marked as delivered."""
        self.pending_updates = [u for u in self.pending_updates if not u.delivered]

    def add_message(self, message: StoredMessage) -> None:
        """Add a message to the history.

        Args:
            message: The message to store.
        """
        self.message_history.append(message)

    def get_message(self, chat_id: int, message_id: int) -> StoredMessage | None:
        """Retrieve a specific message from history.

        Args:
            chat_id: The chat ID where the message was sent.
            message_id: The message ID to find.

        Returns:
            The stored message if found, None otherwise.
        """
        for msg in self.message_history:
            if msg.chat_id == chat_id and msg.message_id == message_id:
                return msg
        return None

    def get_messages_for_chat(self, chat_id: int, limit: int | None = None) -> list[StoredMessage]:
        """Get messages for a specific chat.

        Args:
            chat_id: The chat ID to get messages for.
            limit: Maximum number of messages to return (most recent first).

        Returns:
            List of messages for the chat, sorted by date descending.
        """
        messages = [m for m in self.message_history if m.chat_id == chat_id]
        messages.sort(key=lambda m: m.date, reverse=True)
        if limit is not None:
            messages = messages[:limit]
        return messages

    def set_chat_action(self, chat_id: int, action: str) -> None:
        """Set the current action for a chat (e.g., typing).

        Args:
            chat_id: The chat ID.
            action: The action string (e.g., "typing", "upload_photo").
        """
        self.chat_actions[chat_id] = ChatAction(
            chat_id=chat_id,
            action=action,
            timestamp=time.time(),
        )

    def get_chat_action(self, chat_id: int) -> ChatAction | None:
        """Get the current action for a chat if it exists and is recent.

        Args:
            chat_id: The chat ID.

        Returns:
            The chat action if it exists and is less than 5 seconds old, None otherwise.
        """
        action = self.chat_actions.get(chat_id)
        if action is None:
            return None
        # Chat actions expire after 5 seconds
        if time.time() - action.timestamp > 5:
            del self.chat_actions[chat_id]
            return None
        return action


def _extract_bot_id_from_token(token: str) -> int:
    """Extract the bot ID from a token string.

    Telegram bot tokens have the format: "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    where the part before the colon is the bot's user ID.

    Args:
        token: The bot token string.

    Returns:
        The bot user ID extracted from the token.

    Raises:
        ValueError: If the token format is invalid.
    """
    if ":" not in token:
        raise ValueError(f"Invalid token format: {token}")

    bot_id_str = token.split(":")[0]
    try:
        return int(bot_id_str)
    except ValueError as e:
        raise ValueError(f"Invalid bot ID in token: {bot_id_str}") from e


def _create_bot_user(token: str) -> User:
    """Create a User object for a bot based on its token.

    Args:
        token: The bot token.

    Returns:
        A User object representing the bot.
    """
    bot_id = _extract_bot_id_from_token(token)
    return User(
        id=bot_id,
        is_bot=True,
        first_name="Test Bot",
        username=f"test_bot_{bot_id}",
    )


class ServerState:
    """Main server state managing all bots and shared resources.

    This is the central state class that holds all bot states, the ID generator,
    and file storage. It uses asyncio.Lock for thread-safe operations.
    """

    def __init__(self) -> None:
        """Initialize the server state."""
        self._bots: dict[str, BotState] = {}
        self._id_generator = IDGenerator()
        self._file_storage = FileStorage()
        self._lock = asyncio.Lock()

    @property
    def bots(self) -> dict[str, BotState]:
        """Get the dictionary of all bot states."""
        return self._bots

    @property
    def id_generator(self) -> IDGenerator:
        """Get the ID generator instance."""
        return self._id_generator

    @property
    def file_storage(self) -> FileStorage:
        """Get the file storage instance."""
        return self._file_storage

    async def get_or_create_bot(self, token: str) -> BotState:
        """Get an existing bot state or create a new one.

        This method auto-creates a bot on first access, simulating Telegram's
        behavior where any valid token is accepted.

        Args:
            token: The bot token.

        Returns:
            The BotState for the given token.
        """
        async with self._lock:
            if token not in self._bots:
                bot_user = _create_bot_user(token)
                self._bots[token] = BotState(
                    token=token,
                    bot_user=bot_user,
                )
            return self._bots[token]

    def get_bot(self, token: str) -> BotState | None:
        """Get a bot state by token if it exists.

        Args:
            token: The bot token.

        Returns:
            The BotState if found, None otherwise.
        """
        return self._bots.get(token)

    async def add_message(
        self,
        token: str,
        message: Message,
        is_bot_message: bool = True,
    ) -> StoredMessage:
        """Add a message to a bot's history.

        Args:
            token: The bot token.
            message: The Message object to store.
            is_bot_message: Whether this message was sent by the bot.

        Returns:
            The stored message.
        """
        bot_state = await self.get_or_create_bot(token)

        stored = StoredMessage(
            message_id=message.message_id,
            chat_id=message.chat.id,
            from_user_id=message.from_user.id if message.from_user else None,
            text=message.text,
            date=message.date,
            is_bot_message=is_bot_message,
            raw_message=message,
        )

        async with self._lock:
            bot_state.add_message(stored)

        return stored

    async def add_update(self, token: str, update: Update) -> StoredUpdate:
        """Add an update to a bot's pending updates.

        Args:
            token: The bot token.
            update: The Update object to queue.

        Returns:
            The stored update.
        """
        bot_state = await self.get_or_create_bot(token)

        stored = StoredUpdate(
            update_id=update.update_id,
            update=update,
            delivered=False,
        )

        async with self._lock:
            bot_state.add_update(stored)

        return stored

    async def reset(self) -> None:
        """Reset all server state (for testing purposes)."""
        async with self._lock:
            self._bots.clear()
            self._id_generator.reset()
            self._file_storage.clear()
