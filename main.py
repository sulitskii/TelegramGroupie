import asyncio
import logging
import os
from datetime import datetime

from flask import Flask, abort, jsonify, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

app = Flask(__name__)

# Initialize services based on environment
if os.environ.get("TESTING") == "true":
    # Use mock implementations for testing
    import mock_firestore
    from mock_encryption import MockMessageEncryption

    # Mock Firestore
    db = mock_firestore.Client()

    # Mock encryption
    encryption = MockMessageEncryption(
        project_id=os.environ.get("GCP_PROJECT_ID", "test-project"),
        location_id=os.environ.get("KMS_LOCATION", "global"),
        key_ring_id=os.environ.get("KMS_KEY_RING", "telegram-messages"),
        key_id=os.environ.get("KMS_KEY_ID", "message-key"),
    )

    # Mock FieldFilter for testing
    from mock_firestore import MockFieldFilter as FieldFilter

    print("🧪 Running in TESTING mode with mock implementations")
else:
    # Use real implementations for production
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    from encryption import MessageEncryption

    # Initialize Firestore client
    db = firestore.Client()

    # Initialize encryption
    encryption = MessageEncryption(
        project_id=os.environ.get("GCP_PROJECT_ID"),
        location_id=os.environ.get("KMS_LOCATION", "global"),
        key_ring_id=os.environ.get("KMS_KEY_RING", "telegram-messages"),
        key_id=os.environ.get("KMS_KEY_ID", "message-key"),
    )

# Telegram configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "test-token")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "test-secret")

# Initialize Telegram application (only if not in testing mode)
if os.environ.get("TESTING") != "true" and TELEGRAM_TOKEN != "test-token":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
else:
    # Mock Telegram application for testing
    class MockTelegramApp:
        def __init__(self):
            self.bot = None  # Mock bot attribute

        def process_update(self, update):
            return None

    application = MockTelegramApp()

logging.basicConfig(level=logging.INFO)

# Batch size for processing messages
BATCH_SIZE = 500


# Telegram message processing
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        chat = message.chat

        # Encrypt the message text
        encrypted_data = encryption.encrypt_message(message.text)

        # Create message document
        message_data = {
            "message_id": message.message_id,
            "chat_id": chat.id,
            "chat_title": chat.title,
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "encrypted_text": encrypted_data,  # Store encrypted data
            "timestamp": datetime.utcnow(),
            "type": "telegram",
        }

        # Store in Firestore
        messages_ref = db.collection("messages")
        messages_ref.add(message_data)

        logging.info(
            f"Stored encrypted message {message.message_id} from chat {chat.title}"
        )

    except Exception as e:
        logging.exception(f"Error processing message: {e!s}")


# Telegram handler for all group messages
async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_message(update, context)


# Add Telegram handler (only for real Telegram app)
if hasattr(application, "add_handler"):
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS, group_message_handler)
    )


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


@app.route("/webhook/<secret>", methods=["POST"])
def webhook(secret):
    webhook_secret = os.environ.get("WEBHOOK_SECRET", "test-secret")
    if secret != webhook_secret:
        abort(404)

    if os.environ.get("TESTING") == "true":
        # Mock webhook processing for testing
        return jsonify({"status": "ok"})

    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return jsonify({"status": "ok"})


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
