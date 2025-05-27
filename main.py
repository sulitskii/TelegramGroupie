import asyncio
import logging
import os
from datetime import datetime

from flask import Flask, abort, jsonify, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

app = Flask(__name__)

# Set up logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Production-only services initialization
logger.info("🏭 Initializing production services...")

# Check if we're in testing mode
TESTING_MODE = os.environ.get("TESTING", "false").lower() == "true"

if TESTING_MODE:
    logger.info("🧪 TESTING MODE: Using mock services")
    # Use mock implementations for testing
    try:
        from mock_encryption import MockMessageEncryption
        from mock_firestore import MockFirestoreClient

        logger.info("📦 Using mock services for testing")

        # Initialize mock Firestore client
        logger.info("🔥 Initializing mock Firestore client...")
        db = MockFirestoreClient()
        logger.info("✅ Mock Firestore client initialized successfully")

        # Initialize mock encryption
        encryption = MockMessageEncryption(
            project_id="test-project",
            location_id="global",
            key_ring_id="test-key-ring",
            key_id="test-key-id",
        )
        logger.info("✅ Mock encryption service initialized successfully")

        # Mock FieldFilter for testing
        from mock_firestore import MockFieldFilter as FieldFilter

    except Exception as e:
        logger.exception(f"❌ Failed to initialize mock services: {e}")
        raise
else:
    logger.info("🏭 PRODUCTION MODE: Using real GCP services")
    try:
        # Always use real implementations in production
        from google.cloud import firestore
        from google.cloud.firestore_v1.base_query import FieldFilter

        from encryption import MessageEncryption

        logger.info("📦 Imported Google Cloud services")

        # Initialize Firestore client
        logger.info("🔥 Initializing Firestore client...")
        db = firestore.Client()
        logger.info("✅ Firestore client initialized successfully")

        # Get environment variables
        project_id = os.environ.get("GCP_PROJECT_ID")
        kms_location = os.environ.get("KMS_LOCATION", "global")
        kms_key_ring = os.environ.get("KMS_KEY_RING", "telegram-messages")
        kms_key_id = os.environ.get("KMS_KEY_ID", "message-key")

        logger.info(
            f"🔐 Initializing encryption with project_id={project_id}, location={kms_location}, key_ring={kms_key_ring}, key_id={kms_key_id}"
        )

        # Initialize encryption
        encryption = MessageEncryption(
            project_id=project_id,
            location_id=kms_location,
            key_ring_id=kms_key_ring,
            key_id=kms_key_id,
        )
        logger.info("✅ Encryption service initialized successfully")

    except Exception as e:
        logger.exception(f"❌ Failed to initialize Google Cloud services: {e}")
        raise

# Telegram configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "test-token")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "test-secret")

# Initialize Telegram Bot for production use
if not TESTING_MODE and TELEGRAM_TOKEN != "test-token":
    from telegram import Bot

    telegram_bot = Bot(token=TELEGRAM_TOKEN)
    logger.info("✅ Telegram Bot initialized for production")
else:
    # Mock bot for testing
    class MockTelegramBot:
        async def send_message(self, chat_id, text, parse_mode=None):
            logger.info(f"🧪 Mock: Would send message to {chat_id}: {text}")
            return {"message_id": 999, "chat": {"id": chat_id}}

    telegram_bot = MockTelegramBot()
    logger.info("🧪 Mock Telegram Bot initialized for testing")

# Initialize Telegram application (only if not in testing mode)
if not TESTING_MODE and TELEGRAM_TOKEN != "test-token":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
else:
    # Mock Telegram application for testing
    class MockTelegramApp:
        def __init__(self):
            self.bot = None  # Mock bot attribute

        async def process_update(self, update):
            return None

    application = MockTelegramApp()

# Batch size for processing messages
BATCH_SIZE = 500


# Telegram message processing
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        chat = message.chat
        user = message.from_user

        # Encrypt the message text
        encrypted_data = encryption.encrypt_message(message.text)

        # Create message document
        message_data = {
            "message_id": message.message_id,
            "chat_id": chat.id,
            "chat_title": chat.title,
            "user_id": user.id,
            "username": user.username,
            "encrypted_text": encrypted_data,  # Store encrypted data
            "timestamp": datetime.utcnow(),
            "type": "telegram",
        }

        # Store in Firestore
        messages_ref = db.collection("messages")
        messages_ref.add(message_data)

        logger.info(f"💾 Stored encrypted message {message.message_id} to Firestore")

        # Return stored document reference for further processing
        return message_data["message_id"]

    except Exception as e:
        logging.exception(f"Error processing message: {e!s}")
        return None


# Bot response functionality
async def send_message_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a response message with metadata about the received message."""
    try:
        message = update.message
        chat = message.chat
        user = message.from_user

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
        await context.bot.send_message(
            chat_id=chat.id, text=response_text, parse_mode="Markdown"
        )

        logging.info(
            f"Sent response for message {message.message_id} in chat {chat.id}"
        )

    except Exception as e:
        logging.exception(f"Error sending message response: {e!s}")


# Combined message handler for storage and response
async def combined_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages: store to Firestore and send response."""
    # Store the message
    message_id = await process_message(update, context)

    # Send response back to chat
    await send_message_response(update, context)

    return message_id


# Telegram handler for all messages (groups and private)
async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await combined_message_handler(update, context)


# Add Telegram handler (only for real Telegram app)
if hasattr(application, "add_handler"):
    application.add_handler(
        MessageHandler(filters.ALL, group_message_handler)  # Handle all message types
    )


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


@app.route("/webhook/<secret>", methods=["POST"])
def webhook(secret):
    webhook_secret = os.environ.get("WEBHOOK_SECRET", "test-secret")
    if secret != webhook_secret:
        abort(500)  # Return 500 for invalid secret to hide endpoint

    try:
        # Parse the incoming update
        update_data = request.get_json(force=True)
        logger.info(
            f"📨 Received webhook update: {update_data.get('update_id', 'unknown')}"
        )

        if TESTING_MODE:
            # Mock webhook processing for testing
            logger.info("🧪 Mock webhook processing in testing mode")
            return jsonify({"status": "ok"})

        # Parse the Telegram update
        update = Update.de_json(update_data, telegram_bot)

        # Only process message updates
        if not update.message:
            logger.info("⏭️ Skipping non-message update")
            return jsonify({"status": "ok"})

        # Process the message asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Store message and send response
            loop.run_until_complete(handle_telegram_message(update))
            logger.info(
                f"✅ Successfully processed message {update.message.message_id}"
            )
        finally:
            loop.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.exception(f"❌ Error in webhook processing: {e}")
        return jsonify({"error": "Internal server error"}), 500


async def handle_telegram_message(update: Update):
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
            encrypted_data = encryption.encrypt_message(message.text)

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
            messages_ref = db.collection("messages")
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
        await telegram_bot.send_message(
            chat_id=chat.id, text=response_text, parse_mode="Markdown"
        )

        logger.info(
            f"📤 Sent response for message {message.message_id} in chat {chat.id}"
        )

    except Exception as e:
        logger.exception(f"❌ Error handling Telegram message: {e}")
        raise


@app.route("/webhook/<secret>", methods=["GET"])
def webhook_method_not_allowed(secret):
    return "", 405


# New endpoints for message access
@app.route("/messages", methods=["GET"])
def get_messages():
    try:
        # Get query parameters
        chat_id = request.args.get("chat_id")
        user_id = request.args.get("user_id")
        start_after = request.args.get("start_after")
        limit = int(request.args.get("limit", 100))

        # Build query
        query = db.collection("messages")

        # Add filters if provided
        if chat_id:
            query = query.where(filter=FieldFilter("chat_id", "==", int(chat_id)))
        if user_id:
            query = query.where(filter=FieldFilter("user_id", "==", int(user_id)))

        # Add pagination
        if start_after:
            start_after_doc = db.collection("messages").document(start_after).get()
            if start_after_doc.exists:
                query = query.start_after(start_after_doc)

        # Add limit
        query = query.limit(limit)

        # Execute query
        docs = query.stream()

        # Process results
        messages = []
        last_doc = None
        for doc in docs:
            message_data = doc.to_dict()
            # Decrypt message text
            try:
                message_data["text"] = encryption.decrypt_message(
                    message_data["encrypted_text"]
                )
                del message_data[
                    "encrypted_text"
                ]  # Remove encrypted data from response
            except Exception as e:
                logging.exception(f"Error decrypting message: {e!s}")
                message_data["text"] = "[Encrypted]"

            messages.append(
                {
                    "id": doc.id,
                    **message_data,
                }
            )
            last_doc = doc

        # Prepare response
        response = {
            "messages": messages,
            "next_page_token": last_doc.id if last_doc else None,
        }

        return jsonify(response)

    except Exception as e:
        logging.exception(f"Error retrieving messages: {e!s}")
        return jsonify({"error": str(e)}), 500


# Batch processing endpoint
@app.route("/messages/batch", methods=["POST"])
def process_messages_batch():
    try:
        # Get batch parameters
        chat_id = request.json.get("chat_id")
        user_id = request.json.get("user_id")
        batch_size = int(request.json.get("batch_size", BATCH_SIZE))

        # Build query
        query = db.collection("messages")

        # Add filters if provided
        if chat_id:
            query = query.where(filter=FieldFilter("chat_id", "==", int(chat_id)))
        if user_id:
            query = query.where(filter=FieldFilter("user_id", "==", int(user_id)))

        # Execute query
        docs = query.limit(batch_size).stream()

        # Process results
        messages = []
        for doc in docs:
            message_data = doc.to_dict()
            # Decrypt message text
            try:
                message_data["text"] = encryption.decrypt_message(
                    message_data["encrypted_text"]
                )
                del message_data[
                    "encrypted_text"
                ]  # Remove encrypted data from response
            except Exception as e:
                logging.exception(f"Error decrypting message: {e!s}")
                message_data["text"] = "[Encrypted]"

            messages.append(
                {
                    "id": doc.id,
                    **message_data,
                }
            )

        return jsonify(
            {
                "messages": messages,
                "count": len(messages),
            }
        )

    except Exception as e:
        logging.exception(f"Error processing message batch: {e!s}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
