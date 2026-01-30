"""End-to-end integration tests for the full message flow."""

import json

import pytest
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

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
    """Create a test client for e2e tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestE2EPolling:
    """End-to-end tests using polling (getUpdates)."""

    def test_user_sends_message_bot_receives_and_responds(self, client: TestClient):
        """Full flow: user sends message -> bot receives via getUpdates -> bot responds -> user gets response."""
        # Step 1: User sends a message to the bot
        user_response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello, bot!",
            },
        )
        assert user_response.status_code == 200
        update_data = user_response.json()
        assert update_data["ok"] is True
        update_id = update_data["result"]["update_id"]

        # Step 2: Bot fetches updates (simulating bot polling)
        bot_response = client.get(f"/bot{TEST_TOKEN}/getUpdates")
        assert bot_response.status_code == 200
        updates = bot_response.json()["result"]
        assert len(updates) == 1
        assert updates[0]["update_id"] == update_id
        assert updates[0]["message"]["text"] == "Hello, bot!"
        user_chat_id = updates[0]["message"]["chat"]["id"]

        # Step 3: Bot processes the message and sends a response
        bot_reply = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": str(user_chat_id),
                "text": "Hello, user! How can I help you?",
            },
        )
        assert bot_reply.status_code == 200
        assert bot_reply.json()["ok"] is True

        # Step 4: User retrieves the bot's response
        user_check = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": user_chat_id},
        )
        assert user_check.status_code == 200
        bot_messages = user_check.json()["result"]
        assert len(bot_messages) == 1
        assert bot_messages[0]["text"] == "Hello, user! How can I help you?"

    def test_user_sends_command_bot_responds_with_inline_keyboard(self, client: TestClient):
        """Test command flow with inline keyboard response."""
        # Step 1: User sends /start command
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Step 2: Bot fetches and processes the command
        updates = client.get(f"/bot{TEST_TOKEN}/getUpdates").json()["result"]
        assert len(updates) == 1
        assert updates[0]["message"]["entities"][0]["type"] == "bot_command"

        # Step 3: Bot responds with an inline keyboard
        keyboard = {
            "inline_keyboard": [
                [{"text": "Option 1", "callback_data": "opt1"}],
                [{"text": "Option 2", "callback_data": "opt2"}],
            ]
        }
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Welcome! Please choose an option:",
                "reply_markup": json.dumps(keyboard),
            },
        )

        # Step 4: User sees the message with keyboard
        bot_messages = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        ).json()["result"]

        assert len(bot_messages) == 1
        assert bot_messages[0]["text"] == "Welcome! Please choose an option:"
        assert bot_messages[0]["reply_markup"] is not None
        assert len(bot_messages[0]["reply_markup"]["inline_keyboard"]) == 2

    def test_user_clicks_callback_button_bot_handles(self, client: TestClient):
        """Test callback query flow from inline button click."""
        # Step 1: Bot sends a message with inline keyboard
        keyboard = {
            "inline_keyboard": [
                [{"text": "Click Me", "callback_data": "clicked"}],
            ]
        }
        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Click the button:",
                "reply_markup": json.dumps(keyboard),
            },
        )
        message_id = send_response.json()["result"]["message_id"]

        # Step 2: User clicks the button (callback query)
        callback_response = client.post(
            "/client/sendCallback",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "message_id": message_id,
                "callback_data": "clicked",
            },
        )
        assert callback_response.status_code == 200
        callback_data = callback_response.json()
        assert callback_data["ok"] is True
        assert callback_data["result"]["callback_query"]["data"] == "clicked"

        # Step 3: Bot receives the callback query via getUpdates
        updates = client.get(f"/bot{TEST_TOKEN}/getUpdates").json()["result"]
        assert len(updates) == 1
        assert "callback_query" in updates[0]
        assert updates[0]["callback_query"]["data"] == "clicked"

        # Step 4: Bot answers the callback query
        callback_query_id = updates[0]["callback_query"]["id"]
        answer_response = client.post(
            f"/bot{TEST_TOKEN}/answerCallbackQuery",
            data={
                "callback_query_id": callback_query_id,
                "text": "Button clicked!",
            },
        )
        assert answer_response.status_code == 200
        assert answer_response.json()["ok"] is True

    def test_multiple_users_multiple_chats(self, client: TestClient):
        """Test handling messages from multiple users/chats."""
        # User 1 sends a message
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello from User 1",
                "from_user": {"id": 1, "first_name": "User One"},
            },
        )

        # User 2 sends a message
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 200,
                "text": "Hello from User 2",
                "from_user": {"id": 2, "first_name": "User Two"},
            },
        )

        # Bot gets all updates
        updates = client.get(f"/bot{TEST_TOKEN}/getUpdates").json()["result"]
        assert len(updates) == 2

        # Bot responds to each user
        for update in updates:
            chat_id = update["message"]["chat"]["id"]
            user_name = update["message"]["from"]["first_name"]
            client.post(
                f"/bot{TEST_TOKEN}/sendMessage",
                data={
                    "chat_id": str(chat_id),
                    "text": f"Hello, {user_name}!",
                },
            )

        # Each user sees their response
        user1_messages = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        ).json()["result"]
        assert len(user1_messages) == 1
        assert user1_messages[0]["text"] == "Hello, User One!"

        user2_messages = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 200},
        ).json()["result"]
        assert len(user2_messages) == 1
        assert user2_messages[0]["text"] == "Hello, User Two!"


class TestE2EWebhook:
    """End-to-end tests using webhook delivery."""

    @pytest.mark.asyncio
    async def test_webhook_receives_user_message(self, client: TestClient, httpx_mock: HTTPXMock):
        """Test that webhook receives updates when user sends a message."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        # Step 1: Bot sets up webhook
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": webhook_url},
        )

        # Step 2: User sends a message - should trigger webhook
        response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello via webhook!",
            },
        )
        assert response.status_code == 200

        # Give async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Step 3: Verify webhook was called
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        payload = json.loads(requests[0].content)
        assert payload["message"]["text"] == "Hello via webhook!"

    @pytest.mark.asyncio
    async def test_webhook_receives_command(self, client: TestClient, httpx_mock: HTTPXMock):
        """Test that webhook receives command updates."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        # Set up webhook
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": webhook_url},
        )

        # User sends a command
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Give async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Verify webhook was called with command
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        payload = json.loads(requests[0].content)
        assert payload["message"]["text"] == "/start"
        assert payload["message"]["entities"][0]["type"] == "bot_command"

    @pytest.mark.asyncio
    async def test_webhook_receives_callback_query(self, client: TestClient, httpx_mock: HTTPXMock):
        """Test that webhook receives callback query updates."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        # Bot sends message with button
        keyboard = {"inline_keyboard": [[{"text": "Click", "callback_data": "test"}]]}
        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Click:",
                "reply_markup": json.dumps(keyboard),
            },
        )
        message_id = send_response.json()["result"]["message_id"]

        # Set up webhook after message is sent
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": webhook_url},
        )

        # User clicks button
        client.post(
            "/client/sendCallback",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "message_id": message_id,
                "callback_data": "test",
            },
        )

        # Give async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Verify webhook was called with callback query
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        payload = json.loads(requests[0].content)
        assert "callback_query" in payload
        assert payload["callback_query"]["data"] == "test"

    @pytest.mark.asyncio
    async def test_webhook_with_secret_token(self, client: TestClient, httpx_mock: HTTPXMock):
        """Test that webhook requests include secret token header."""
        webhook_url = "https://example.com/webhook"
        secret_token = "my_secret_123"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        # Set up webhook with secret token
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": webhook_url, "secret_token": secret_token},
        )

        # User sends a message
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello!",
            },
        )

        # Give async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Verify secret token header was included
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert requests[0].headers["x-telegram-bot-api-secret-token"] == secret_token

    @pytest.mark.asyncio
    async def test_full_webhook_flow_bot_responds(self, client: TestClient, httpx_mock: HTTPXMock):
        """Full webhook flow: user message -> webhook -> bot responds -> user gets response."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        # Set up webhook
        client.post(
            f"/bot{TEST_TOKEN}/setWebhook",
            data={"url": webhook_url},
        )

        # Step 1: User sends a message (triggers webhook)
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello!",
            },
        )

        # Give async task time to complete
        import asyncio

        await asyncio.sleep(0.1)

        # Verify webhook was called
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

        # Step 2: Bot sends a response (as if webhook handler processed it)
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Hi there!",
            },
        )

        # Step 3: User retrieves the response
        bot_messages = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        ).json()["result"]

        assert len(bot_messages) == 1
        assert bot_messages[0]["text"] == "Hi there!"


class TestCallbackFlow:
    """Tests for callback query handling flow."""

    def test_callback_message_not_found(self, client: TestClient):
        """Test that callback fails when message doesn't exist."""
        response = client.post(
            "/client/sendCallback",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "message_id": 999,  # Non-existent message
                "callback_data": "test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "message not found" in data["description"]

    def test_callback_includes_original_message(self, client: TestClient):
        """Test that callback query includes the original message."""
        # Bot sends message with button
        keyboard = {"inline_keyboard": [[{"text": "Click", "callback_data": "test"}]]}
        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={
                "chat_id": "100",
                "text": "Original message text",
                "reply_markup": json.dumps(keyboard),
            },
        )
        message_id = send_response.json()["result"]["message_id"]

        # User clicks button
        callback_response = client.post(
            "/client/sendCallback",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "message_id": message_id,
                "callback_data": "test",
            },
        )

        # Verify original message is included in callback
        callback_data = callback_response.json()
        assert callback_data["ok"] is True
        callback_message = callback_data["result"]["callback_query"]["message"]
        assert callback_message["message_id"] == message_id
        assert callback_message["text"] == "Original message text"
