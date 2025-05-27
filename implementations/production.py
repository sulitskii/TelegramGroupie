"""Production implementations using real GCP services.

This module provides the actual implementations that connect to
Google Cloud Platform services for production use.
"""

import logging
from datetime import datetime
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from telegram import Bot, Update
from telegram.request import HTTPXRequest

from encryption import MessageEncryption
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


class ProductionDatabaseDocument:
    """Production Firestore document wrapper."""

    def __init__(self, firestore_doc):
        self._firestore_doc = firestore_doc

    @property
    def id(self) -> str:
        return self._firestore_doc.id

    def to_dict(self) -> dict[str, Any]:
        return self._firestore_doc.to_dict()

    @property
    def exists(self) -> bool:
        return self._firestore_doc.exists


class ProductionDatabaseQuery:
    """Production Firestore query wrapper."""

    def __init__(self, firestore_query):
        self._firestore_query = firestore_query

    def where(self, filter: Any = None, **kwargs) -> "ProductionDatabaseQuery":
        if filter is not None:
            query = self._firestore_query.where(filter=filter)
        else:
            query = self._firestore_query.where(**kwargs)
        return ProductionDatabaseQuery(query)

    def limit(self, count: int) -> "ProductionDatabaseQuery":
        query = self._firestore_query.limit(count)
        return ProductionDatabaseQuery(query)

    def start_after(self, document: DatabaseDocument) -> "ProductionDatabaseQuery":
        if hasattr(document, "_firestore_doc"):
            query = self._firestore_query.start_after(document._firestore_doc)
        else:
            # For compatibility with mock documents
            query = self._firestore_query.start_after(document)
        return ProductionDatabaseQuery(query)

    def stream(self) -> list[DatabaseDocument]:
        firestore_docs = self._firestore_query.stream()
        return [ProductionDatabaseDocument(doc) for doc in firestore_docs]


class ProductionDatabaseCollection:
    """Production Firestore collection wrapper."""

    def __init__(self, firestore_collection):
        self._firestore_collection = firestore_collection

    def add(self, data: dict[str, Any]) -> tuple:
        return self._firestore_collection.add(data)

    def document(self, doc_id: str) -> DatabaseDocument:
        firestore_doc = self._firestore_collection.document(doc_id).get()
        return ProductionDatabaseDocument(firestore_doc)

    def where(self, filter: Any = None, **kwargs) -> DatabaseQuery:
        if filter is not None:
            query = self._firestore_collection.where(filter=filter)
        else:
            query = self._firestore_collection.where(**kwargs)
        return ProductionDatabaseQuery(query)

    def limit(self, count: int) -> DatabaseQuery:
        query = self._firestore_collection.limit(count)
        return ProductionDatabaseQuery(query)

    def stream(self) -> list[DatabaseDocument]:
        firestore_docs = self._firestore_collection.stream()
        return [ProductionDatabaseDocument(doc) for doc in firestore_docs]


class ProductionDatabaseClient(DatabaseClient):
    """Production Firestore client implementation."""

    def __init__(self):
        logger.info("🔥 Initializing production Firestore client...")
        self._client = firestore.Client()
        logger.info("✅ Production Firestore client initialized successfully")

    def collection(self, collection_name: str) -> DatabaseCollection:
        firestore_collection = self._client.collection(collection_name)
        return ProductionDatabaseCollection(firestore_collection)


class ProductionFieldFilterFactory(FieldFilterFactory):
    """Production field filter factory using Firestore FieldFilter."""

    def create_filter(self, field: str, op: str, value: Any) -> Any:
        return FieldFilter(field, op, value)


class ProductionEncryptionService(EncryptionService):
    """Production encryption service using Google Cloud KMS."""

    def __init__(
        self, project_id: str, location_id: str, key_ring_id: str, key_id: str
    ):
        logger.info(
            f"🔐 Initializing production encryption with "
            f"project_id={project_id}, location={location_id}, "
            f"key_ring={key_ring_id}, key_id={key_id}"
        )
        self._encryption = MessageEncryption(
            project_id=project_id,
            location_id=location_id,
            key_ring_id=key_ring_id,
            key_id=key_id,
        )
        logger.info("✅ Production encryption service initialized successfully")

    def encrypt_message(self, plaintext: str) -> dict[str, Any]:
        return self._encryption.encrypt_message(plaintext)

    def decrypt_message(self, encrypted_data: dict[str, Any]) -> str:
        return self._encryption.decrypt_message(encrypted_data)


class ProductionTelegramBot(TelegramBot):
    """Production Telegram bot implementation with optimized connection pool."""

    def __init__(self, token: str):
        logger.info("🤖 Initializing production Telegram bot...")

        # Configure HTTPXRequest with larger connection pool for production
        request = HTTPXRequest(
            connection_pool_size=20,  # Increase from default 1 to handle concurrent requests
            connect_timeout=20.0,  # Increase connection timeout
            read_timeout=30.0,  # Increase read timeout
            pool_timeout=10.0,  # Increase pool timeout from default 1.0
            write_timeout=30.0,  # Increase write timeout
        )

        self._bot = Bot(token=token, request=request)
        logger.info(
            "✅ Production Telegram bot initialized successfully with optimized connection pool"
        )

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str | None = None
    ) -> dict[str, Any]:
        message = await self._bot.send_message(
            chat_id=chat_id, text=text, parse_mode=parse_mode
        )
        return {"message_id": message.message_id, "chat": {"id": message.chat.id}}


class ProductionTelegramUpdateParser(TelegramUpdateParser):
    """Production Telegram update parser."""

    def __init__(self, bot: Bot):
        self._bot = bot

    def parse_update(self, update_data: dict[str, Any]) -> TelegramUpdate:
        return Update.de_json(update_data, self._bot)


class ProductionMessageHandler(MessageHandler):
    """Production message handler implementation."""

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
        """Handle incoming Telegram message: store to Firestore and send response."""
        try:
            message = update.message
            chat = message.chat
            user = message.from_user

            logger.info(
                f"🔄 Processing message {message.message_id} from user {user.id} in chat {chat.id}"
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

                # Store in Firestore
                messages_ref = self.db_client.collection("messages")
                messages_ref.add(message_data)

                logger.info(
                    f"💾 Stored encrypted message {message.message_id} to Firestore"
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
                f"📤 Sent response for message {message.message_id} in chat {chat.id}"
            )

            return message.message_id

        except Exception as e:
            logger.exception(f"❌ Error handling Telegram message: {e}")
            raise
