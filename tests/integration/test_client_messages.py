"""Integration tests for client message API endpoints."""

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app
from telegram_bot_api_mock.dependencies import reset_state


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before and after each test."""
    reset_state()
    yield
    reset_state()


@pytest.fixture
def client():
    """Create a test client for client message tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestClientSendMessage:
    """Tests for the client sendMessage endpoint."""

    def test_send_message_creates_update_for_bot(self, client: TestClient):
        """Test that sendMessage creates an update for the bot."""
        response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello, bot!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["update_id"] == 1
        assert data["result"]["message"]["text"] == "Hello, bot!"
        assert data["result"]["message"]["chat"]["id"] == 100
        # From user should be the default test user
        assert data["result"]["message"]["from"]["id"] == 1
        assert data["result"]["message"]["from"]["is_bot"] is False
        assert data["result"]["message"]["from"]["first_name"] == "Test User"

    def test_send_message_with_custom_from_user(self, client: TestClient):
        """Test sendMessage with a custom from_user."""
        response = client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello from custom user!",
                "from_user": {
                    "id": 42,
                    "is_bot": False,
                    "first_name": "Custom",
                    "last_name": "User",
                    "username": "customuser",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["from"]["id"] == 42
        assert data["result"]["message"]["from"]["first_name"] == "Custom"
        assert data["result"]["message"]["from"]["last_name"] == "User"
        assert data["result"]["message"]["from"]["username"] == "customuser"

    def test_send_message_update_available_via_get_updates(self, client: TestClient):
        """Test that the update created by sendMessage is available via bot getUpdates."""
        # Send a message as the client
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello, bot!",
            },
        )

        # Bot retrieves updates
        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 1
        assert data["result"][0]["message"]["text"] == "Hello, bot!"


class TestClientSendCommand:
    """Tests for the client sendCommand endpoint."""

    def test_send_command_creates_update_with_command_entity(self, client: TestClient):
        """Test that sendCommand creates an update with command entity."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["text"] == "/start"
        # Should have a bot_command entity
        entities = data["result"]["message"]["entities"]
        assert entities is not None
        assert len(entities) == 1
        assert entities[0]["type"] == "bot_command"
        assert entities[0]["offset"] == 0
        assert entities[0]["length"] == 6  # len("/start")

    def test_send_command_with_arguments(self, client: TestClient):
        """Test sendCommand with arguments after the command."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/help topic",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["text"] == "/help topic"
        # Entity should only cover "/help"
        entities = data["result"]["message"]["entities"]
        assert entities[0]["length"] == 5  # len("/help")

    def test_send_command_must_start_with_slash(self, client: TestClient):
        """Test that sendCommand rejects commands not starting with /."""
        response = client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "start",  # Missing /
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "must start with /" in data["description"]

    def test_send_command_update_available_via_get_updates(self, client: TestClient):
        """Test that command updates are available via bot getUpdates."""
        # Send a command as the client
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Bot retrieves updates
        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        message = data["result"][0]["message"]
        assert message["text"] == "/start"
        assert message["entities"][0]["type"] == "bot_command"


class TestClientGetUpdates:
    """Tests for the client getUpdates endpoint."""

    def test_get_updates_returns_bot_messages(self, client: TestClient):
        """Test that getUpdates returns messages sent by the bot."""
        # Bot sends a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello, user!"},
        )

        # Client retrieves bot messages
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 1
        assert data["result"][0]["text"] == "Hello, user!"
        # Message should be from the bot
        assert data["result"][0]["from"]["is_bot"] is True

    def test_get_updates_excludes_user_messages(self, client: TestClient):
        """Test that getUpdates does not return user messages."""
        # User sends a message (simulated)
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello from user!",
            },
        )

        # Bot sends a message
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello from bot!"},
        )

        # Client retrieves bot messages - should only see bot's message
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        # Should only contain the bot's message
        assert len(data["result"]) == 1
        assert data["result"][0]["text"] == "Hello from bot!"

    def test_get_updates_empty_for_different_chat(self, client: TestClient):
        """Test that getUpdates returns empty for different chat."""
        # Bot sends a message to chat 100
        client.post(
            f"/bot{TEST_TOKEN}/sendMessage",
            data={"chat_id": "100", "text": "Hello!"},
        )

        # Client checks chat 200 - should be empty
        response = client.get(
            "/client/getUpdates",
            params={"bot_token": TEST_TOKEN, "chat_id": 200},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 0


class TestClientGetUpdatesHistory:
    """Tests for the client getUpdatesHistory endpoint."""

    def test_get_updates_history_returns_all_updates(self, client: TestClient):
        """Test that getUpdatesHistory returns all updates for a bot."""
        # Send multiple messages
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "First message",
            },
        )
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Second message",
            },
        )

        # Get updates history
        response = client.get(
            "/client/getUpdatesHistory",
            params={"bot_token": TEST_TOKEN},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 2
        assert data["result"][0]["message"]["text"] == "First message"
        assert data["result"][1]["message"]["text"] == "Second message"

    def test_get_updates_history_includes_commands(self, client: TestClient):
        """Test that getUpdatesHistory includes command updates."""
        # Send a regular message
        client.post(
            "/client/sendMessage",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "text": "Hello",
            },
        )

        # Send a command
        client.post(
            "/client/sendCommand",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "command": "/start",
            },
        )

        # Get updates history
        response = client.get(
            "/client/getUpdatesHistory",
            params={"bot_token": TEST_TOKEN},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        # Second update should be the command
        assert data["result"][1]["message"]["text"] == "/start"
        assert data["result"][1]["message"]["entities"][0]["type"] == "bot_command"


class TestClientSendPhoto:
    """Tests for the client sendPhoto endpoint."""

    def test_send_photo_creates_update_with_photo(self, client: TestClient):
        """Test that sendPhoto creates an update with photo data."""
        import base64

        # Create a simple test image (1x1 pixel PNG)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        photo_b64 = base64.b64encode(png_data).decode()

        response = client.post(
            "/client/sendPhoto",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "photo": photo_b64,
                "caption": "Test photo",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["update_id"] == 1
        assert data["result"]["message"]["chat"]["id"] == 100
        # Should have photo data
        assert data["result"]["message"]["photo"] is not None
        assert len(data["result"]["message"]["photo"]) == 3  # 3 sizes
        # Caption should be in text field
        assert data["result"]["message"]["text"] == "Test photo"

    def test_send_photo_available_via_get_updates(self, client: TestClient):
        """Test that photo updates are available via bot getUpdates."""
        import base64

        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        photo_b64 = base64.b64encode(png_data).decode()

        client.post(
            "/client/sendPhoto",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "photo": photo_b64,
            },
        )

        response = client.get(f"/bot{TEST_TOKEN}/getUpdates")

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert data["result"][0]["message"]["photo"] is not None

    def test_send_photo_file_downloadable(self, client: TestClient):
        """Test that the photo can be downloaded via getMedia."""
        import base64

        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        photo_b64 = base64.b64encode(png_data).decode()

        response = client.post(
            "/client/sendPhoto",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "photo": photo_b64,
            },
        )

        photo_sizes = response.json()["result"]["message"]["photo"]
        file_id = photo_sizes[0]["file_id"]

        # Download the file
        download_response = client.get(f"/client/getMedia/{file_id}")
        assert download_response.status_code == 200
        assert download_response.content == png_data

    def test_send_photo_invalid_base64_returns_error(self, client: TestClient):
        """Test that invalid base64 returns an error."""
        response = client.post(
            "/client/sendPhoto",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "photo": "not-valid-base64!!!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "invalid base64" in data["description"]


class TestClientSendVideo:
    """Tests for the client sendVideo endpoint."""

    def test_send_video_creates_update_with_video(self, client: TestClient):
        """Test that sendVideo creates an update with video data."""
        import base64

        video_data = b"fake video content"
        video_b64 = base64.b64encode(video_data).decode()

        response = client.post(
            "/client/sendVideo",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "video": video_b64,
                "caption": "Test video",
                "width": 1920,
                "height": 1080,
                "duration": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["video"] is not None
        assert data["result"]["message"]["video"]["width"] == 1920
        assert data["result"]["message"]["video"]["height"] == 1080
        assert data["result"]["message"]["video"]["duration"] == 60
        assert data["result"]["message"]["text"] == "Test video"

    def test_send_video_downloadable(self, client: TestClient):
        """Test that the video can be downloaded."""
        import base64

        video_data = b"fake video content"
        video_b64 = base64.b64encode(video_data).decode()

        response = client.post(
            "/client/sendVideo",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "video": video_b64,
            },
        )

        file_id = response.json()["result"]["message"]["video"]["file_id"]
        download_response = client.get(f"/client/getMedia/{file_id}")
        assert download_response.status_code == 200
        assert download_response.content == video_data


class TestClientSendAudio:
    """Tests for the client sendAudio endpoint."""

    def test_send_audio_creates_update_with_audio(self, client: TestClient):
        """Test that sendAudio creates an update with audio data."""
        import base64

        audio_data = b"fake audio content"
        audio_b64 = base64.b64encode(audio_data).decode()

        response = client.post(
            "/client/sendAudio",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "audio": audio_b64,
                "caption": "Test audio",
                "duration": 180,
                "performer": "Test Artist",
                "title": "Test Song",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["audio"] is not None
        assert data["result"]["message"]["audio"]["duration"] == 180
        assert data["result"]["message"]["audio"]["performer"] == "Test Artist"
        assert data["result"]["message"]["audio"]["title"] == "Test Song"
        assert data["result"]["message"]["text"] == "Test audio"

    def test_send_audio_downloadable(self, client: TestClient):
        """Test that the audio can be downloaded."""
        import base64

        audio_data = b"fake audio content"
        audio_b64 = base64.b64encode(audio_data).decode()

        response = client.post(
            "/client/sendAudio",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "audio": audio_b64,
            },
        )

        file_id = response.json()["result"]["message"]["audio"]["file_id"]
        download_response = client.get(f"/client/getMedia/{file_id}")
        assert download_response.status_code == 200
        assert download_response.content == audio_data


class TestClientSendDocument:
    """Tests for the client sendDocument endpoint."""

    def test_send_document_creates_update_with_document(self, client: TestClient):
        """Test that sendDocument creates an update with document data."""
        import base64

        doc_data = b"Hello, this is a test document!"
        doc_b64 = base64.b64encode(doc_data).decode()

        response = client.post(
            "/client/sendDocument",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "document": doc_b64,
                "filename": "test.txt",
                "mime_type": "text/plain",
                "caption": "Test document",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["document"] is not None
        assert data["result"]["message"]["document"]["file_name"] == "test.txt"
        assert data["result"]["message"]["document"]["mime_type"] == "text/plain"
        assert data["result"]["message"]["document"]["file_size"] == len(doc_data)
        assert data["result"]["message"]["text"] == "Test document"

    def test_send_document_downloadable(self, client: TestClient):
        """Test that the document can be downloaded."""
        import base64

        doc_data = b"Document content for download test"
        doc_b64 = base64.b64encode(doc_data).decode()

        response = client.post(
            "/client/sendDocument",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "document": doc_b64,
                "filename": "download_test.txt",
            },
        )

        file_id = response.json()["result"]["message"]["document"]["file_id"]
        download_response = client.get(f"/client/getMedia/{file_id}")
        assert download_response.status_code == 200
        assert download_response.content == doc_data

    def test_send_document_with_custom_user(self, client: TestClient):
        """Test sendDocument with a custom from_user."""
        import base64

        doc_data = b"Document from custom user"
        doc_b64 = base64.b64encode(doc_data).decode()

        response = client.post(
            "/client/sendDocument",
            json={
                "bot_token": TEST_TOKEN,
                "chat_id": 100,
                "document": doc_b64,
                "filename": "custom.txt",
                "from_user": {
                    "id": 999,
                    "is_bot": False,
                    "first_name": "Document",
                    "last_name": "Sender",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message"]["from"]["id"] == 999
        assert data["result"]["message"]["from"]["first_name"] == "Document"
