"""Integration tests for webhook delivery."""

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from telegram_bot_api_mock.dependencies import get_state, reset_state
from telegram_bot_api_mock.models import Message, Update
from telegram_bot_api_mock.models.telegram_types import Chat, User
from telegram_bot_api_mock.services import webhook_service

# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before and after each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def sample_update() -> Update:
    """Create a sample update for testing."""
    return Update(
        update_id=12345,
        message=Message(
            message_id=1,
            date=1234567890,
            chat=Chat(id=100, type="private"),
            from_user=User(id=100, is_bot=False, first_name="Test User"),
            text="Hello, bot!",
        ),
    )


class TestWebhookDelivery:
    """Tests for webhook delivery functionality."""

    @pytest.mark.asyncio
    async def test_deliver_update_success(self, httpx_mock: HTTPXMock, sample_update: Update):
        """Test that updates are delivered successfully to webhook URL."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        state = get_state()

        # Set up webhook
        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
        )

        # Deliver update
        result = await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        assert result is True

        # Verify the request was made
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        request = requests[0]
        assert str(request.url) == webhook_url
        assert request.method == "POST"
        assert request.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_deliver_update_with_secret_token(
        self, httpx_mock: HTTPXMock, sample_update: Update
    ):
        """Test that secret token is included in headers."""
        webhook_url = "https://example.com/webhook"
        secret_token = "my_secret_token_123"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        state = get_state()

        # Set up webhook with secret token
        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
            secret_token=secret_token,
        )

        # Deliver update
        await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        # Verify secret token header
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        request = requests[0]
        assert request.headers["x-telegram-bot-api-secret-token"] == secret_token

    @pytest.mark.asyncio
    async def test_deliver_update_payload_format(
        self, httpx_mock: HTTPXMock, sample_update: Update
    ):
        """Test that update payload is correctly formatted."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=200)

        state = get_state()

        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
        )

        await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        # Verify payload
        requests = httpx_mock.get_requests()
        request = requests[0]
        payload = json.loads(request.content)

        assert payload["update_id"] == 12345
        assert payload["message"]["message_id"] == 1
        assert payload["message"]["text"] == "Hello, bot!"
        assert payload["message"]["chat"]["id"] == 100
        assert payload["message"]["from"]["id"] == 100
        assert payload["message"]["from"]["first_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_deliver_update_no_webhook(self, sample_update: Update):
        """Test that delivery returns False when no webhook is configured."""
        state = get_state()

        # Don't set up any webhook
        await state.get_or_create_bot(TEST_TOKEN)

        result = await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_deliver_update_failure_logged(
        self, httpx_mock: HTTPXMock, sample_update: Update
    ):
        """Test that failed deliveries are handled gracefully."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=500, text="Internal Server Error")

        state = get_state()

        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
        )

        # Should not raise, just return False
        result = await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        assert result is False

        # Verify error info is stored
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert bot_state.webhook_config is not None
        assert bot_state.webhook_config.last_error_date is not None
        assert bot_state.webhook_config.last_error_message is not None
        assert "500" in bot_state.webhook_config.last_error_message

    @pytest.mark.asyncio
    async def test_deliver_update_connection_error(
        self, httpx_mock: HTTPXMock, sample_update: Update
    ):
        """Test that connection errors are handled gracefully."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        state = get_state()

        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
        )

        # Should not raise, just return False
        result = await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        assert result is False

        # Verify error info is stored
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert bot_state.webhook_config is not None
        assert bot_state.webhook_config.last_error_date is not None
        assert bot_state.webhook_config.last_error_message is not None
        assert "Connection" in bot_state.webhook_config.last_error_message


class TestWebhookInfoAfterErrors:
    """Tests for webhook info after delivery errors."""

    @pytest.mark.asyncio
    async def test_get_webhook_info_shows_error(self, httpx_mock: HTTPXMock, sample_update: Update):
        """Test that getWebhookInfo shows error information after failure."""
        webhook_url = "https://example.com/webhook"
        httpx_mock.add_response(url=webhook_url, status_code=400, text="Bad Request")

        state = get_state()

        await webhook_service.set_webhook(
            state=state,
            bot_token=TEST_TOKEN,
            url=webhook_url,
        )

        # Trigger a failed delivery
        await webhook_service.deliver_update(
            state=state,
            bot_token=TEST_TOKEN,
            update=sample_update,
        )

        # Get webhook info
        info = await webhook_service.get_webhook_info(
            state=state,
            bot_token=TEST_TOKEN,
        )

        assert info["url"] == webhook_url
        assert info["last_error_date"] is not None
        assert info["last_error_message"] is not None
        assert "400" in info["last_error_message"]
