"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app
from telegram_bot_api_mock.dependencies import reset_state


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
    """Create a test client."""
    return TestClient(app)
