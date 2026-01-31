"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from telegram_bot_api_mock.exceptions import InvalidTokenError
from telegram_bot_api_mock.routes.bot import bot_router
from telegram_bot_api_mock.routes.client import client_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Telegram Bot API Mock",
        description="A mock server for testing Telegram bots",
        version="0.1.0",
    )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_exception_handler(
        _request: Request, exc: InvalidTokenError
    ) -> JSONResponse:
        """Handle invalid token errors with Telegram API-style responses."""
        return JSONResponse(
            status_code=401,
            content={
                "ok": False,
                "error_code": 401,
                "description": f"Unauthorized: {exc.message}",
            },
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
