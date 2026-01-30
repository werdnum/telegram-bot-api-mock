"""Unit tests for state management modules."""

import pytest

from telegram_bot_api_mock.dependencies import get_bot_state, get_state, reset_state
from telegram_bot_api_mock.models import Chat, Message, Update, User
from telegram_bot_api_mock.state import (
    BotState,
    FileStorage,
    IDGenerator,
    ServerState,
    StoredMessage,
    StoredUpdate,
)


class TestIDGenerator:
    """Tests for the IDGenerator class."""

    @pytest.fixture
    def generator(self) -> IDGenerator:
        """Create a fresh IDGenerator for each test."""
        return IDGenerator()

    async def test_next_message_id_sequential(self, generator: IDGenerator) -> None:
        """Test that message IDs are generated sequentially starting from 1."""
        assert await generator.next_message_id() == 1
        assert await generator.next_message_id() == 2
        assert await generator.next_message_id() == 3

    async def test_next_update_id_sequential(self, generator: IDGenerator) -> None:
        """Test that update IDs are generated sequentially starting from 1."""
        assert await generator.next_update_id() == 1
        assert await generator.next_update_id() == 2
        assert await generator.next_update_id() == 3

    async def test_next_file_id_sequential(self, generator: IDGenerator) -> None:
        """Test that file IDs are generated sequentially starting from 1."""
        assert await generator.next_file_id() == 1
        assert await generator.next_file_id() == 2
        assert await generator.next_file_id() == 3

    async def test_next_callback_query_id_sequential(self, generator: IDGenerator) -> None:
        """Test that callback query IDs are generated sequentially starting from 1."""
        assert await generator.next_callback_query_id() == 1
        assert await generator.next_callback_query_id() == 2
        assert await generator.next_callback_query_id() == 3

    async def test_counters_are_independent(self, generator: IDGenerator) -> None:
        """Test that different ID counters are independent of each other."""
        assert await generator.next_message_id() == 1
        assert await generator.next_update_id() == 1
        assert await generator.next_file_id() == 1
        assert await generator.next_message_id() == 2
        assert await generator.next_update_id() == 2

    def test_reset_clears_all_counters(self, generator: IDGenerator) -> None:
        """Test that reset() clears all counters."""
        # We can't test async methods here, but we can verify reset works
        generator._message_id = 10
        generator._update_id = 20
        generator._file_id = 30
        generator._callback_query_id = 40

        generator.reset()

        assert generator._message_id == 0
        assert generator._update_id == 0
        assert generator._file_id == 0
        assert generator._callback_query_id == 0


class TestFileStorage:
    """Tests for the FileStorage class."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        """Create a fresh FileStorage for each test."""
        return FileStorage()

    def test_store_file_returns_unique_id(self, storage: FileStorage) -> None:
        """Test that store_file returns a unique file ID."""
        file_id1 = storage.store_file(b"content1", "file1.txt", "text/plain")
        file_id2 = storage.store_file(b"content2", "file2.txt", "text/plain")

        assert file_id1 != file_id2
        assert isinstance(file_id1, str)
        assert isinstance(file_id2, str)

    def test_get_file_returns_stored_content(self, storage: FileStorage) -> None:
        """Test that get_file returns the correct content and metadata."""
        content = b"Hello, World!"
        filename = "greeting.txt"
        mime_type = "text/plain"

        file_id = storage.store_file(content, filename, mime_type)
        result = storage.get_file(file_id)

        assert result is not None
        assert result[0] == content
        assert result[1] == filename
        assert result[2] == mime_type

    def test_get_file_returns_none_for_unknown_id(self, storage: FileStorage) -> None:
        """Test that get_file returns None for unknown file IDs."""
        result = storage.get_file("nonexistent-id")
        assert result is None

    def test_delete_file_removes_file(self, storage: FileStorage) -> None:
        """Test that delete_file removes the file from storage."""
        file_id = storage.store_file(b"content", "file.txt", "text/plain")

        assert storage.delete_file(file_id) is True
        assert storage.get_file(file_id) is None

    def test_delete_file_returns_false_for_unknown_id(self, storage: FileStorage) -> None:
        """Test that delete_file returns False for unknown file IDs."""
        assert storage.delete_file("nonexistent-id") is False

    def test_clear_removes_all_files(self, storage: FileStorage) -> None:
        """Test that clear() removes all files from storage."""
        storage.store_file(b"content1", "file1.txt", "text/plain")
        storage.store_file(b"content2", "file2.txt", "text/plain")

        storage.clear()

        assert storage.count == 0

    def test_count_returns_number_of_files(self, storage: FileStorage) -> None:
        """Test that count returns the correct number of stored files."""
        assert storage.count == 0

        storage.store_file(b"content1", "file1.txt", "text/plain")
        assert storage.count == 1

        storage.store_file(b"content2", "file2.txt", "text/plain")
        assert storage.count == 2


class TestBotState:
    """Tests for the BotState class."""

    @pytest.fixture
    def bot_user(self) -> User:
        """Create a test bot user."""
        return User(
            id=123456789,
            is_bot=True,
            first_name="Test Bot",
            username="test_bot",
        )

    @pytest.fixture
    def bot_state(self, bot_user: User) -> BotState:
        """Create a fresh BotState for each test."""
        return BotState(
            token="123456789:ABC-DEF1234",
            bot_user=bot_user,
        )

    @pytest.fixture
    def sample_message(self) -> Message:
        """Create a sample message for testing."""
        return Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=100, type="private", first_name="Test User"),
            text="Hello!",
        )

    @pytest.fixture
    def sample_update(self, sample_message: Message) -> Update:
        """Create a sample update for testing."""
        return Update(
            update_id=1,
            message=sample_message,
        )

    def test_initial_state(self, bot_state: BotState) -> None:
        """Test that BotState initializes with correct defaults."""
        assert bot_state.webhook_url is None
        assert bot_state.webhook_secret is None
        assert bot_state.pending_updates == []
        assert bot_state.message_history == []
        assert bot_state.chat_actions == {}

    def test_add_update(self, bot_state: BotState, sample_update: Update) -> None:
        """Test that updates can be added to the pending queue."""
        stored = StoredUpdate(update_id=1, update=sample_update)
        bot_state.add_update(stored)

        assert len(bot_state.pending_updates) == 1
        assert bot_state.pending_updates[0].update_id == 1

    def test_get_pending_updates_with_offset(
        self, bot_state: BotState, sample_message: Message
    ) -> None:
        """Test that get_pending_updates respects offset."""
        for i in range(1, 4):
            update = Update(update_id=i, message=sample_message)
            bot_state.add_update(StoredUpdate(update_id=i, update=update))

        updates = bot_state.get_pending_updates(offset=2)
        assert len(updates) == 2
        assert updates[0].update_id == 2
        assert updates[1].update_id == 3

    def test_get_pending_updates_with_limit(
        self, bot_state: BotState, sample_message: Message
    ) -> None:
        """Test that get_pending_updates respects limit."""
        for i in range(1, 4):
            update = Update(update_id=i, message=sample_message)
            bot_state.add_update(StoredUpdate(update_id=i, update=update))

        updates = bot_state.get_pending_updates(limit=2)
        assert len(updates) == 2

    def test_mark_updates_delivered(self, bot_state: BotState, sample_message: Message) -> None:
        """Test that updates can be marked as delivered."""
        for i in range(1, 4):
            update = Update(update_id=i, message=sample_message)
            bot_state.add_update(StoredUpdate(update_id=i, update=update))

        bot_state.mark_updates_delivered(2)

        assert bot_state.pending_updates[0].delivered is True
        assert bot_state.pending_updates[1].delivered is True
        assert bot_state.pending_updates[2].delivered is False

    def test_clear_delivered_updates(self, bot_state: BotState, sample_message: Message) -> None:
        """Test that delivered updates can be cleared."""
        for i in range(1, 4):
            update = Update(update_id=i, message=sample_message)
            bot_state.add_update(StoredUpdate(update_id=i, update=update))

        bot_state.mark_updates_delivered(2)
        bot_state.clear_delivered_updates()

        assert len(bot_state.pending_updates) == 1
        assert bot_state.pending_updates[0].update_id == 3

    def test_add_message(self, bot_state: BotState, sample_message: Message) -> None:
        """Test that messages can be added to history."""
        stored = StoredMessage(
            message_id=sample_message.message_id,
            chat_id=sample_message.chat.id,
            text=sample_message.text,
            date=sample_message.date,
            is_bot_message=True,
            raw_message=sample_message,
        )
        bot_state.add_message(stored)

        assert len(bot_state.message_history) == 1

    def test_get_message(self, bot_state: BotState, sample_message: Message) -> None:
        """Test that a specific message can be retrieved."""
        stored = StoredMessage(
            message_id=sample_message.message_id,
            chat_id=sample_message.chat.id,
            text=sample_message.text,
            date=sample_message.date,
            is_bot_message=True,
            raw_message=sample_message,
        )
        bot_state.add_message(stored)

        result = bot_state.get_message(
            chat_id=sample_message.chat.id,
            message_id=sample_message.message_id,
        )
        assert result is not None
        assert result.text == "Hello!"

    def test_get_message_returns_none_for_unknown(self, bot_state: BotState) -> None:
        """Test that get_message returns None for unknown messages."""
        result = bot_state.get_message(chat_id=999, message_id=999)
        assert result is None

    def test_get_messages_for_chat(self, bot_state: BotState) -> None:
        """Test that messages can be retrieved by chat ID."""
        chat = Chat(id=100, type="private", first_name="Test User")

        for i in range(3):
            msg = Message(
                message_id=i + 1,
                date=1234567890 + i,
                chat=chat,
                text=f"Message {i + 1}",
            )
            stored = StoredMessage(
                message_id=msg.message_id,
                chat_id=msg.chat.id,
                text=msg.text,
                date=msg.date,
                is_bot_message=True,
                raw_message=msg,
            )
            bot_state.add_message(stored)

        messages = bot_state.get_messages_for_chat(chat_id=100, limit=2)
        assert len(messages) == 2
        # Should be sorted by date descending
        assert messages[0].text == "Message 3"
        assert messages[1].text == "Message 2"

    def test_set_chat_action(self, bot_state: BotState) -> None:
        """Test that chat actions can be set."""
        bot_state.set_chat_action(chat_id=100, action="typing")

        action = bot_state.chat_actions.get(100)
        assert action is not None
        assert action.action == "typing"

    def test_get_chat_action(self, bot_state: BotState) -> None:
        """Test that chat actions can be retrieved."""
        bot_state.set_chat_action(chat_id=100, action="typing")

        action = bot_state.get_chat_action(chat_id=100)
        assert action is not None
        assert action.action == "typing"

    def test_get_chat_action_returns_none_for_unknown(self, bot_state: BotState) -> None:
        """Test that get_chat_action returns None for unknown chats."""
        action = bot_state.get_chat_action(chat_id=999)
        assert action is None


class TestServerState:
    """Tests for the ServerState class."""

    @pytest.fixture
    def server_state(self) -> ServerState:
        """Create a fresh ServerState for each test."""
        return ServerState()

    async def test_get_or_create_bot_creates_new_bot(self, server_state: ServerState) -> None:
        """Test that get_or_create_bot creates a new bot on first access."""
        token = "123456789:ABC-DEF1234"
        bot_state = await server_state.get_or_create_bot(token)

        assert bot_state is not None
        assert bot_state.token == token
        assert bot_state.bot_user.id == 123456789
        assert bot_state.bot_user.is_bot is True

    async def test_get_or_create_bot_returns_existing_bot(self, server_state: ServerState) -> None:
        """Test that get_or_create_bot returns the same bot on subsequent calls."""
        token = "123456789:ABC-DEF1234"
        bot_state1 = await server_state.get_or_create_bot(token)
        bot_state2 = await server_state.get_or_create_bot(token)

        assert bot_state1 is bot_state2

    async def test_get_or_create_bot_extracts_bot_id_from_token(
        self, server_state: ServerState
    ) -> None:
        """Test that the bot ID is correctly extracted from the token."""
        token = "987654321:XYZ-abc1234"
        bot_state = await server_state.get_or_create_bot(token)

        assert bot_state.bot_user.id == 987654321

    def test_get_bot_returns_none_for_unknown_token(self, server_state: ServerState) -> None:
        """Test that get_bot returns None for unknown tokens."""
        bot_state = server_state.get_bot("unknown:token")
        assert bot_state is None

    async def test_get_bot_returns_existing_bot(self, server_state: ServerState) -> None:
        """Test that get_bot returns an existing bot."""
        token = "123456789:ABC-DEF1234"
        await server_state.get_or_create_bot(token)

        bot_state = server_state.get_bot(token)
        assert bot_state is not None
        assert bot_state.token == token

    async def test_add_message_stores_message(self, server_state: ServerState) -> None:
        """Test that add_message stores a message in bot history."""
        token = "123456789:ABC-DEF1234"
        message = Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=100, type="private", first_name="Test User"),
            text="Hello!",
        )

        stored = await server_state.add_message(token, message, is_bot_message=True)

        assert stored.message_id == 1
        assert stored.text == "Hello!"
        assert stored.is_bot_message is True

        bot_state = server_state.get_bot(token)
        assert bot_state is not None
        assert len(bot_state.message_history) == 1

    async def test_add_update_stores_update(self, server_state: ServerState) -> None:
        """Test that add_update stores an update in bot's pending queue."""
        token = "123456789:ABC-DEF1234"
        message = Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=100, type="private", first_name="Test User"),
            text="Hello!",
        )
        update = Update(update_id=1, message=message)

        stored = await server_state.add_update(token, update)

        assert stored.update_id == 1
        assert stored.delivered is False

        bot_state = server_state.get_bot(token)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 1

    async def test_reset_clears_all_state(self, server_state: ServerState) -> None:
        """Test that reset() clears all server state."""
        token = "123456789:ABC-DEF1234"
        await server_state.get_or_create_bot(token)
        server_state.file_storage.store_file(b"test", "test.txt", "text/plain")

        await server_state.reset()

        assert len(server_state.bots) == 0
        assert server_state.file_storage.count == 0

    def test_id_generator_property(self, server_state: ServerState) -> None:
        """Test that id_generator property returns the generator."""
        assert server_state.id_generator is not None
        assert isinstance(server_state.id_generator, IDGenerator)

    def test_file_storage_property(self, server_state: ServerState) -> None:
        """Test that file_storage property returns the storage."""
        assert server_state.file_storage is not None
        assert isinstance(server_state.file_storage, FileStorage)


class TestDependencies:
    """Tests for the dependency injection functions."""

    def test_get_state_returns_server_state(self) -> None:
        """Test that get_state returns a ServerState instance."""
        reset_state()  # Start with fresh state
        state = get_state()

        assert state is not None
        assert isinstance(state, ServerState)

    def test_get_state_returns_same_instance(self) -> None:
        """Test that get_state returns the same instance on repeated calls."""
        reset_state()  # Start with fresh state
        state1 = get_state()
        state2 = get_state()

        assert state1 is state2

    def test_reset_state_creates_new_instance(self) -> None:
        """Test that reset_state creates a new ServerState instance."""
        state1 = get_state()
        reset_state()
        state2 = get_state()

        assert state1 is not state2

    async def test_get_bot_state_creates_bot(self) -> None:
        """Test that get_bot_state creates a bot on first access."""
        reset_state()  # Start with fresh state
        token = "123456789:ABC-DEF1234"

        bot_state = await get_bot_state(token)

        assert bot_state is not None
        assert bot_state.token == token

    async def test_get_bot_state_uses_provided_state(self) -> None:
        """Test that get_bot_state uses the provided ServerState."""
        custom_state = ServerState()
        token = "123456789:ABC-DEF1234"

        await get_bot_state(token, custom_state)

        assert token in custom_state.bots
