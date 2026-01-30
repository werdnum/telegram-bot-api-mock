"""Integration tests for bot message API endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app


@pytest.fixture
def client():
    """Create a test client for bot message tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestSendMessage:
    """Tests for the sendMessage endpoint."""

    def test_send_message_creates_and_returns_message(self, client: TestClient):
        """Test that sendMessage creates a message and returns it."""
        response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello, World!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message_id"] == 1
        assert data["result"]["text"] == "Hello, World!"
        assert data["result"]["chat"]["id"] == 100
        assert data["result"]["from"]["id"] == 123456789
        assert data["result"]["from"]["is_bot"] is True

    def test_send_message_increments_message_id(self, client: TestClient):
        """Test that message IDs increment for each message."""
        response1 = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "First message"},
        )
        response2 = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Second message"},
        )

        assert response1.json()["result"]["message_id"] == 1
        assert response2.json()["result"]["message_id"] == 2

    def test_send_message_with_reply_to(self, client: TestClient):
        """Test that sendMessage can reply to another message."""
        # First, send a message to reply to
        response1 = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Original message"},
        )
        original_id = response1.json()["result"]["message_id"]

        # Now send a reply
        response2 = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Reply message",
                "reply_to_message_id": str(original_id),
            },
        )

        assert response2.status_code == 200
        reply = response2.json()["result"]
        assert reply["reply_to_message"]["message_id"] == original_id

    def test_send_message_with_inline_keyboard(self, client: TestClient):
        """Test sendMessage with inline keyboard markup."""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Button 1", "callback_data": "btn1"}],
                [{"text": "Button 2", "url": "https://example.com"}],
            ]
        }

        response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Message with keyboard",
                "reply_markup": json.dumps(keyboard),
            },
        )

        assert response.status_code == 200
        result = response.json()["result"]
        assert result["reply_markup"] is not None
        assert len(result["reply_markup"]["inline_keyboard"]) == 2


class TestEditMessageText:
    """Tests for the editMessageText endpoint."""

    def test_edit_message_text_updates_message(self, client: TestClient):
        """Test that editMessageText updates the message text."""
        # First send a message
        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Original text"},
        )
        message_id = send_response.json()["result"]["message_id"]

        # Edit the message
        edit_response = client.post(
            f"/bot{TEST_TOKEN}/editMessageText",
            data={"chat_id": "100", "message_id": str(message_id), "text": "Updated text"},
        )

        assert edit_response.status_code == 200
        data = edit_response.json()
        assert data["ok"] is True
        assert data["result"]["text"] == "Updated text"
        assert data["result"]["edit_date"] is not None

    def test_edit_message_text_not_found(self, client: TestClient):
        """Test editMessageText returns error for non-existent message."""
        response = client.post(
            f"/bot{TEST_TOKEN}/editMessageText",
            data={"chat_id": "100", "message_id": "999", "text": "Updated text"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "not found" in data["description"]


class TestDeleteMessage:
    """Tests for the deleteMessage endpoint."""

    def test_delete_message_removes_message(self, client: TestClient):
        """Test that deleteMessage removes the message."""
        # First send a message
        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Message to delete"},
        )
        message_id = send_response.json()["result"]["message_id"]

        # Delete the message
        delete_response = client.post(
            f"/bot{TEST_TOKEN}/deleteMessage",
            data={"chat_id": "100", "message_id": str(message_id)},
        )

        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["ok"] is True
        assert data["result"] is True

        # Verify message is gone by trying to edit it
        edit_response = client.post(
            f"/bot{TEST_TOKEN}/editMessageText",
            data={"chat_id": "100", "message_id": str(message_id), "text": "Try to edit"},
        )
        assert edit_response.json()["ok"] is False

    def test_delete_message_not_found(self, client: TestClient):
        """Test deleteMessage returns error for non-existent message."""
        response = client.post(
            f"/bot{TEST_TOKEN}/deleteMessage",
            data={"chat_id": "100", "message_id": "999"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400


class TestGetMe:
    """Tests for the getMe endpoint."""

    def test_get_me_returns_bot_user(self, client: TestClient):
        """Test that getMe returns the bot user."""
        response = client.get(f"/bot{TEST_TOKEN}/getMe")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["id"] == 123456789
        assert data["result"]["is_bot"] is True
        assert data["result"]["first_name"] == "Test Bot"
        assert data["result"]["username"] == "test_bot_123456789"

    def test_get_me_post_method(self, client: TestClient):
        """Test that getMe works with POST method too."""
        response = client.post(f"/bot{TEST_TOKEN}/getMe")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["is_bot"] is True


class TestGetUpdates:
    """Tests for the getUpdates endpoint."""

    def test_get_updates_returns_empty_list_initially(self, client: TestClient):
        """Test that getUpdates returns an empty list when no updates exist."""
        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == []

    def test_get_updates_post_method(self, client: TestClient):
        """Test that getUpdates works with POST method."""
        response = client.post(f"/bot{TEST_TOKEN}/getUpdates", data={})

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == []


class TestFallbackRoute:
    """Tests for the fallback route."""

    def test_unknown_method_returns_success(self, client: TestClient):
        """Test that unknown methods return ok=True like real Telegram API."""
        response = client.post(f"/bot{TEST_TOKEN}/unknownMethod")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True
