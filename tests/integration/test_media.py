"""Integration tests for media API endpoints."""

import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from telegram import Bot
from telegram.constants import ChatAction

from tests.conftest import TEST_TOKEN


class TestSendPhoto:
    """Tests for the sendPhoto endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_photo_stores_and_returns_photo(self, bot: Bot):
        """Test that sendPhoto stores the photo and returns a message with photo field."""
        # Create a simple fake image content
        photo_data = BytesIO(b"fake image content for testing")
        photo_data.name = "test_photo.jpg"

        message = await bot.send_photo(chat_id=100, photo=photo_data)

        assert message.message_id == 1
        assert message.chat.id == 100
        assert message.from_user.id == 123456789
        assert message.from_user.is_bot is True

        # Verify photo field is populated with multiple sizes
        assert message.photo is not None
        assert len(message.photo) == 3  # thumbnail, medium, large

        # Check photo size fields
        for photo_size in message.photo:
            assert photo_size.file_id is not None
            assert photo_size.file_unique_id is not None
            assert photo_size.width is not None
            assert photo_size.height is not None
            assert photo_size.file_id != photo_size.file_unique_id

    @pytest.mark.asyncio
    async def test_send_photo_with_caption(self, bot: Bot):
        """Test sendPhoto with caption."""
        photo_data = BytesIO(b"fake image content")
        photo_data.name = "photo.jpg"

        message = await bot.send_photo(chat_id=100, photo=photo_data, caption="My photo caption")

        # Note: The mock server returns caption in the 'text' field, which PTB maps to 'text'
        # PTB's caption property returns the text field for media messages
        assert message.text == "My photo caption"


class TestSendDocument:
    """Tests for the sendDocument endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_document_stores_and_returns_document(self, bot: Bot):
        """Test that sendDocument stores the document and returns a message."""
        doc_content = b"This is a test document content"
        doc_data = BytesIO(doc_content)
        doc_data.name = "test_doc.pdf"

        message = await bot.send_document(chat_id=100, document=doc_data)

        assert message.message_id == 1
        assert message.chat.id == 100

        # Verify document field is populated
        assert message.document is not None
        assert message.document.file_id is not None
        assert message.document.file_unique_id is not None
        assert message.document.file_name == "test_doc.pdf"
        assert message.document.file_size == len(doc_content)

    @pytest.mark.asyncio
    async def test_send_document_with_caption(self, bot: Bot):
        """Test sendDocument with caption."""
        doc_data = BytesIO(b"Document content")
        doc_data.name = "doc.txt"

        message = await bot.send_document(
            chat_id=100, document=doc_data, caption="Document caption"
        )

        # Note: The mock server returns caption in the 'text' field
        assert message.text == "Document caption"


class TestSendVideo:
    """Tests for the sendVideo endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_video_stores_and_returns_video(self, bot: Bot):
        """Test that sendVideo stores the video and returns a message."""
        video_data = BytesIO(b"fake video content")
        video_data.name = "video.mp4"

        message = await bot.send_video(
            chat_id=100,
            video=video_data,
            duration=30,
            width=1920,
            height=1080,
        )

        assert message.video is not None
        assert message.video.duration == 30
        assert message.video.width == 1920
        assert message.video.height == 1080
        assert message.video.file_name == "video.mp4"


class TestSendAudio:
    """Tests for the sendAudio endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_audio_stores_and_returns_audio(self, bot: Bot):
        """Test that sendAudio stores the audio and returns a message."""
        audio_data = BytesIO(b"fake audio content")
        audio_data.name = "song.mp3"

        message = await bot.send_audio(
            chat_id=100,
            audio=audio_data,
            duration=180,
            performer="Test Artist",
            title="Test Song",
        )

        assert message.audio is not None
        assert message.audio.duration == 180
        assert message.audio.performer == "Test Artist"
        assert message.audio.title == "Test Song"


class TestSendVoice:
    """Tests for the sendVoice endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_voice_stores_and_returns_voice(self, bot: Bot):
        """Test that sendVoice stores the voice note and returns a message."""
        voice_data = BytesIO(b"fake voice content")
        voice_data.name = "voice.ogg"

        message = await bot.send_voice(
            chat_id=100,
            voice=voice_data,
            duration=5,
        )

        assert message.voice is not None
        assert message.voice.duration == 5
        assert message.voice.mime_type == "audio/ogg"


class TestSendAnimation:
    """Tests for the sendAnimation endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_animation_stores_and_returns_animation(self, bot: Bot):
        """Test that sendAnimation stores the animation and returns a message."""
        animation_data = BytesIO(b"fake gif content")
        animation_data.name = "animation.gif"

        message = await bot.send_animation(
            chat_id=100,
            animation=animation_data,
            duration=3,
            width=320,
            height=240,
        )

        assert message.animation is not None
        assert message.animation.duration == 3
        assert message.animation.width == 320
        assert message.animation.height == 240


class TestSendChatAction:
    """Tests for the sendChatAction endpoint using PTB."""

    @pytest.mark.asyncio
    async def test_send_chat_action_stores_action(self, bot: Bot):
        """Test that sendChatAction stores the action."""
        result = await bot.send_chat_action(chat_id=100, action=ChatAction.TYPING)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_chat_action_upload_photo(self, bot: Bot):
        """Test sendChatAction with upload_photo action."""
        result = await bot.send_chat_action(chat_id=100, action=ChatAction.UPLOAD_PHOTO)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_chat_action_invalid_action(self, client: TestClient):
        """Test sendChatAction with invalid action returns error.

        Note: We use the raw client here because PTB validates actions on the
        client side and won't send invalid action strings to the server.
        """
        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            data={"chat_id": "100", "action": "invalid_action"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "invalid action" in data["description"]


class TestGetFile:
    """Tests for the getFile endpoint.

    Note: PTB sends getFile requests as JSON POST, but the mock server currently
    expects query parameters. We use the raw client for these tests to match
    the current server implementation.
    """

    @pytest.mark.asyncio
    async def test_get_file_returns_file_info(self, client: TestClient, bot: Bot):
        """Test that getFile returns file information for a stored file."""
        # First, send a document to store a file using PTB
        doc_content = b"Test document content"
        doc_data = BytesIO(doc_content)
        doc_data.name = "test.txt"

        message = await bot.send_document(chat_id=100, document=doc_data)
        file_id = message.document.file_id

        # Now get the file info using raw client
        response = client.get(
            f"/bot{TEST_TOKEN}/getFile",
            params={"file_id": file_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["file_id"] == file_id
        assert data["result"]["file_unique_id"] is not None
        assert data["result"]["file_size"] == len(doc_content)
        assert data["result"]["file_path"] is not None

    def test_get_file_not_found(self, client: TestClient):
        """Test getFile returns error for non-existent file."""
        response = client.get(
            f"/bot{TEST_TOKEN}/getFile",
            params={"file_id": "nonexistent_file_id"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 400
        assert "not found" in data["description"]


class TestClientGetMedia:
    """Tests for the client getMedia endpoint.

    These tests use the raw client fixture since getMedia is a custom endpoint
    not part of the standard Telegram Bot API.
    """

    @pytest.mark.asyncio
    async def test_client_can_download_media(self, client: TestClient, bot: Bot):
        """Test that client can download media via getMedia endpoint."""
        # First, send a document to store a file
        doc_content = b"Test document content for download"
        doc_data = BytesIO(doc_content)
        doc_data.name = "download_test.txt"

        message = await bot.send_document(chat_id=100, document=doc_data)
        file_id = message.document.file_id

        # Now download the file using client endpoint
        response = client.get(f"/client/getMedia/{file_id}")

        assert response.status_code == 200
        assert response.content == doc_content
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    @pytest.mark.asyncio
    async def test_client_download_photo(self, client: TestClient, bot: Bot):
        """Test that client can download a photo."""
        photo_content = b"fake jpeg image data"
        photo_data = BytesIO(photo_content)
        photo_data.name = "photo.jpg"

        message = await bot.send_photo(chat_id=100, photo=photo_data)

        # Get one of the photo sizes
        file_id = message.photo[0].file_id

        response = client.get(f"/client/getMedia/{file_id}")

        assert response.status_code == 200
        assert response.content == photo_content

    def test_client_download_not_found(self, client: TestClient):
        """Test that client gets 404 for non-existent file."""
        response = client.get("/client/getMedia/nonexistent_id")

        assert response.status_code == 404


class TestClientGetChatActions:
    """Tests for the client getChatActions endpoint.

    These tests use the raw client fixture since getChatActions is a custom endpoint
    not part of the standard Telegram Bot API.
    """

    @pytest.mark.asyncio
    async def test_get_chat_actions_returns_active_actions(self, client: TestClient, bot: Bot):
        """Test getChatActions returns active actions."""
        # Send a chat action using PTB
        await bot.send_chat_action(chat_id=100, action=ChatAction.TYPING)

        # Get the actions using client endpoint
        response = client.get(
            "/client/getChatActions",
            params={"bot_token": TEST_TOKEN, "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["result"]) == 1
        assert data["result"][0]["action"] == "typing"
        assert data["result"][0]["chat_id"] == 100

    def test_get_chat_actions_empty_for_no_actions(self, client: TestClient):
        """Test getChatActions returns empty list when no actions."""
        response = client.get(
            "/client/getChatActions",
            params={"bot_token": TEST_TOKEN, "chat_id": 999},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == []

    def test_get_chat_actions_empty_for_unknown_bot(self, client: TestClient):
        """Test getChatActions returns empty list for unknown bot."""
        response = client.get(
            "/client/getChatActions",
            params={"bot_token": "unknown_token", "chat_id": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == []


class TestSendMediaGroup:
    """Tests for the sendMediaGroup endpoint.

    Note: PTB's send_media_group requires InputMedia objects with actual files,
    which is more complex. We keep using the raw client for these tests.
    """

    def test_send_media_group_returns_messages(self, client: TestClient):
        """Test sendMediaGroup returns a list of messages."""
        media = [
            {"type": "photo", "media": "photo1.jpg", "caption": "First photo"},
            {"type": "photo", "media": "photo2.jpg", "caption": "Second photo"},
        ]

        response = client.post(
            f"/bot{TEST_TOKEN}/sendMediaGroup",
            data={"chat_id": "100", "media": json.dumps(media)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], list)
        assert len(data["result"]) == 2

    def test_send_media_group_invalid_json(self, client: TestClient):
        """Test sendMediaGroup with invalid JSON returns error."""
        response = client.post(
            f"/bot{TEST_TOKEN}/sendMediaGroup",
            data={"chat_id": "100", "media": "invalid json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "invalid media JSON" in data["description"]
