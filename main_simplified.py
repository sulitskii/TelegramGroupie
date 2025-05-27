"""TelegramGroupie - Simplified Main Application

This is the main Flask application that handles Telegram webhooks and
provides message storage/retrieval APIs. It uses dependency injection
to work identically in all environments without conditional logic.
"""

import asyncio
import logging
import os

from flask import Flask, abort, jsonify, request

from service_container import initialize_service_container

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global service container (set during app creation)
_service_container = None


def get_services():
    """Get the current service container."""
    global _service_container
    if _service_container is None:
        raise RuntimeError("Service container not initialized")
    return _service_container


def healthz():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


def webhook(secret):
    """Webhook endpoint for receiving Telegram updates."""
    webhook_secret = os.environ.get("WEBHOOK_SECRET", "test-secret")
    if secret != webhook_secret:
        abort(500)

    try:
        update_data = request.get_json(force=True)
        logger.info(f"📨 Received webhook update: {update_data.get('update_id', 'unknown')}")

        services = get_services()
        message_handler = services.get_message_handler()
        update_parser = services.get_telegram_update_parser()

        update = update_parser.parse_update(update_data)

        if not update.message:
            logger.info("⏭️ Skipping non-message update")
            return jsonify({"status": "ok"})

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(message_handler.handle_message(update))
            logger.info(f"✅ Successfully processed message {update.message.message_id}")
        finally:
            loop.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.exception(f"❌ Error in webhook processing: {e}")
        return jsonify({"error": "Internal server error"}), 500


def webhook_get(secret):
    """Handle GET requests to webhook endpoint."""
    return "", 405


def build_query(db_client, field_filter_factory, chat_id, user_id):
    """Build message query with filters."""
    query = db_client.collection("messages")

    if chat_id:
        filter_obj = field_filter_factory.create_filter("chat_id", "==", int(chat_id))
        query = query.where(filter=filter_obj)
    if user_id:
        filter_obj = field_filter_factory.create_filter("user_id", "==", int(user_id))
        query = query.where(filter=filter_obj)

    return query


def process_docs(docs, encryption_service):
    """Process and decrypt message documents."""
    messages = []
    last_doc = None
    
    for doc in docs:
        message_data = doc.to_dict()
        try:
            message_data["text"] = encryption_service.decrypt_message(
                message_data["encrypted_text"]
            )
            del message_data["encrypted_text"]
        except Exception as e:
            logging.exception(f"Error decrypting message: {e}")
            message_data["text"] = "[Encrypted]"

        messages.append({"id": doc.id, **message_data})
        last_doc = doc
        
    return messages, last_doc


def get_messages():
    """Retrieve messages with optional filtering."""
    try:
        services = get_services()
        db_client = services.get_database_client()
        encryption_service = services.get_encryption_service()
        field_filter_factory = services.get_field_filter_factory()

        chat_id = request.args.get("chat_id")
        user_id = request.args.get("user_id")
        start_after = request.args.get("start_after")
        limit = int(request.args.get("limit", 100))

        query = build_query(db_client, field_filter_factory, chat_id, user_id)

        if start_after:
            start_after_doc = db_client.collection("messages").document(start_after)
            if start_after_doc.exists:
                query = query.start_after(start_after_doc)

        query = query.limit(limit)
        docs = query.stream()

        messages, last_doc = process_docs(docs, encryption_service)

        response = {
            "messages": messages,
            "next_page_token": last_doc.id if last_doc else None,
        }

        return jsonify(response)

    except Exception as e:
        logging.exception(f"Error retrieving messages: {e}")
        return jsonify({"error": str(e)}), 500


def process_messages_batch():
    """Process messages in batch."""
    try:
        services = get_services()
        db_client = services.get_database_client()
        encryption_service = services.get_encryption_service()
        field_filter_factory = services.get_field_filter_factory()

        chat_id = request.json.get("chat_id")
        user_id = request.json.get("user_id")
        batch_size = int(request.json.get("batch_size", 500))

        query = build_query(db_client, field_filter_factory, chat_id, user_id)
        docs = query.limit(batch_size).stream()

        messages, _ = process_docs(docs, encryption_service)

        return jsonify({"messages": messages, "count": len(messages)})

    except Exception as e:
        logging.exception(f"Error processing message batch: {e}")
        return jsonify({"error": str(e)}), 500


def create_app(environment: str | None = None) -> Flask:
    """Application factory that creates and configures the Flask app."""
    global _service_container
    app = Flask(__name__)

    logger.info("🚀 Initializing TelegramGroupie application...")
    _service_container = initialize_service_container(environment)
    logger.info("✅ TelegramGroupie application initialized successfully")

    app.add_url_rule("/healthz", "healthz", healthz, methods=["GET"])
    app.add_url_rule("/webhook/<secret>", "webhook", webhook, methods=["POST"])
    app.add_url_rule("/webhook/<secret>", "webhook_get", webhook_get, methods=["GET"])
    app.add_url_rule("/messages", "get_messages", get_messages, methods=["GET"])
    app.add_url_rule("/messages/batch", "process_messages_batch", process_messages_batch, methods=["POST"])

    return app


def get_app():
    """Get or create the Flask app instance."""
    return create_app()


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port) 