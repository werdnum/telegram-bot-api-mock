# Telegram Bot API Mock

A Python/FastAPI mock server for testing Telegram bots.

## Quick Reference

```bash
uv run poe test       # Run lint + typecheck + tests
uv run poe lint       # Lint and format only
uv run poe typecheck  # Type check only
uv run poe test-only  # Tests only
uv run poe serve      # Start dev server
```

## Project Structure

- `src/telegram_bot_api_mock/` - Main package
  - `app.py` - FastAPI application factory
  - `config.py` - pydantic-settings configuration
  - `dependencies.py` - FastAPI dependency injection
  - `models/` - Pydantic models (Telegram types, requests, responses)
  - `state/` - Server state management (storage, counters, files)
  - `routes/bot/` - Bot API endpoints (`/bot{token}/*`)
  - `routes/client/` - Test simulation endpoints (`/client/*`)
  - `services/` - Business logic services
- `tests/` - Test suite (unit and integration)

## Key Design Patterns

1. **Auto-registration**: Bots are auto-created on first API call with their token
2. **Async-first**: All routes and services are async
3. **Thread-safe**: Uses asyncio locks for state modifications
4. **In-memory storage**: Files stored in memory by default

## Dependencies

- FastAPI + Pydantic for API and validation
- httpx for webhook delivery
- pytest-asyncio for async tests

@AGENTS.md
