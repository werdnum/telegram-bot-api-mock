"""Unit tests for Pydantic models."""

import json

from telegram_bot_api_mock.models import (
    AnswerCallbackQueryRequest,
    Audio,
    CallbackQuery,
    Chat,
    DeleteMessageRequest,
    Document,
    EditMessageTextRequest,
    ForceReply,
    GetUpdatesRequest,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    PhotoSize,
    ReplyKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    SendChatActionRequest,
    SendMessageRequest,
    SetWebhookRequest,
    TelegramResponse,
    Update,
    User,
    Video,
    Voice,
)


class TestUser:
    """Tests for User model."""

    def test_user_minimal(self):
        """Test User with minimal required fields."""
        user = User(id=123, is_bot=False, first_name="John")
        assert user.id == 123
        assert user.is_bot is False
        assert user.first_name == "John"
        assert user.last_name is None
        assert user.username is None
        assert user.language_code is None

    def test_user_full(self):
        """Test User with all fields."""
        user = User(
            id=456,
            is_bot=True,
            first_name="Bot",
            last_name="Test",
            username="testbot",
            language_code="en",
        )
        assert user.id == 456
        assert user.is_bot is True
        assert user.first_name == "Bot"
        assert user.last_name == "Test"
        assert user.username == "testbot"
        assert user.language_code == "en"


class TestChat:
    """Tests for Chat model."""

    def test_private_chat(self):
        """Test private chat."""
        chat = Chat(id=123, type="private", first_name="John", last_name="Doe")
        assert chat.id == 123
        assert chat.type == "private"
        assert chat.first_name == "John"
        assert chat.last_name == "Doe"
        assert chat.title is None

    def test_group_chat(self):
        """Test group chat."""
        chat = Chat(id=-456, type="group", title="Test Group")
        assert chat.id == -456
        assert chat.type == "group"
        assert chat.title == "Test Group"

    def test_supergroup_chat(self):
        """Test supergroup chat."""
        chat = Chat(id=-100123, type="supergroup", title="Super Group", username="supergroup")
        assert chat.type == "supergroup"
        assert chat.username == "supergroup"

    def test_channel(self):
        """Test channel."""
        chat = Chat(id=-100456, type="channel", title="Test Channel", username="testchannel")
        assert chat.type == "channel"


class TestMessageEntity:
    """Tests for MessageEntity model."""

    def test_basic_entity(self):
        """Test basic message entity."""
        entity = MessageEntity(type="bold", offset=0, length=5)
        assert entity.type == "bold"
        assert entity.offset == 0
        assert entity.length == 5

    def test_url_entity(self):
        """Test URL entity."""
        entity = MessageEntity(type="text_link", offset=0, length=10, url="https://example.com")
        assert entity.url == "https://example.com"

    def test_mention_entity(self):
        """Test mention entity with user."""
        user = User(id=123, is_bot=False, first_name="John")
        entity = MessageEntity(type="text_mention", offset=0, length=5, user=user)
        assert entity.user is not None
        assert entity.user.id == 123


class TestInlineKeyboard:
    """Tests for InlineKeyboardButton and InlineKeyboardMarkup."""

    def test_button_with_url(self):
        """Test button with URL."""
        button = InlineKeyboardButton(text="Visit", url="https://example.com")
        assert button.text == "Visit"
        assert button.url == "https://example.com"
        assert button.callback_data is None

    def test_button_with_callback_data(self):
        """Test button with callback data."""
        button = InlineKeyboardButton(text="Click me", callback_data="action_1")
        assert button.text == "Click me"
        assert button.callback_data == "action_1"

    def test_inline_keyboard_markup(self):
        """Test inline keyboard markup."""
        button1 = InlineKeyboardButton(text="Option 1", callback_data="opt1")
        button2 = InlineKeyboardButton(text="Option 2", callback_data="opt2")
        markup = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
        assert len(markup.inline_keyboard) == 1
        assert len(markup.inline_keyboard[0]) == 2


class TestReplyKeyboard:
    """Tests for ReplyKeyboardButton and ReplyKeyboardMarkup."""

    def test_button_basic(self):
        """Test basic reply keyboard button."""
        button = ReplyKeyboardButton(text="Send")
        assert button.text == "Send"
        assert button.request_contact is None

    def test_button_with_contact_request(self):
        """Test button requesting contact."""
        button = ReplyKeyboardButton(text="Share Contact", request_contact=True)
        assert button.request_contact is True

    def test_reply_keyboard_markup(self):
        """Test reply keyboard markup."""
        button = ReplyKeyboardButton(text="Hello")
        markup = ReplyKeyboardMarkup(
            keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True
        )
        assert len(markup.keyboard) == 1
        assert markup.resize_keyboard is True
        assert markup.one_time_keyboard is True


class TestReplyKeyboardRemove:
    """Tests for ReplyKeyboardRemove."""

    def test_default(self):
        """Test default values."""
        remove = ReplyKeyboardRemove()
        assert remove.remove_keyboard is True
        assert remove.selective is None

    def test_with_selective(self):
        """Test with selective."""
        remove = ReplyKeyboardRemove(selective=True)
        assert remove.selective is True


class TestForceReply:
    """Tests for ForceReply."""

    def test_default(self):
        """Test default values."""
        force = ForceReply()
        assert force.force_reply is True
        assert force.input_field_placeholder is None

    def test_with_placeholder(self):
        """Test with placeholder."""
        force = ForceReply(input_field_placeholder="Enter your message...")
        assert force.input_field_placeholder == "Enter your message..."


class TestMessage:
    """Tests for Message model."""

    def test_minimal_message(self):
        """Test message with minimal fields."""
        chat = Chat(id=123, type="private")
        message = Message(message_id=1, date=1234567890, chat=chat)
        assert message.message_id == 1
        assert message.date == 1234567890
        assert message.chat.id == 123
        assert message.from_user is None
        assert message.text is None

    def test_message_with_from_alias(self):
        """Test message with from field using alias."""
        # Test using the alias "from" as key
        data = {
            "message_id": 1,
            "date": 1234567890,
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 456, "is_bot": False, "first_name": "John"},
            "text": "Hello",
        }
        message = Message.model_validate(data)
        assert message.from_user is not None
        assert message.from_user.id == 456

    def test_message_with_text(self):
        """Test message with text."""
        chat = Chat(id=123, type="private")
        message = Message(message_id=1, date=1234567890, chat=chat, text="Hello, World!")
        assert message.text == "Hello, World!"

    def test_message_with_entities(self):
        """Test message with entities."""
        chat = Chat(id=123, type="private")
        entity = MessageEntity(type="bold", offset=0, length=5)
        message = Message(message_id=1, date=1234567890, chat=chat, text="Hello", entities=[entity])
        assert message.entities is not None
        assert len(message.entities) == 1
        assert message.entities[0].type == "bold"

    def test_message_with_reply_markup(self):
        """Test message with inline keyboard."""
        chat = Chat(id=123, type="private")
        button = InlineKeyboardButton(text="Click", callback_data="test")
        markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
        message = Message(message_id=1, date=1234567890, chat=chat, reply_markup=markup)
        assert message.reply_markup is not None


class TestMediaTypes:
    """Tests for media type models."""

    def test_photo_size(self):
        """Test PhotoSize model."""
        photo = PhotoSize(
            file_id="abc123", file_unique_id="unique123", width=640, height=480, file_size=12345
        )
        assert photo.file_id == "abc123"
        assert photo.width == 640
        assert photo.height == 480

    def test_document(self):
        """Test Document model."""
        doc = Document(
            file_id="doc123",
            file_unique_id="docunique123",
            file_name="test.pdf",
            mime_type="application/pdf",
            file_size=54321,
        )
        assert doc.file_name == "test.pdf"
        assert doc.mime_type == "application/pdf"

    def test_document_with_thumbnail(self):
        """Test Document with thumbnail."""
        thumb = PhotoSize(file_id="thumb123", file_unique_id="thumbunique", width=90, height=90)
        doc = Document(file_id="doc123", file_unique_id="docunique123", thumbnail=thumb)
        assert doc.thumbnail is not None
        assert doc.thumbnail.file_id == "thumb123"

    def test_audio(self):
        """Test Audio model."""
        audio = Audio(
            file_id="audio123",
            file_unique_id="audiounique123",
            duration=180,
            performer="Artist",
            title="Song Title",
        )
        assert audio.duration == 180
        assert audio.performer == "Artist"

    def test_video(self):
        """Test Video model."""
        video = Video(
            file_id="video123",
            file_unique_id="videounique123",
            width=1920,
            height=1080,
            duration=60,
        )
        assert video.width == 1920
        assert video.height == 1080

    def test_voice(self):
        """Test Voice model."""
        voice = Voice(
            file_id="voice123",
            file_unique_id="voiceunique123",
            duration=30,
            mime_type="audio/ogg",
        )
        assert voice.duration == 30


class TestCallbackQuery:
    """Tests for CallbackQuery model."""

    def test_callback_query_with_message(self):
        """Test callback query with message."""
        data = {
            "id": "query123",
            "from": {"id": 456, "is_bot": False, "first_name": "John"},
            "chat_instance": "instance123",
            "data": "button_clicked",
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123, "type": "private"},
            },
        }
        query = CallbackQuery.model_validate(data)
        assert query.id == "query123"
        assert query.from_user.id == 456
        assert query.data == "button_clicked"
        assert query.message is not None

    def test_callback_query_with_inline_message(self):
        """Test callback query with inline message ID."""
        data = {
            "id": "query456",
            "from": {"id": 789, "is_bot": False, "first_name": "Jane"},
            "chat_instance": "instance456",
            "inline_message_id": "inline123",
        }
        query = CallbackQuery.model_validate(data)
        assert query.inline_message_id == "inline123"
        assert query.message is None


class TestUpdate:
    """Tests for Update model."""

    def test_update_with_message(self):
        """Test update with message."""
        data = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 1234567890,
                "chat": {"id": 123, "type": "private"},
                "text": "Hello",
            },
        }
        update = Update.model_validate(data)
        assert update.update_id == 1
        assert update.message is not None
        assert update.message.text == "Hello"

    def test_update_with_callback_query(self):
        """Test update with callback query."""
        data = {
            "update_id": 2,
            "callback_query": {
                "id": "query123",
                "from": {"id": 456, "is_bot": False, "first_name": "John"},
                "chat_instance": "instance123",
                "data": "clicked",
            },
        }
        update = Update.model_validate(data)
        assert update.callback_query is not None
        assert update.callback_query.data == "clicked"


class TestSendMessageRequest:
    """Tests for SendMessageRequest model."""

    def test_minimal_request(self):
        """Test minimal send message request."""
        request = SendMessageRequest(chat_id=123, text="Hello")
        assert request.chat_id == 123
        assert request.text == "Hello"

    def test_request_with_string_chat_id(self):
        """Test request with string chat_id."""
        request = SendMessageRequest(chat_id="@channel", text="Hello")
        assert request.chat_id == "@channel"

    def test_reply_markup_from_dict(self):
        """Test reply_markup parsed from dict."""
        request = SendMessageRequest.model_validate(
            {
                "chat_id": 123,
                "text": "Hello",
                "reply_markup": {"inline_keyboard": [[{"text": "Click", "callback_data": "test"}]]},
            }
        )
        assert isinstance(request.reply_markup, InlineKeyboardMarkup)
        assert len(request.reply_markup.inline_keyboard) == 1

    def test_reply_markup_from_json_string(self):
        """Test reply_markup parsed from JSON string."""
        markup_json = json.dumps(
            {"inline_keyboard": [[{"text": "Button", "callback_data": "action"}]]}
        )
        request = SendMessageRequest.model_validate(
            {"chat_id": 123, "text": "Hello", "reply_markup": markup_json}
        )
        assert isinstance(request.reply_markup, InlineKeyboardMarkup)
        assert request.reply_markup.inline_keyboard[0][0].text == "Button"

    def test_reply_keyboard_markup_from_json(self):
        """Test ReplyKeyboardMarkup parsed from JSON string."""
        markup_json = json.dumps({"keyboard": [[{"text": "Option 1"}]], "resize_keyboard": True})
        request = SendMessageRequest.model_validate(
            {"chat_id": 123, "text": "Choose", "reply_markup": markup_json}
        )
        assert isinstance(request.reply_markup, ReplyKeyboardMarkup)
        assert request.reply_markup.resize_keyboard is True

    def test_reply_keyboard_remove_from_json(self):
        """Test ReplyKeyboardRemove parsed from JSON string."""
        markup_json = json.dumps({"remove_keyboard": True})
        request = SendMessageRequest.model_validate(
            {"chat_id": 123, "text": "Removed", "reply_markup": markup_json}
        )
        assert isinstance(request.reply_markup, ReplyKeyboardRemove)

    def test_force_reply_from_json(self):
        """Test ForceReply parsed from JSON string."""
        markup_json = json.dumps({"force_reply": True, "input_field_placeholder": "Type here"})
        request = SendMessageRequest.model_validate(
            {"chat_id": 123, "text": "Reply", "reply_markup": markup_json}
        )
        assert isinstance(request.reply_markup, ForceReply)
        assert request.reply_markup.input_field_placeholder == "Type here"


class TestEditMessageTextRequest:
    """Tests for EditMessageTextRequest model."""

    def test_edit_with_chat_and_message_id(self):
        """Test edit with chat_id and message_id."""
        request = EditMessageTextRequest(chat_id=123, message_id=456, text="Updated text")
        assert request.chat_id == 123
        assert request.message_id == 456
        assert request.text == "Updated text"

    def test_edit_with_inline_message_id(self):
        """Test edit with inline_message_id."""
        request = EditMessageTextRequest(inline_message_id="inline123", text="Updated")
        assert request.inline_message_id == "inline123"
        assert request.chat_id is None

    def test_reply_markup_from_json_string(self):
        """Test reply_markup parsed from JSON string."""
        markup_json = json.dumps(
            {"inline_keyboard": [[{"text": "New Button", "callback_data": "new"}]]}
        )
        request = EditMessageTextRequest.model_validate(
            {"chat_id": 123, "message_id": 456, "text": "Updated", "reply_markup": markup_json}
        )
        assert isinstance(request.reply_markup, InlineKeyboardMarkup)


class TestDeleteMessageRequest:
    """Tests for DeleteMessageRequest model."""

    def test_delete_request(self):
        """Test delete message request."""
        request = DeleteMessageRequest(chat_id=123, message_id=456)
        assert request.chat_id == 123
        assert request.message_id == 456


class TestAnswerCallbackQueryRequest:
    """Tests for AnswerCallbackQueryRequest model."""

    def test_minimal_request(self):
        """Test minimal answer callback query request."""
        request = AnswerCallbackQueryRequest(callback_query_id="query123")
        assert request.callback_query_id == "query123"
        assert request.text is None

    def test_with_alert(self):
        """Test with alert."""
        request = AnswerCallbackQueryRequest(
            callback_query_id="query123", text="Alert!", show_alert=True
        )
        assert request.show_alert is True


class TestSetWebhookRequest:
    """Tests for SetWebhookRequest model."""

    def test_minimal_request(self):
        """Test minimal set webhook request."""
        request = SetWebhookRequest(url="https://example.com/webhook")
        assert request.url == "https://example.com/webhook"

    def test_full_request(self):
        """Test full set webhook request."""
        request = SetWebhookRequest(
            url="https://example.com/webhook",
            max_connections=100,
            allowed_updates=["message", "callback_query"],
            secret_token="secret123",
        )
        assert request.max_connections == 100
        assert request.allowed_updates is not None
        assert "message" in request.allowed_updates


class TestSendChatActionRequest:
    """Tests for SendChatActionRequest model."""

    def test_typing_action(self):
        """Test typing action."""
        request = SendChatActionRequest(chat_id=123, action="typing")
        assert request.action == "typing"


class TestGetUpdatesRequest:
    """Tests for GetUpdatesRequest model."""

    def test_minimal_request(self):
        """Test minimal request."""
        request = GetUpdatesRequest()
        assert request.offset is None

    def test_with_parameters(self):
        """Test with parameters."""
        request = GetUpdatesRequest(offset=100, limit=50, timeout=30)
        assert request.offset == 100
        assert request.limit == 50
        assert request.timeout == 30


class TestTelegramResponse:
    """Tests for TelegramResponse generic model."""

    def test_success_response_with_bool(self):
        """Test success response with boolean result."""
        response = TelegramResponse[bool](ok=True, result=True)
        assert response.ok is True
        assert response.result is True
        assert response.error_code is None

    def test_success_response_with_message(self):
        """Test success response with Message result."""
        message_data = {
            "message_id": 1,
            "date": 1234567890,
            "chat": {"id": 123, "type": "private"},
            "text": "Hello",
        }
        message = Message.model_validate(message_data)
        response = TelegramResponse[Message](ok=True, result=message)
        assert response.ok is True
        assert response.result is not None
        assert response.result.text == "Hello"

    def test_error_response(self):
        """Test error response."""
        response = TelegramResponse[Message](
            ok=False, error_code=400, description="Bad Request: chat not found"
        )
        assert response.ok is False
        assert response.error_code == 400
        assert response.description == "Bad Request: chat not found"
        assert response.result is None

    def test_success_response_with_list(self):
        """Test success response with list result."""
        updates = [
            Update(
                update_id=1,
                message=Message.model_validate(
                    {
                        "message_id": 1,
                        "date": 1234567890,
                        "chat": {"id": 123, "type": "private"},
                    }
                ),
            )
        ]
        response = TelegramResponse[list[Update]](ok=True, result=updates)
        assert response.ok is True
        assert response.result is not None
        assert len(response.result) == 1
        assert response.result[0].update_id == 1
