"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from telegram_bot_api_mock.routes.bot import bot_router
from telegram_bot_api_mock.routes.client import client_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Telegram Bot API Mock",
        description="A mock server for testing Telegram bots",
        version="0.1.0",
    )

    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({"status": "ok"})

    # Include the bot API router
    app.include_router(bot_router)

    # Include the client API router for test simulation
    app.include_router(client_router)

    return app


app = create_app()
