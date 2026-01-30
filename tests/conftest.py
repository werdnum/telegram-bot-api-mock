"""Pytest configuration and fixtures."""

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from telegram import Bot
from telegram._utils.defaultvalue import DEFAULT_NONE
from telegram._utils.types import ODVInput
from telegram.request import BaseRequest, RequestData

from telegram_bot_api_mock.app import create_app
from telegram_bot_api_mock.dependencies import reset_state

# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class ASGIRequest(BaseRequest):
    """Custom request class that routes requests through ASGI transport.

    This allows PTB to communicate with our mock server without making real HTTP requests.
    """

    def __init__(self, app):
        """Initialize with the ASGI app to route requests to."""
        self._app = app
        self._client: AsyncClient | None = None

    @property
    def read_timeout(self) -> float | None:
        """Return the read timeout (not used for ASGI)."""
        return None

    async def initialize(self) -> None:
        """Initialize the httpx client with ASGI transport."""
        transport = ASGITransport(app=self._app)
        self._client = AsyncClient(transport=transport, base_url="http://test")

    async def shutdown(self) -> None:
        """Close the httpx client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def do_request(
        self,
        url: str,
        method: str,
        request_data: RequestData | None = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
    ) -> tuple[int, bytes]:
        """Perform the actual HTTP request via ASGI transport."""
        if self._client is None:
            raise RuntimeError("ASGIRequest is not initialized!")

        # Build request kwargs
        kwargs = {}
        if request_data:
            # Check if we have multipart data (files)
            if request_data.multipart_data:
                kwargs["files"] = request_data.multipart_data
                kwargs["data"] = request_data.json_parameters
            else:
                kwargs["data"] = request_data.json_parameters

        response = await self._client.request(
            method=method,
            url=url,
            **kwargs,
        )

        return response.status_code, response.content


@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset the global server state before each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def app():
    """Create a test application instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for raw HTTP requests."""
    return TestClient(app)


@pytest.fixture
async def bot(app) -> AsyncIterator[Bot]:
    """Create a PTB Bot instance configured to use the mock server.

    This fixture creates a python-telegram-bot Bot that sends requests
    to our mock ASGI app instead of the real Telegram API.
    """
    # Create custom requests that use ASGI transport
    # PTB uses separate request objects for get_updates vs other methods
    request = ASGIRequest(app)
    get_updates_request = ASGIRequest(app)

    # Create the bot with our custom requests and base_url pointing to mock server
    # The base_url should be just the base, PTB appends the token
    bot = Bot(
        token=TEST_TOKEN,
        base_url="http://test/bot",
        request=request,
        get_updates_request=get_updates_request,
    )

    # Initialize the bot (required for PTB v20+)
    await bot.initialize()

    yield bot

    # Cleanup
    await bot.shutdown()
