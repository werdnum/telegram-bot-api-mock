"""Integration tests for client message API endpoints."""

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app
from telegram_bot_api_mock.dependencies import reset_state


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before and after each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def client():
    """Create a test client for client message tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestClientSendMessage:
    """Tests for the client sendMessage endpoint."""

    def test_send_message_creates_update_for_bot(self, client: TestClient):
        """Test that sendMessage creates an update for the bot."""
        response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello, bot!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["update_id"] == 1
        assert data["result"]["message"]["text"] == "Hello, bot!"
        assert data["result"]["message"]["chat"]["id"] == 100
        # From user should be the default test user
        assert data["result"]["message"]["from"]["id"] == 1
        assert data["result"]["message"]["from"]["is_bot"] is False
        assert data["result"]["message"]["from"]["first_name"] == "Test User"

    def test_send_message_with_custom_from_user(self, client: TestClient):
        """Test sendMessage with a custom from_user."""
        response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello from custom user!",
                "from_user": {
                    "id": 42,
                    "is_bot": False,
                    "first_name": "Custom",
                    "last_name": "User",
                    "username": "customuser",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["from"]["id"] == 42
        assert data["result"]["message"]["from"]["first_name"] == "Custom"
        assert data["result"]["message"]["from"]["last_name"] == "User"
        assert data["result"]["message"]["from"]["username"] == "customuser"

    def test_send_message_update_available_via_get_updates(self, client: TestClient):
        """Test that the update created by sendMessage is available via bot getUpdates."""
        # Send a message as the client
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello, bot!",
            },
        )

        # Bot retrieves updates
        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 1
        assert data["result"][0]["message"]["text"] == "Hello, bot!"


class TestClientSendCommand:
    """Tests for the client sendCommand endpoint."""

    def test_send_command_creates_update_with_command_entity(self, client: TestClient):
        """Test that sendCommand creates an update with command entity."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["text"] == "/start"
        # Should have a bot_command entity
        entities = data["result"]["message"]["entities"]
        assert entities is not None
        assert len(entities) == 1
        assert entities[0]["type"] == "bot_command"
        assert entities[0]["offset"] == 0
        assert entities[0]["length"] == 6  # len("/start")

    def test_send_command_with_arguments(self, client: TestClient):
        """Test sendCommand with arguments after the command."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/help topic",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["text"] == "/help topic"
        # Entity should only cover "/help"
        entities = data["result"]["message"]["entities"]
        assert entities[0]["length"] == 5  # len("/help")

    def test_send_command_must_start_with_slash(self, client: TestClient):
        """Test that sendCommand rejects commands not starting with /."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "start",  # Missing /
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "must start with /" in data["description"]

    def test_send_command_update_available_via_get_updates(self, client: TestClient):
        """Test that command updates are available via bot getUpdates."""
        # Send a command as the client
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Bot retrieves updates
        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        message = data["result"][0]["message"]
        assert message["text"] == "/start"
        assert message["entities"][0]["type"] == "bot_command"


class TestClientGetUpdates:
    """Tests for the client getUpdates endpoint."""

    def test_get_updates_returns_bot_messages(self, client: TestClient):
        """Test that getUpdates returns messages sent by the bot."""
        # Bot sends a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello, user!"},
        )

        # Client retrieves bot messages
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 1
        assert data["result"][0]["text"] == "Hello, user!"
        # Message should be from the bot
        assert data["result"][0]["from"]["is_bot"] is True

    def test_get_updates_excludes_user_messages(self, client: TestClient):
        """Test that getUpdates does not return user messages."""
        # User sends a message (simulated)
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello from user!",
            },
        )

        # Bot sends a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello from bot!"},
        )

        # Client retrieves bot messages - should only see bot's message
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        # Should only contain the bot's message
        assert len(data["result"]) == 1
        assert data["result"][0]["text"] == "Hello from bot!"

    def test_get_updates_empty_for_different_chat(self, client: TestClient):
        """Test that getUpdates returns empty for different chat."""
        # Bot sends a message to chat 100
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello!"},
        )

        # Client checks chat 200 - should be empty
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 200},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 0


class TestClientGetUpdatesHistory:
    """Tests for the client getUpdatesHistory endpoint."""

    def test_get_updates_history_returns_all_updates(self, client: TestClient):
        """Test that getUpdatesHistory returns all updates for a bot."""
        # Send multiple messages
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "First message",
            },
        )
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Second message",
            },
        )

        # Get updates history
        response = client.get(
            "/client/getUpdatesHistory",
            params={"bot_token": TEST_TOKEN},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 2
        assert data["result"][0]["message"]["text"] == "First message"
        assert data["result"][1]["message"]["text"] == "Second message"

    def test_get_updates_history_includes_commands(self, client: TestClient):
        """Test that getUpdatesHistory includes command updates."""
        # Send a regular message
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello",
            },
        )

        # Send a command
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Get updates history
        response = client.get(
            "/client/getUpdatesHistory",
            params={"bot_token": TEST_TOKEN},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        # Second update should be the command
        assert data["result"][1]["message"]["text"] == "/start"
        assert data["result"][1]["message"]["entities"][0]["type"] == "bot_command"
