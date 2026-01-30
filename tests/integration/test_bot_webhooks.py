"""Integration tests for bot webhook API endpoints using python-telegram-bot."""

import pytest
from telegram import Bot

from telegram_bot_api_mock.dependencies import get_state
from telegram_bot_api_mock.models import Message, Update
from telegram_bot_api_mock.models.telegram_types import Chat, User
from tests.conftest import TEST_TOKEN


class TestSetWebhook:
    """Tests for the setWebhook endpoint."""

    @pytest.mark.asyncio
    async def test_set_webhook_stores_url(self, bot: Bot):
        """Test that setWebhook stores the webhook URL."""
        result = await bot.set_webhook(url="https://example.com/webhook")

        assert result is True

        # Verify webhook is stored by calling getWebhookInfo
        info = await bot.get_webhook_info()
        assert info.url == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_set_webhook_with_secret_token(self, bot: Bot):
        """Test that setWebhook stores the secret token."""
        result = await bot.set_webhook(
            url="https://example.com/webhook",
            secret_token="my_secret_token",
        )

        assert result is True

        # Verify in state
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert bot_state.webhook_secret == "my_secret_token"

    @pytest.mark.asyncio
    async def test_set_webhook_with_max_connections(self, bot: Bot):
        """Test that setWebhook stores max_connections."""
        result = await bot.set_webhook(
            url="https://example.com/webhook",
            max_connections=100,
        )

        assert result is True

        info = await bot.get_webhook_info()
        assert info.max_connections == 100

    @pytest.mark.asyncio
    async def test_set_webhook_drop_pending_updates(self, bot: Bot):
        """Test that setWebhook can drop pending updates."""
        # First, we need to add some pending updates to the bot state
        state = get_state()

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

        # Verify update exists
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 1

        # Set webhook with drop_pending_updates=true
        result = await bot.set_webhook(
            url="https://example.com/webhook",
            drop_pending_updates=True,
        )

        assert result is True

        # Verify updates were dropped
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 0


class TestDeleteWebhook:
    """Tests for the deleteWebhook endpoint."""

    @pytest.mark.asyncio
    async def test_delete_webhook_removes_url(self, bot: Bot):
        """Test that deleteWebhook removes the webhook URL."""
        # First set a webhook
        await bot.set_webhook(url="https://example.com/webhook")

        # Verify it's set
        info = await bot.get_webhook_info()
        assert info.url == "https://example.com/webhook"

        # Delete the webhook
        result = await bot.delete_webhook()

        assert result is True

        # Verify it's gone
        info = await bot.get_webhook_info()
        assert info.url == ""

    @pytest.mark.asyncio
    async def test_delete_webhook_drop_pending_updates(self, bot: Bot):
        """Test that deleteWebhook can drop pending updates."""
        state = get_state()

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

        # Verify update exists
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 1

        # Delete webhook with drop_pending_updates=true
        result = await bot.delete_webhook(drop_pending_updates=True)

        assert result is True

        # Verify updates were dropped
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert len(bot_state.pending_updates) == 0


class TestGetWebhookInfo:
    """Tests for the getWebhookInfo endpoint."""

    @pytest.mark.asyncio
    async def test_get_webhook_info_empty(self, bot: Bot):
        """Test getWebhookInfo when no webhook is set."""
        info = await bot.get_webhook_info()

        assert info.url == ""
        assert info.has_custom_certificate is False
        assert info.pending_update_count == 0

    @pytest.mark.asyncio
    async def test_get_webhook_info_with_webhook(self, bot: Bot):
        """Test getWebhookInfo when webhook is set."""
        # Set a webhook
        await bot.set_webhook(
            url="https://example.com/webhook",
            max_connections=50,
        )

        info = await bot.get_webhook_info()

        assert info.url == "https://example.com/webhook"
        assert info.max_connections == 50
        assert info.has_custom_certificate is False


class TestAnswerCallbackQuery:
    """Tests for the answerCallbackQuery endpoint."""

    @pytest.mark.asyncio
    async def test_answer_callback_query_stores_answer(self, bot: Bot):
        """Test that answerCallbackQuery stores the answer."""
        result = await bot.answer_callback_query(
            callback_query_id="test_callback_123",
            text="Button clicked!",
            show_alert=True,
        )

        assert result is True

        # Verify answer is stored in state
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert "test_callback_123" in bot_state.answered_callbacks
        answered = bot_state.answered_callbacks["test_callback_123"]
        assert answered.text == "Button clicked!"
        assert answered.show_alert is True

    @pytest.mark.asyncio
    async def test_answer_callback_query_minimal(self, bot: Bot):
        """Test answerCallbackQuery with minimal parameters."""
        result = await bot.answer_callback_query(
            callback_query_id="test_callback_456",
        )

        assert result is True

        # Verify answer is stored
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        assert "test_callback_456" in bot_state.answered_callbacks
        answered = bot_state.answered_callbacks["test_callback_456"]
        assert answered.text is None
        assert answered.show_alert is False

    @pytest.mark.asyncio
    async def test_answer_callback_query_with_url(self, bot: Bot):
        """Test answerCallbackQuery with URL parameter."""
        result = await bot.answer_callback_query(
            callback_query_id="test_callback_789",
            url="https://example.com/game",
        )

        assert result is True

        # Verify URL is stored
        state = get_state()
        bot_state = state.get_bot(TEST_TOKEN)
        assert bot_state is not None
        answered = bot_state.answered_callbacks["test_callback_789"]
        assert answered.url == "https://example.com/game"
