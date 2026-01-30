"""Dependency injection for FastAPI routes."""

from telegram_bot_api_mock.state import BotState, ServerState

# Global server state instance
_server_state: ServerState | None = None


def get_state() -> ServerState:
    """Get the global ServerState instance.

    Creates the instance on first access (lazy initialization).

    Returns:
        The global ServerState instance.
    """
    global _server_state
    if _server_state is None:
        _server_state = ServerState()
    return _server_state


def reset_state() -> None:
    """Reset the global state (for testing purposes).

    This creates a fresh ServerState instance.
    """
    global _server_state
    _server_state = ServerState()


async def get_bot_state(token: str, state: ServerState | None = None) -> BotState:
    """Get the BotState for a given token.

    This is a helper function that gets or creates a bot state for the given token.
    If no state is provided, it uses the global state.

    Args:
        token: The bot token.
        state: Optional ServerState to use. If None, uses the global state.

    Returns:
        The BotState for the given token.
    """
    if state is None:
        state = get_state()
    return await state.get_or_create_bot(token)
