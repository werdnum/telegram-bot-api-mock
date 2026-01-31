"""Integration tests for bot message API endpoints using python-telegram-bot."""

import pytest
from fastapi.testclient import TestClient
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.error import BadRequest


class TestSendMessage:
    """Tests for the sendMessage endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_creates_and_returns_message(self, bot: Bot):
        """Test that sendMessage creates a message and returns it."""
        message = await bot.send_message(chat_id=100, text="Hello, World!")

        assert message.message_id == 1
        assert message.text == "Hello, World!"
        assert message.chat.id == 100
        assert message.from_user is not None
        assert message.from_user.id == 123456789
        assert message.from_user.is_bot is True

    @pytest.mark.asyncio
    async def test_send_message_increments_message_id(self, bot: Bot):
        """Test that message IDs increment for each message."""
        message1 = await bot.send_message(chat_id=100, text="First message")
        message2 = await bot.send_message(chat_id=100, text="Second message")

        assert message1.message_id == 1
        assert message2.message_id == 2

    @pytest.mark.asyncio
    async def test_send_message_with_reply_to(self, bot: Bot):
        """Test that sendMessage can reply to another message."""
        # First, send a message to reply to
        original = await bot.send_message(chat_id=100, text="Original message")

        # Now send a reply
        reply = await bot.send_message(
            chat_id=100,
            text="Reply message",
            reply_to_message_id=original.message_id,
        )

        assert reply.reply_to_message is not None
        assert reply.reply_to_message.message_id == original.message_id

    @pytest.mark.asyncio
    async def test_send_message_with_inline_keyboard(self, bot: Bot):
        """Test sendMessage with inline keyboard markup."""
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Button 1", callback_data="btn1")],
                [InlineKeyboardButton("Button 2", url="https://example.com")],
            ]
        )

        message = await bot.send_message(
            chat_id=100,
            text="Message with keyboard",
            reply_markup=keyboard,
        )

        assert message.reply_markup is not None
        assert len(message.reply_markup.inline_keyboard) == 2

    @pytest.mark.asyncio
    async def test_send_message_json_body(self, client: TestClient):
        """Test that sendMessage works with JSON body (raw client)."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            json={"chat_id": 100, "text": "Hello JSON"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["text"] == "Hello JSON"


class TestEditMessageText:
    """Tests for the editMessageText endpoint."""

    @pytest.mark.asyncio
    async def test_edit_message_text_updates_message(self, bot: Bot):
        """Test that editMessageText updates the message text."""
        # First send a message
        original = await bot.send_message(chat_id=100, text="Original text")

        # Edit the message
        edited = await bot.edit_message_text(
            text="Updated text",
            chat_id=100,
            message_id=original.message_id,
        )

        assert isinstance(edited, Message)
        assert edited.text == "Updated text"
        assert edited.edit_date is not None

    @pytest.mark.asyncio
    async def test_edit_message_text_not_found(self, bot: Bot):
        """Test editMessageText raises error for non-existent message."""
        with pytest.raises(BadRequest) as exc_info:
            await bot.edit_message_text(
                text="Updated text",
                chat_id=100,
                message_id=999,
            )

        assert "not found" in str(exc_info.value).lower()


class TestDeleteMessage:
    """Tests for the deleteMessage endpoint."""

    @pytest.mark.asyncio
    async def test_delete_message_removes_message(self, bot: Bot):
        """Test that deleteMessage removes the message."""
        # First send a message
        message = await bot.send_message(chat_id=100, text="Message to delete")

        # Delete the message
        result = await bot.delete_message(chat_id=100, message_id=message.message_id)

        assert result is True

        # Verify message is gone by trying to edit it
        with pytest.raises(BadRequest):
            await bot.edit_message_text(
                text="Try to edit",
                chat_id=100,
                message_id=message.message_id,
            )

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, bot: Bot):
        """Test deleteMessage raises error for non-existent message."""
        with pytest.raises(BadRequest):
            await bot.delete_message(chat_id=100, message_id=999)


class TestGetMe:
    """Tests for the getMe endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_returns_bot_user(self, bot: Bot):
        """Test that getMe returns the bot user."""
        me = await bot.get_me()

        assert me.id == 123456789
        assert me.is_bot is True
        assert me.first_name == "Test Bot"
        assert me.username == "test_bot_123456789"


class TestGetUpdates:
    """Tests for the getUpdates endpoint."""

    @pytest.mark.asyncio
    async def test_get_updates_returns_empty_list_initially(self, bot: Bot):
        """Test that getUpdates returns an empty list when no updates exist."""
        updates = await bot.get_updates()

        # PTB returns a tuple for empty lists
        assert len(updates) == 0

    @pytest.mark.asyncio
    async def test_get_updates_with_parameters(self, bot: Bot):
        """Test that getUpdates works with optional parameters."""
        updates = await bot.get_updates(offset=0, limit=10, timeout=0)

        # PTB returns a tuple for empty lists
        assert len(updates) == 0


class TestJSONBodySupport:
    """Tests for JSON body support and error handling across endpoints."""

    def test_send_message_json_body_invalid_json(self, client: TestClient):
        """Test that sendMessage returns proper error for invalid JSON."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            content="{invalid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "invalid JSON" in data["description"]

    def test_send_message_json_body_validation_error(self, client: TestClient):
        """Test that sendMessage returns proper error for validation failures."""
        from tests.conftest import TEST_TOKEN

        # Missing required 'text' field
        response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            json={"chat_id": 100},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "validation error" in data["description"]

    def test_edit_message_text_json_body(self, client: TestClient):
        """Test that editMessageText works with JSON body."""
        from tests.conftest import TEST_TOKEN

        # First create a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            json={"chat_id": 100, "text": "Original"},
        )

        # Now edit it with JSON body
        response = client.post(
            f"/bot{TEST_TOKEN}/editMessageText",
            json={"chat_id": 100, "message_id": 1, "text": "Edited via JSON"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["text"] == "Edited via JSON"

    def test_delete_message_json_body(self, client: TestClient):
        """Test that deleteMessage works with JSON body."""
        from tests.conftest import TEST_TOKEN

        # First create a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            json={"chat_id": 100, "text": "To be deleted"},
        )

        # Delete it with JSON body
        response = client.post(
            f"/bot{TEST_TOKEN}/deleteMessage",
            json={"chat_id": 100, "message_id": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

    def test_get_updates_json_body(self, client: TestClient):
        """Test that getUpdates works with JSON body."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/getUpdates",
            json={"offset": 0, "limit": 10, "timeout": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == []

    def test_set_webhook_json_body(self, client: TestClient):
        """Test that setWebhook works with JSON body."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            json={"url": "https://example.com/webhook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_delete_webhook_json_body(self, client: TestClient):
        """Test that deleteWebhook works with JSON body."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/deleteWebhook",
            json={"drop_pending_updates": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_send_chat_action_json_body(self, client: TestClient):
        """Test that sendChatAction works with JSON body."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            json={"chat_id": 100, "action": "typing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_send_chat_action_json_body_invalid_json(self, client: TestClient):
        """Test that sendChatAction returns proper error for invalid JSON."""
        from tests.conftest import TEST_TOKEN

        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            content="{not valid json}",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "invalid JSON" in data["description"]

    def test_send_chat_action_json_body_validation_error(self, client: TestClient):
        """Test that sendChatAction returns proper error for validation failures."""
        from tests.conftest import TEST_TOKEN

        # Missing required 'action' field
        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            json={"chat_id": 100},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "validation error" in data["description"]
