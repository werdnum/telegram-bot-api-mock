"""Integration tests for token validation error responses."""

from fastapi.testclient import TestClient


class TestInvalidTokenResponses:
    """Tests for HTTP error responses when invalid tokens are used."""

    def test_missing_colon_returns_401_with_clear_message(self, client: TestClient) -> None:
        """Test that a token without colon returns 401 with helpful message."""
        response = client.post(
            "/botinvalid_token/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 401
        assert "Unauthorized" in data["description"]
        assert "colon" in data["description"].lower()

    def test_non_numeric_bot_id_returns_401_with_clear_message(self, client: TestClient) -> None:
        """Test that a non-numeric bot ID returns 401 with helpful message."""
        response = client.post(
            "/botabc:secret/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 401
        assert "Unauthorized" in data["description"]
        assert "positive integer" in data["description"]
        assert "abc" in data["description"]

    def test_empty_bot_id_returns_401_with_clear_message(self, client: TestClient) -> None:
        """Test that an empty bot ID returns 401 with helpful message."""
        response = client.post(
            "/bot:secret/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 401
        assert "cannot be empty" in data["description"]

    def test_negative_bot_id_returns_401_with_clear_message(self, client: TestClient) -> None:
        """Test that a negative bot ID returns 401 with helpful message."""
        response = client.post(
            "/bot-123:secret/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert data["error_code"] == 401
        assert "positive integer" in data["description"]

    def test_valid_token_is_accepted(self, client: TestClient) -> None:
        """Test that a valid token format is accepted."""
        response = client.post(
            "/bot123456789:ABC-secret/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_invalid_token_on_getme(self, client: TestClient) -> None:
        """Test that invalid token also fails for getMe endpoint."""
        response = client.get("/botbadtoken/getMe")

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False
        assert "colon" in data["description"].lower()

    def test_invalid_token_on_getupdates(self, client: TestClient) -> None:
        """Test that invalid token also fails for getUpdates endpoint."""
        response = client.get("/botbadtoken/getUpdates")

        assert response.status_code == 401
        data = response.json()
        assert data["ok"] is False

    def test_error_response_format_matches_telegram_api(self, client: TestClient) -> None:
        """Test that error response format matches Telegram Bot API style."""
        response = client.post(
            "/botinvalid/sendMessage",
            data={"chat_id": "100", "text": "Hello"},
        )

        data = response.json()
        # Verify all expected fields are present
        assert "ok" in data
        assert "error_code" in data
        assert "description" in data
        # Verify format
        assert isinstance(data["ok"], bool)
        assert isinstance(data["error_code"], int)
        assert isinstance(data["description"], str)
