"""Client API routes for test simulation."""

from fastapi import APIRouter

from telegram_bot_api_mock.routes.client.callbacks import router as callbacks_router
from telegram_bot_api_mock.routes.client.media import router as media_router
from telegram_bot_api_mock.routes.client.messages import router as messages_router
from telegram_bot_api_mock.routes.client.updates import router as updates_router

# Create the main client router
client_router = APIRouter()

# Include the sub-routers
client_router.include_router(messages_router)
client_router.include_router(callbacks_router)
client_router.include_router(updates_router)
client_router.include_router(media_router)

__all__ = ["client_router"]
