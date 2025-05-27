"""Test implementations using mocks.

This module provides mock implementations that implement the same interfaces
as production services but use in-memory storage and simple logic for testing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from interfaces import (
    DatabaseClient,
    DatabaseCollection,
    DatabaseDocument,
    DatabaseQuery,
    EncryptionService,
    FieldFilterFactory,
    MessageHandler,
    TelegramBot,
    TelegramUpdate,
    TelegramUpdateParser,
)

logger = logging.getLogger(__name__)


class TestDatabaseDocument:
    """Test database document implementation."""

    def __init__(self, doc_id: str, data: dict[str, Any]):
        self.id = doc_id
        self._data = data

    def to_dict(self) -> dict[str, Any]:
        return self._data.copy()

    @property
    def exists(self) -> bool:
        return True


class TestDatabaseQuery:
    """Test database query implementation."""

    def __init__(self, collection_name: str, test_client: "TestDatabaseClient"):
        self.collection_name = collection_name
        self.test_client = test_client
        self._filters = []
        self._limit_value = None
        self._start_after_doc = None

    def where(self, filter: Any = None, **kwargs) -> "TestDatabaseQuery":
        new_query = TestDatabaseQuery(self.collection_name, self.test_client)
        new_query._filters = self._filters.copy()
        new_query._limit_value = self._limit_value
        new_query._start_after_doc = self._start_after_doc

        if filter is not None:
            new_query._filters.append(filter)

        for key, value in kwargs.items():
            new_query._filters.append({"field": key, "value": value})

        return new_query

    def limit(self, count: int) -> "TestDatabaseQuery":
        new_query = TestDatabaseQuery(self.collection_name, self.test_client)
        new_query._filters = self._filters.copy()
        new_query._limit_value = count
        new_query._start_after_doc = self._start_after_doc
        return new_query

    def start_after(self, document: DatabaseDocument) -> "TestDatabaseQuery":
        new_query = TestDatabaseQuery(self.collection_name, self.test_client)
        new_query._filters = self._filters.copy()
        new_query._limit_value = self._limit_value
        new_query._start_after_doc = document
        return new_query

    def _apply_filters(self, docs: list[DatabaseDocument]) -> list[DatabaseDocument]:
        """Apply filters to documents."""
        filtered_docs = []
        for doc in docs:
            if self._document_matches_filters(doc):
                filtered_docs.append(doc)
        return filtered_docs

    def _document_matches_filters(self, doc: DatabaseDocument) -> bool:
        """Check if a document matches all filters."""
        for filter_obj in self._filters:
            field, value = self._extract_filter_field_value(filter_obj)
            if field and field in doc._data and doc._data[field] != value:
                return False
        return True

    def _extract_filter_field_value(self, filter_obj: Any) -> tuple[str | None, Any]:
        """Extract field and value from filter object."""
        if hasattr(filter_obj, "field") and hasattr(filter_obj, "value"):
            return filter_obj.field, filter_obj.value
        elif isinstance(filter_obj, dict):
            return filter_obj.get("field"), filter_obj.get("value")
        return None, None

    def _apply_start_after(
        self, docs: list[DatabaseDocument]
    ) -> list[DatabaseDocument]:
        """Apply start_after pagination."""
        if not self._start_after_doc:
            return docs

        start_index = 0
        for i, doc in enumerate(docs):
            if doc.id == self._start_after_doc.id:
                start_index = i + 1
                break
        return docs[start_index:]

    def stream(self) -> list[DatabaseDocument]:
        """Stream documents with applied filters and pagination."""
        # Get all documents from the collection
        all_docs = self.test_client._collections.get(self.collection_name, [])

        # Apply filters
        filtered_docs = self._apply_filters(all_docs)

        # Apply start_after pagination
        filtered_docs = self._apply_start_after(filtered_docs)

        # Apply limit
        if self._limit_value:
            filtered_docs = filtered_docs[: self._limit_value]

        return filtered_docs


class TestDatabaseCollection:
    """Test database collection implementation."""

    def __init__(self, collection_name: str, test_client: "TestDatabaseClient"):
        self.collection_name = collection_name
        self.test_client = test_client

    def add(self, data: dict[str, Any]) -> tuple:
        doc_id = str(uuid.uuid4())
        doc = TestDatabaseDocument(doc_id, data)

        if self.collection_name not in self.test_client._collections:
            self.test_client._collections[self.collection_name] = []

        self.test_client._collections[self.collection_name].append(doc)
        return (datetime.utcnow(), doc)

    def document(self, doc_id: str) -> DatabaseDocument:
        docs = self.test_client._collections.get(self.collection_name, [])
        for doc in docs:
            if doc.id == doc_id:
                return doc
        return TestDatabaseDocument(doc_id, {})

    def where(self, filter: Any = None, **kwargs) -> DatabaseQuery:
        query = TestDatabaseQuery(self.collection_name, self.test_client)
        return query.where(filter=filter, **kwargs)

    def limit(self, count: int) -> DatabaseQuery:
        query = TestDatabaseQuery(self.collection_name, self.test_client)
        return query.limit(count)

    def stream(self) -> list[DatabaseDocument]:
        return self.test_client._collections.get(self.collection_name, [])


class TestDatabaseClient(DatabaseClient):
    """Test database client implementation using in-memory storage."""

    def __init__(self):
        logger.info("🧪 Initializing test database client...")
        self._collections = {}
        self._seed_test_data()
        logger.info("✅ Test database client initialized successfully")

    def collection(self, collection_name: str) -> DatabaseCollection:
        return TestDatabaseCollection(collection_name, self)

    def _seed_test_data(self):
        """Add some test data for integration tests."""
        messages_data = [
            {
                "message_id": 1,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 123456,
                "username": "testuser",
                "encrypted_text": {
                    "ciphertext": "dGVzdCBtZXNzYWdlIDEK",  # base64 "test message 1"
                    "encrypted_data_key": "mock_key_1",
                    "iv": "mock_iv_1",
                    "salt": "mock_salt_1",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
            {
                "message_id": 2,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 789012,
                "username": "testuser2",
                "encrypted_text": {
                    "ciphertext": "dGVzdCBtZXNzYWdlIDIK",  # base64 "test message 2"
                    "encrypted_data_key": "mock_key_2",
                    "iv": "mock_iv_2",
                    "salt": "mock_salt_2",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
        ]

        # Add test messages
        self._collections["messages"] = [
            TestDatabaseDocument(f"msg_{i}", data)
            for i, data in enumerate(messages_data)
        ]


class TestFieldFilterFactory(FieldFilterFactory):
    """Test field filter factory."""

    def create_filter(self, field: str, op: str, value: Any) -> Any:
        return TestFieldFilter(field, op, value)


class TestFieldFilter:
    """Test field filter implementation."""

    def __init__(self, field: str, op: str, value: Any):
        self.field = field
        self.op = op
        self.value = value


class TestEncryptionService(EncryptionService):
    """Test encryption service using simple base64 encoding."""

    def __init__(
        self,
        project_id: str = "test-project",
        location_id: str = "global",
        key_ring_id: str = "test-key-ring",
        key_id: str = "test-key",
    ):
        logger.info("🔐 Initializing test encryption service...")
        self.project_id = project_id
        self.location_id = location_id
        self.key_ring_id = key_ring_id
        self.key_id = key_id
        logger.info("✅ Test encryption service initialized successfully")

    def encrypt_message(self, plaintext: str) -> dict[str, Any]:
        """Test encryption using base64 encoding."""
        if not plaintext:
            return {
                "ciphertext": "",
                "encrypted_data_key": "",
                "iv": "",
                "salt": "",
            }

        import base64

        mock_ciphertext = base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")

        return {
            "ciphertext": mock_ciphertext,
            "encrypted_data_key": f"mock_key_{len(plaintext)}",
            "iv": f"mock_iv_{hash(plaintext) % 1000}",
            "salt": f"mock_salt_{len(plaintext)}",
        }

    def decrypt_message(self, encrypted_data: dict[str, Any]) -> str:
        """Test decryption using base64 decoding."""
        if not encrypted_data or not encrypted_data.get("ciphertext"):
            return ""

        try:
            import base64

            ciphertext = encrypted_data["ciphertext"]

            if isinstance(ciphertext, dict):
                ciphertext = ciphertext.get("ciphertext", "")

            if not ciphertext:
                return "[Test: Empty encrypted data]"

            try:
                decrypted_bytes = base64.b64decode(ciphertext.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
            except Exception:
                return f"[Test: Decrypted] {ciphertext[:50]}..."

        except Exception as e:
            return f"[Test: Decryption Error] {e!s}"


class TestTelegramBot(TelegramBot):
    """Test Telegram bot implementation."""

    def __init__(self, token: str | None = None):
        logger.info("🤖 Initializing test Telegram bot...")
        self.token = token or "test-bot-token"
        self.sent_messages = []  # Store sent messages for testing
        logger.info("✅ Test Telegram bot initialized successfully")

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str | None = None
    ) -> dict[str, Any]:
        message = {
            "message_id": len(self.sent_messages) + 1000,
            "chat": {"id": chat_id},
            "text": text,
            "parse_mode": parse_mode,
        }
        self.sent_messages.append(message)
        logger.info(f"🧪 Test: Would send message to {chat_id}: {text}")
        return message


class TestTelegramMessage:
    """Test Telegram message implementation."""

    def __init__(
        self,
        message_id: int,
        text: str,
        chat: "TestTelegramChat",
        user: "TestTelegramUser",
    ):
        self.message_id = message_id
        self.text = text
        self.chat = chat
        self.from_user = user


class TestTelegramChat:
    """Test Telegram chat implementation."""

    def __init__(
        self, chat_id: int, title: str | None = None, chat_type: str = "group"
    ):
        self.id = chat_id
        self.title = title
        self.type = chat_type


class TestTelegramUser:
    """Test Telegram user implementation."""

    def __init__(
        self, user_id: int, username: str | None = None, first_name: str | None = None
    ):
        self.id = user_id
        self.username = username
        self.first_name = first_name


class TestTelegramUpdate:
    """Test Telegram update implementation."""

    def __init__(self, message: TestTelegramMessage):
        self.message = message


class TestTelegramUpdateParser(TelegramUpdateParser):
    """Test Telegram update parser."""

    def parse_update(self, update_data: dict[str, Any]) -> TelegramUpdate:
        # Create test objects from update data
        message_data = update_data.get("message", {})
        chat_data = message_data.get("chat", {})
        user_data = message_data.get("from", {})

        chat = TestTelegramChat(
            chat_id=chat_data.get("id", 0),
            title=chat_data.get("title"),
            chat_type=chat_data.get("type", "group"),
        )

        user = TestTelegramUser(
            user_id=user_data.get("id", 0),
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
        )

        message = TestTelegramMessage(
            message_id=message_data.get("message_id", 0),
            text=message_data.get("text", ""),
            chat=chat,
            user=user,
        )

        return TestTelegramUpdate(message)


class TestMessageHandler(MessageHandler):
    """Test message handler implementation."""

    def __init__(
        self,
        db_client: DatabaseClient,
        encryption_service: EncryptionService,
        telegram_bot: TelegramBot,
    ):
        self.db_client = db_client
        self.encryption_service = encryption_service
        self.telegram_bot = telegram_bot

    async def handle_message(self, update: TelegramUpdate) -> int | None:
        """Handle incoming Telegram message: store to database and send response."""
        try:
            message = update.message
            chat = message.chat
            user = message.from_user

            logger.info(
                f"🧪 Test: Processing message {message.message_id} from user {user.id} in chat {chat.id}"
            )

            # 1. Encrypt and store the message
            if message.text:
                encrypted_data = self.encryption_service.encrypt_message(message.text)

                # Create message document
                message_data = {
                    "message_id": message.message_id,
                    "chat_id": chat.id,
                    "chat_title": chat.title,
                    "user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "encrypted_text": encrypted_data,
                    "timestamp": datetime.utcnow(),
                    "type": "telegram",
                }

                # Store in database
                messages_ref = self.db_client.collection("messages")
                messages_ref.add(message_data)

                logger.info(
                    f"🧪 Test: Stored encrypted message {message.message_id} to database"
                )

            # 2. Send response back to chat
            # Determine user display name
            user_display = user.username if user.username else user.first_name

            # Determine chat type and name
            if chat.type == "private":
                chat_display = "private chat"
            else:
                chat_display = chat.title or f"group chat {chat.id}"

            # Create response message
            response_text = f"I received message from *{user_display}*, in the chat *{chat_display}*, message id #{message.message_id}"

            # Send response back to the chat
            await self.telegram_bot.send_message(
                chat_id=chat.id, text=response_text, parse_mode="Markdown"
            )

            logger.info(
                f"🧪 Test: Sent response for message {message.message_id} in chat {chat.id}"
            )

            return message.message_id

        except Exception as e:
            logger.exception(f"❌ Test: Error handling Telegram message: {e}")
            raise
