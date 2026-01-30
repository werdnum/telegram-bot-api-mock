"""Bot API routes."""

from fastapi import APIRouter

from telegram_bot_api_mock.routes.bot.callbacks import router as callbacks_router
from telegram_bot_api_mock.routes.bot.chat_actions import router as chat_actions_router
from telegram_bot_api_mock.routes.bot.fallback import router as fallback_router
from telegram_bot_api_mock.routes.bot.media import router as media_router
from telegram_bot_api_mock.routes.bot.messages import router as messages_router
from telegram_bot_api_mock.routes.bot.updates import router as updates_router
from telegram_bot_api_mock.routes.bot.webhooks import router as webhooks_router

# Create the main bot router
bot_router = APIRouter()

# Include the sub-routers
# Order matters: more specific routes should come before the fallback
bot_router.include_router(messages_router)
bot_router.include_router(updates_router)
bot_router.include_router(webhooks_router)
bot_router.include_router(callbacks_router)
bot_router.include_router(media_router)
bot_router.include_router(chat_actions_router)
bot_router.include_router(fallback_router)

__all__ = ["bot_router"]
