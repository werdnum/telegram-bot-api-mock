"""Integration tests for bot webhook API endpoints."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app
from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import Message, Update
from telegram_bot_api_mock.models.telegram_types import Chat, User


@pytest.fixture
def client():
    """Create a test client for bot webhook tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestSetWebhook:
    """Tests for the setWebhook endpoint."""

    def test_set_webhook_stores_url(self, client: TestClient):
        """Test that setWebhook stores the webhook URL."""
        response = client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": "https://example.com/webhook"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

        # Verify webhook is stored by calling getWebhookInfo
        info_response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")
        info_data = info_response.json()
        assert info_data["result"]["url"] == "https://example.com/webhook"

    def test_set_webhook_with_secret_token(self, client: TestClient):
        """Test that setWebhook stores the secret token."""
        response = client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={
                "url": "https://example.com/webhook",
                "secret_token": "my_secret_token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

        # Verify in state
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert bot_state.webhook_secret == "my_secret_token"

    def test_set_webhook_with_max_connections(self, client: TestClient):
        """Test that setWebhook stores max_connections."""
        response = client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={
                "url": "https://example.com/webhook",
                "max_connections": "100",
            },
        )

        assert response.status_code == 200

        info_response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")
        info_data = info_response.json()
        assert info_data["result"]["max_connections"] == 100

    def test_set_webhook_drop_pending_updates(self, client: TestClient):
        """Test that setWebhook can drop pending updates."""
        # First, we need to add some pending updates to the bot state
        state = get_state()

        async def add_update():
            update = Update(
                update_id=1,
                message=Message(
                    message_id=1,
                    date=1234567890,
                    chat=Chat(id=100, type="private"),
                    from_user=User(id=100, is_bot=False, first_name="Test"),
                    text="Test message",
                ),
            )
            await state.add_update(TEST_TOKEN, update)

        asyncio.new_event_loop().run_until_complete(add_update())

        # Verify update exists
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 1

        # Set webhook with drop_pending_updates=true
        response = client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={
                "url": "https://example.com/webhook",
                "drop_pending_updates": "true",
            },
        )

        assert response.status_code == 200

        # Verify updates were dropped
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 0


class TestDeleteWebhook:
    """Tests for the deleteWebhook endpoint."""

    def test_delete_webhook_removes_url(self, client: TestClient):
        """Test that deleteWebhook removes the webhook URL."""
        # First set a webhook
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": "https://example.com/webhook"},
        )

        # Verify it's set
        info_response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")
        assert info_response.json()["result"]["url"] == "https://example.com/webhook"

        # Delete the webhook
        response = client.post(f"/bot{TEST_TOKEN}/deleteWebhook", data={})

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

        # Verify it's gone
        info_response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")
        assert info_response.json()["result"]["url"] == ""

    def test_delete_webhook_drop_pending_updates(self, client: TestClient):
        """Test that deleteWebhook can drop pending updates."""
        state = get_state()

        async def add_update():
            update = Update(
                update_id=1,
                message=Message(
                    message_id=1,
                    date=1234567890,
                    chat=Chat(id=100, type="private"),
                    from_user=User(id=100, is_bot=False, first_name="Test"),
                    text="Test message",
                ),
            )
            await state.add_update(TEST_TOKEN, update)

        asyncio.new_event_loop().run_until_complete(add_update())

        # Verify update exists
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 1

        # Delete webhook with drop_pending_updates=true
        response = client.post(
            f"/bot{TEST_TOKEN}/deleteWebhook",
            data={"drop_pending_updates": "true"},
        )

        assert response.status_code == 200

        # Verify updates were dropped
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 0


class TestGetWebhookInfo:
    """Tests for the getWebhookInfo endpoint."""

    def test_get_webhook_info_empty(self, client: TestClient):
        """Test getWebhookInfo when no webhook is set."""
        response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["url"] == ""
        assert data["result"]["has_custom_certificate"] is False
        assert data["result"]["pending_update_count"] == 0

    def test_get_webhook_info_with_webhook(self, client: TestClient):
        """Test getWebhookInfo when webhook is set."""
        # Set a webhook
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={
                "url": "https://example.com/webhook",
                "max_connections": "50",
            },
        )

        response = client.get(f"/bot{TEST_TOKEN}/getWebhookInfo")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["url"] == "https://example.com/webhook"
        assert data["result"]["max_connections"] == 50
        assert data["result"]["has_custom_certificate"] is False

    def test_get_webhook_info_post_method(self, client: TestClient):
        """Test that getWebhookInfo works with POST method too."""
        response = client.post(f"/bot{TEST_TOKEN}/getWebhookInfo")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


class TestAnswerCallbackQuery:
    """Tests for the answerCallbackQuery endpoint."""

    def test_answer_callback_query_stores_answer(self, client: TestClient):
        """Test that answerCallbackQuery stores the answer."""
        response = client.post(
            f"/bot{TEST_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": "test_callback_123",
                "text": "Button clicked!",
                "show_alert": "true",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

        # Verify answer is stored in state
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert "test_callback_123" in bot_state.answered_callbacks
        answered = bot_state.answered_callbacks["test_callback_123"]
        assert answered.text == "Button clicked!"
        assert answered.show_alert is True

    def test_answer_callback_query_minimal(self, client: TestClient):
        """Test answerCallbackQuery with minimal parameters."""
        response = client.post(
            f"/bot{TEST_TOKEN}/answerCallbackQuery",
            data={"callback_query_id": "test_callback_456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

        # Verify answer is stored
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert "test_callback_456" in bot_state.answered_callbacks
        answered = bot_state.answered_callbacks["test_callback_456"]
        assert answered.text is None
        assert answered.show_alert is False

    def test_answer_callback_query_with_url(self, client: TestClient):
        """Test answerCallbackQuery with URL parameter."""
        response = client.post(
            f"/bot{TEST_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": "test_callback_789",
                "url": "https://example.com/game",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

        # Verify URL is stored
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        answered = bot_state.answered_callbacks["test_callback_789"]
        assert answered.url == "https://example.com/game"
