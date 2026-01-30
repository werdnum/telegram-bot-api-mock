"""Integration tests for media API endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from telegram_bot_api_mock.app import create_app


@pytest.fixture
def client():
    """Create a test client for media tests."""
    app = create_app()
    return TestClient(app)


# Test bot token - format is bot_id:secret
TEST_TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


class TestSendPhoto:
    """Tests for the sendPhoto endpoint."""

    def test_send_photo_stores_and_returns_photo(self, client: TestClient):
        """Test that sendPhoto stores the photo and returns a message with photo field."""
        # Create a simple fake image content
        photo_content = b"fake image content for testing"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendPhoto",
            data={"chat_id": "100"},
            files={"photo": ("test_photo.jpg", io.BytesIO(photo_content), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message_id"] == 1
        assert data["result"]["chat"]["id"] == 100
        assert data["result"]["from"]["id"] == 123456789
        assert data["result"]["from"]["is_bot"] is True

        # Verify photo field is populated with multiple sizes
        assert data["result"]["photo"] is not None
        assert len(data["result"]["photo"]) == 3  # thumbnail, medium, large

        # Check photo size fields
        for photo_size in data["result"]["photo"]:
            assert "file_id" in photo_size
            assert "file_unique_id" in photo_size
            assert "width" in photo_size
            assert "height" in photo_size
            assert photo_size["file_id"] != photo_size["file_unique_id"]

    def test_send_photo_with_caption(self, client: TestClient):
        """Test sendPhoto with caption."""
        photo_content = b"fake image content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendPhoto",
            data={"chat_id": "100", "caption": "My photo caption"},
            files={"photo": ("photo.jpg", io.BytesIO(photo_content), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["text"] == "My photo caption"


class TestSendDocument:
    """Tests for the sendDocument endpoint."""

    def test_send_document_stores_and_returns_document(self, client: TestClient):
        """Test that sendDocument stores the document and returns a message."""
        doc_content = b"This is a test document content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendDocument",
            data={"chat_id": "100"},
            files={"document": ("test_doc.pdf", io.BytesIO(doc_content), "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["message_id"] == 1
        assert data["result"]["chat"]["id"] == 100

        # Verify document field is populated
        assert data["result"]["document"] is not None
        doc = data["result"]["document"]
        assert "file_id" in doc
        assert "file_unique_id" in doc
        assert doc["file_name"] == "test_doc.pdf"
        assert doc["mime_type"] == "application/pdf"
        assert doc["file_size"] == len(doc_content)

    def test_send_document_with_caption(self, client: TestClient):
        """Test sendDocument with caption."""
        doc_content = b"Document content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendDocument",
            data={"chat_id": "100", "caption": "Document caption"},
            files={"document": ("doc.txt", io.BytesIO(doc_content), "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["text"] == "Document caption"


class TestSendVideo:
    """Tests for the sendVideo endpoint."""

    def test_send_video_stores_and_returns_video(self, client: TestClient):
        """Test that sendVideo stores the video and returns a message."""
        video_content = b"fake video content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendVideo",
            data={
                "chat_id": "100",
                "duration": "30",
                "width": "1920",
                "height": "1080",
            },
            files={"video": ("video.mp4", io.BytesIO(video_content), "video/mp4")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["video"] is not None
        video = data["result"]["video"]
        assert video["duration"] == 30
        assert video["width"] == 1920
        assert video["height"] == 1080
        assert video["file_name"] == "video.mp4"


class TestSendAudio:
    """Tests for the sendAudio endpoint."""

    def test_send_audio_stores_and_returns_audio(self, client: TestClient):
        """Test that sendAudio stores the audio and returns a message."""
        audio_content = b"fake audio content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendAudio",
            data={
                "chat_id": "100",
                "duration": "180",
                "performer": "Test Artist",
                "title": "Test Song",
            },
            files={"audio": ("song.mp3", io.BytesIO(audio_content), "audio/mpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["audio"] is not None
        audio = data["result"]["audio"]
        assert audio["duration"] == 180
        assert audio["performer"] == "Test Artist"
        assert audio["title"] == "Test Song"


class TestSendVoice:
    """Tests for the sendVoice endpoint."""

    def test_send_voice_stores_and_returns_voice(self, client: TestClient):
        """Test that sendVoice stores the voice note and returns a message."""
        voice_content = b"fake voice content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendVoice",
            data={"chat_id": "100", "duration": "5"},
            files={"voice": ("voice.ogg", io.BytesIO(voice_content), "audio/ogg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["voice"] is not None
        voice = data["result"]["voice"]
        assert voice["duration"] == 5
        assert voice["mime_type"] == "audio/ogg"


class TestSendAnimation:
    """Tests for the sendAnimation endpoint."""

    def test_send_animation_stores_and_returns_animation(self, client: TestClient):
        """Test that sendAnimation stores the animation and returns a message."""
        animation_content = b"fake gif content"

        response = client.post(
            f"/bot{TEST_TOKEN}/sendAnimation",
            data={
                "chat_id": "100",
                "duration": "3",
                "width": "320",
                "height": "240",
            },
            files={"animation": ("animation.gif", io.BytesIO(animation_content), "image/gif")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"]["animation"] is not None
        animation = data["result"]["animation"]
        assert animation["duration"] == 3
        assert animation["width"] == 320
        assert animation["height"] == 240


class TestSendChatAction:
    """Tests for the sendChatAction endpoint."""

    def test_send_chat_action_stores_action(self, client: TestClient):
        """Test that sendChatAction stores the action."""
        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            data={"chat_id": "100", "action": "typing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

    def test_send_chat_action_upload_photo(self, client: TestClient):
        """Test sendChatAction with upload_photo action."""
        response = client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            data={"chat_id": "100", "action": "upload_photo"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] is True

    def test_send_chat_action_invalid_action(self, client: TestClient):
        """Test sendChatAction with invalid action returns error."""
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
    """Tests for the getFile endpoint."""

    def test_get_file_returns_file_info(self, client: TestClient):
        """Test that getFile returns file information for a stored file."""
        # First, send a document to store a file
        doc_content = b"Test document content"

        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendDocument",
            data={"chat_id": "100"},
            files={"document": ("test.txt", io.BytesIO(doc_content), "text/plain")},
        )

        file_id = send_response.json()["result"]["document"]["file_id"]

        # Now get the file info
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
    """Tests for the client getMedia endpoint."""

    def test_client_can_download_media(self, client: TestClient):
        """Test that client can download media via getMedia endpoint."""
        # First, send a document to store a file
        doc_content = b"Test document content for download"

        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendDocument",
            data={"chat_id": "100"},
            files={"document": ("download_test.txt", io.BytesIO(doc_content), "text/plain")},
        )

        file_id = send_response.json()["result"]["document"]["file_id"]

        # Now download the file using client endpoint
        response = client.get(f"/client/getMedia/{file_id}")

        assert response.status_code == 200
        assert response.content == doc_content
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    def test_client_download_photo(self, client: TestClient):
        """Test that client can download a photo."""
        photo_content = b"fake jpeg image data"

        send_response = client.post(
            f"/bot{TEST_TOKEN}/sendPhoto",
            data={"chat_id": "100"},
            files={"photo": ("photo.jpg", io.BytesIO(photo_content), "image/jpeg")},
        )

        # Get one of the photo sizes
        file_id = send_response.json()["result"]["photo"][0]["file_id"]

        response = client.get(f"/client/getMedia/{file_id}")

        assert response.status_code == 200
        assert response.content == photo_content

    def test_client_download_not_found(self, client: TestClient):
        """Test that client gets 404 for non-existent file."""
        response = client.get("/client/getMedia/nonexistent_id")

        assert response.status_code == 404


class TestClientGetChatActions:
    """Tests for the client getChatActions endpoint."""

    def test_get_chat_actions_returns_active_actions(self, client: TestClient):
        """Test getChatActions returns active actions."""
        # Send a chat action
        client.post(
            f"/bot{TEST_TOKEN}/sendChatAction",
            data={"chat_id": "100", "action": "typing"},
        )

        # Get the actions
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
    """Tests for the sendMediaGroup endpoint."""

    def test_send_media_group_returns_messages(self, client: TestClient):
        """Test sendMediaGroup returns a list of messages."""
        import json

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
