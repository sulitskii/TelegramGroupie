"""TelegramGroupie - Refactored Main Application

This is the main Flask application that handles Telegram webhooks and
provides message storage/retrieval APIs. It uses dependency injection
to work identically in all environments without conditional logic.

Key improvements:
- No TESTING flag or conditional logic in application code
- Uses dependency injection for all external services
- Application logic is identical in production and testing
- Clean separation of concerns through interfaces
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


def create_app(environment: str | None = None) -> Flask:
    """Application factory that creates and configures the Flask app.

    Args:
        environment: The environment to create the app for ('production', 'test',
                    or None for auto-detect)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Initialize service container with dependency injection
    logger.info("🚀 Initializing TelegramGroupie application...")
    service_container = initialize_service_container(environment)
    logger.info("✅ TelegramGroupie application initialized successfully")

    # Batch size for processing messages
    batch_size = 500

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """Health check endpoint."""
        return jsonify({"status": "ok"})

    @app.route("/webhook/<secret>", methods=["POST"])
    def webhook(secret):
        """Webhook endpoint for receiving Telegram updates.

        This endpoint works identically in all environments because
        the services are injected through the service container.
        """
        webhook_secret = os.environ.get("WEBHOOK_SECRET", "test-secret")
        if secret != webhook_secret:
            abort(500)  # Return 500 for invalid secret to hide endpoint

        try:
            # Parse the incoming update
            update_data = request.get_json(force=True)
            logger.info(
                f"📨 Received webhook update: {update_data.get('update_id', 'unknown')}"
            )

            # Get services from container (no conditional logic!)
            message_handler = service_container.get_message_handler()
            update_parser = service_container.get_telegram_update_parser()

            # Parse the Telegram update
            update = update_parser.parse_update(update_data)

            # Only process message updates
            if not update.message:
                logger.info("⏭️ Skipping non-message update")
                return jsonify({"status": "ok"})

            # Process the message asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Handle message using injected handler
                loop.run_until_complete(message_handler.handle_message(update))
                logger.info(
                    f"✅ Successfully processed message {update.message.message_id}"
                )
            finally:
                loop.close()

            return jsonify({"status": "ok"})

        except Exception as e:
            logger.exception(f"❌ Error in webhook processing: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/webhook/<secret>", methods=["GET"])
    def webhook_method_not_allowed(secret):
        """Handle GET requests to webhook endpoint."""
        return "", 405

    @app.route("/messages", methods=["GET"])
    def get_messages():
        """Retrieve messages with optional filtering.

        Query parameters:
        - chat_id: Filter by chat ID
        - user_id: Filter by user ID
        - start_after: Pagination token
        - limit: Maximum number of results (default: 100)
        """
        try:
            # Get services from container
            db_client = service_container.get_database_client()
            encryption_service = service_container.get_encryption_service()
            field_filter_factory = service_container.get_field_filter_factory()

            # Get query parameters
            chat_id = request.args.get("chat_id")
            user_id = request.args.get("user_id")
            start_after = request.args.get("start_after")
            limit = int(request.args.get("limit", 100))

            # Build query
            query = db_client.collection("messages")

            # Add filters if provided
            if chat_id:
                filter_obj = field_filter_factory.create_filter(
                    "chat_id", "==", int(chat_id)
                )
                query = query.where(filter=filter_obj)
            if user_id:
                filter_obj = field_filter_factory.create_filter(
                    "user_id", "==", int(user_id)
                )
                query = query.where(filter=filter_obj)

            # Add pagination
            if start_after:
                start_after_doc = db_client.collection("messages").document(start_after)
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
                    message_data["text"] = encryption_service.decrypt_message(
                        message_data["encrypted_text"]
                    )
                    del message_data[
                        "encrypted_text"
                    ]  # Remove encrypted data from response
                except Exception as e:
                    logging.exception(f"Error decrypting message: {e}")
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
            logging.exception(f"Error retrieving messages: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/messages/batch", methods=["POST"])
    def process_messages_batch():
        """Process messages in batch.

        Request body:
        - chat_id: Filter by chat ID (optional)
        - user_id: Filter by user ID (optional)
        - batch_size: Number of messages to process (default: batch_size)
        """
        try:
            # Get services from container
            db_client = service_container.get_database_client()
            encryption_service = service_container.get_encryption_service()
            field_filter_factory = service_container.get_field_filter_factory()

            # Get batch parameters
            chat_id = request.json.get("chat_id")
            user_id = request.json.get("user_id")
            requested_batch_size = int(request.json.get("batch_size", batch_size))

            # Build query
            query = db_client.collection("messages")

            # Add filters if provided
            if chat_id:
                filter_obj = field_filter_factory.create_filter(
                    "chat_id", "==", int(chat_id)
                )
                query = query.where(filter=filter_obj)
            if user_id:
                filter_obj = field_filter_factory.create_filter(
                    "user_id", "==", int(user_id)
                )
                query = query.where(filter=filter_obj)

            # Execute query
            docs = query.limit(requested_batch_size).stream()

            # Process results
            messages = []
            for doc in docs:
                message_data = doc.to_dict()
                # Decrypt message text
                try:
                    message_data["text"] = encryption_service.decrypt_message(
                        message_data["encrypted_text"]
                    )
                    del message_data[
                        "encrypted_text"
                    ]  # Remove encrypted data from response
                except Exception as e:
                    logging.exception(f"Error decrypting message: {e}")
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
            logging.exception(f"Error processing message batch: {e}")
            return jsonify({"error": str(e)}), 500

    return app


# Only create app when running directly, not during imports
def get_app():
    """Get or create the Flask app instance."""
    return create_app()


if __name__ == "__main__":
    # When running directly, create app for the current environment
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
