"""Custom exceptions for the Telegram Bot API Mock server."""


class InvalidTokenError(Exception):
    """Raised when a bot token has an invalid format.

    Telegram bot tokens follow the format: "<bot_id>:<secret>"
    where bot_id is a positive integer.

    Examples of valid tokens:
        - "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        - "987654321:ABCdefGHIjklMNOpqrSTUvwxYZ"

    Examples of invalid tokens:
        - "invalid" (missing colon separator)
        - "abc:secret" (bot_id is not a number)
        - ":secret" (empty bot_id)
        - "123456789:" (empty secret, though this is technically parseable)
    """

    def __init__(self, message: str, token: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message describing what's wrong.
            token: The invalid token (optional, will be masked in messages).
        """
        self.message = message
        self.token = token
        super().__init__(message)

    @classmethod
    def missing_colon(cls, token: str) -> "InvalidTokenError":
        """Create an error for tokens missing the colon separator."""
        return cls(
            message=(
                "Invalid token format: token must contain a colon (':') separator. "
                "Expected format: '<bot_id>:<secret>' (e.g., '123456789:ABCdef...')"
            ),
            token=token,
        )

    @classmethod
    def invalid_bot_id(cls, bot_id_part: str, token: str) -> "InvalidTokenError":
        """Create an error for tokens with non-numeric bot IDs."""
        if not bot_id_part:
            return cls(
                message=(
                    "Invalid token format: bot_id cannot be empty. "
                    "Expected format: '<bot_id>:<secret>' where bot_id is a positive integer"
                ),
                token=token,
            )
        return cls(
            message=(
                f"Invalid token format: bot_id must be a positive integer, "
                f"got '{bot_id_part}'. "
                "Expected format: '<bot_id>:<secret>' (e.g., '123456789:ABCdef...')"
            ),
            token=token,
        )

    @classmethod
    def negative_bot_id(cls, bot_id: int, token: str) -> "InvalidTokenError":
        """Create an error for tokens with negative bot IDs."""
        return cls(
            message=(
                f"Invalid token format: bot_id must be a positive integer, "
                f"got '{bot_id}'. Bot IDs are always positive numbers."
            ),
            token=token,
        )
