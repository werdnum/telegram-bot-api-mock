# Telegram Bot API Mock

A Python/FastAPI mock server for testing Telegram bots, inspired by [jehy/telegram-test-api](https://github.com/nicholasgribanov/telegram-test-api).

## Features

- Full mock of Telegram Bot API endpoints
- Simulate user messages, commands, and callback queries
- Support for media messages (photos, documents, video, audio, voice, animation)
- Webhook support with automatic update delivery
- In-memory state for fast test execution
- Async-first design with thread-safe state management

## Installation

```bash
pip install telegram-bot-api-mock
```

Or with uv:

```bash
uv add telegram-bot-api-mock
```

## Quick Start

### With FastAPI TestClient (Recommended for Testing)

```python
from fastapi.testclient import TestClient
from telegram_bot_api_mock import create_app

# Create the mock server
app = create_app()
client = TestClient(app)

BOT_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

# Simulate a user sending a message to the bot
response = client.post(
    "/client/sendMessage",
    data={"bot_token": BOT_TOKEN, "chat_id": "100", "text": "Hello bot!"}
)
update = response.json()["result"]

# Bot polls for updates
response = client.get(f"/bot{BOT_TOKEN}/getUpdates")
updates = response.json()["result"]
# updates[0] contains the user's message

# Bot sends a reply
response = client.post(
    f"/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": "100", "text": "Hello user!"}
)

# Test can verify the bot's response
response = client.get(
    "/client/getUpdates",
    params={"bot_token": BOT_TOKEN, "chat_id": "100"}
)
messages = response.json()["result"]
# messages contains the bot's reply
```

### With httpx (Async)

```python
import httpx
from telegram_bot_api_mock import create_app

app = create_app()

async with httpx.AsyncClient(app=app, base_url="http://test") as client:
    # Bot sends a message
    response = await client.post(
        "/bot123456789:ABC/sendMessage",
        data={"chat_id": "123", "text": "Hello!"}
    )

    # Simulate user clicking an inline button
    response = await client.post(
        "/client/sendCallback",
        data={
            "bot_token": "123456789:ABC",
            "chat_id": "123",
            "message_id": "1",
            "callback_data": "button_clicked"
        }
    )
```

### End-to-End Test Example

```python
def test_bot_conversation():
    app = create_app()
    client = TestClient(app)
    TOKEN = "123456789:ABC-DEF"

    # User sends /start command
    client.post(
        "/client/sendCommand",
        data={"bot_token": TOKEN, "chat_id": "100", "command": "/start"}
    )

    # Bot receives the update via polling
    updates = client.get(f"/bot{TOKEN}/getUpdates").json()["result"]
    assert updates[0]["message"]["text"] == "/start"

    # Bot sends welcome message with inline keyboard
    import json
    keyboard = {"inline_keyboard": [[{"text": "Click me", "callback_data": "btn1"}]]}
    client.post(
        f"/bot{TOKEN}/sendMessage",
        data={
            "chat_id": "100",
            "text": "Welcome! Click the button:",
            "reply_markup": json.dumps(keyboard)
        }
    )

    # User clicks the button
    client.post(
        "/client/sendCallback",
        data={
            "bot_token": TOKEN,
            "chat_id": "100",
            "message_id": "2",
            "callback_data": "btn1"
        }
    )

    # Bot receives the callback query
    updates = client.get(f"/bot{TOKEN}/getUpdates").json()["result"]
    callback = updates[0]["callback_query"]
    assert callback["data"] == "btn1"

    # Bot answers the callback
    client.post(
        f"/bot{TOKEN}/answerCallbackQuery",
        data={"callback_query_id": callback["id"], "text": "Button clicked!"}
    )
```

## API Endpoints

### Bot API (`/bot{token}/*`)

Standard Telegram Bot API endpoints:

#### Messages
- `POST /sendMessage` - Send text message
- `POST /editMessageText` - Edit message text
- `POST /deleteMessage` - Delete a message

#### Updates
- `GET/POST /getMe` - Get bot information
- `GET/POST /getUpdates` - Get pending updates

#### Webhooks
- `POST /setWebhook` - Set webhook URL
- `POST /deleteWebhook` - Delete webhook
- `GET/POST /getWebhookInfo` - Get webhook configuration

#### Callbacks
- `POST /answerCallbackQuery` - Answer callback queries

#### Media
- `POST /sendPhoto` - Send photo
- `POST /sendDocument` - Send document
- `POST /sendVideo` - Send video
- `POST /sendAudio` - Send audio file
- `POST /sendVoice` - Send voice note
- `POST /sendAnimation` - Send animation/GIF
- `POST /sendMediaGroup` - Send multiple media as album
- `GET/POST /getFile` - Get file info

#### Chat Actions
- `POST /sendChatAction` - Send typing indicator, etc.

### Client API (`/client/*`)

Test simulation endpoints for triggering user actions:

#### Messages
- `POST /sendMessage` - Simulate user sending a message
- `POST /sendCommand` - Simulate user sending a command (e.g., /start)

#### Callbacks
- `POST /sendCallback` - Simulate user clicking inline button

#### Updates
- `GET /getUpdates` - Get messages sent by the bot to a specific chat
- `GET /getUpdatesHistory` - Get all updates history for a bot

#### Media
- `GET /getMedia/{file_id}` - Download media sent by bot
- `GET /getChatActions` - Get active chat actions for a chat
- `GET /getAllChatActions` - Get all active chat actions

## Development

```bash
# Install dependencies
uv sync --extra dev

# Run all checks (lint + typecheck + tests)
uv run poe test

# Individual commands
uv run poe lint       # Lint and format
uv run poe typecheck  # Type check only
uv run poe test-only  # Tests only

# Start dev server
uv run poe serve
```

## License

MIT
