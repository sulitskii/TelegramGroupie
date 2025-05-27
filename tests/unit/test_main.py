"""
Unit Tests for Flask Application Core

Tests the main Flask application functionality including health endpoints,
webhook processing, and message handling using mocks for external dependencies.
"""

import json
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

# Mock telegram imports
sys.modules["telegram"] = Mock()
sys.modules["telegram.ext"] = Mock()

# Mock Firestore and KMS clients before importing main
with (
    patch("google.cloud.firestore.Client") as mock_firestore,
    patch("google.cloud.kms.KeyManagementServiceClient") as mock_kms,
):
    mock_firestore.return_value = Mock()
    mock_kms.return_value = Mock()
    from main import app, process_message


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram update object."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
            },
            "chat": {
                "id": -100123456789,
                "title": "Test Group",
                "type": "group",
            },
            "date": 1234567890,
            "text": "Test message content",
        },
    }


def test_healthz_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_webhook_invalid_method(client):
    """Test webhook endpoint with invalid HTTP method."""
    response = client.get("/webhook/test-secret")
    assert response.status_code == 405  # Method Not Allowed


def test_webhook_valid_request(client, mock_telegram_update):
    """Test webhook endpoint with valid request."""

    # Mock the encryption and database operations
    with patch("main.encryption") as mock_encryption, \
         patch("main.db") as mock_db, \
         patch("main.telegram_bot") as mock_bot:

        # Set up mocks
        mock_encryption.encrypt_message.return_value = {
            "ciphertext": "encrypted_test",
            "encrypted_data_key": "test_key",
            "iv": "test_iv",
            "salt": "test_salt"
        }

        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.add.return_value = (None, Mock())

        mock_bot.send_message = AsyncMock()

        # Mock the TESTING_MODE to False so it processes the webhook
        with patch.dict("os.environ", {"WEBHOOK_SECRET": "test-secret"}), \
             patch("main.TESTING_MODE", False):

            response = client.post(
                "/webhook/test-secret",
                data=json.dumps(mock_telegram_update),
                content_type="application/json",
            )
            assert response.status_code == 200
            assert response.get_json() == {"status": "ok"}


def test_webhook_invalid_secret(client, mock_telegram_update):
    """Test webhook endpoint with invalid secret."""
    with patch.dict("os.environ", {"WEBHOOK_SECRET": "correct-secret"}):
        response = client.post(
            "/webhook/wrong-secret",
            data=json.dumps(mock_telegram_update),
            content_type="application/json",
        )
        assert response.status_code == 500  # Updated to match new behavior


def test_webhook_testing_mode(client, mock_telegram_update):
    """Test webhook endpoint in testing mode."""
    with patch.dict("os.environ", {"WEBHOOK_SECRET": "test-secret"}), \
         patch("main.TESTING_MODE", True):

        response = client.post(
            "/webhook/test-secret",
            data=json.dumps(mock_telegram_update),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_process_message(mock_telegram_update):
    """Test the message processing function."""
    with patch("main.encryption") as mock_encryption, patch("main.db") as mock_db:
        # Set up encryption mock
        mock_encryption.encrypt_message.return_value = {
            "ciphertext": "encrypted",
            "encrypted_data_key": "key",
            "iv": "iv",
            "salt": "salt",
        }

        # Set up database mock
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection

        # Create a proper mock message object that matches telegram.Message structure
        mock_message = Mock()
        mock_message.text = "Test message"
        mock_message.message_id = 1
        mock_message.chat.id = -100123456789
        mock_message.chat.title = "Test Group"
        mock_message.from_user.id = 123456
        mock_message.from_user.username = "testuser"

        # Create mock update
        mock_update = Mock()
        mock_update.message = mock_message

        await process_message(mock_update, None)

        # Verify encryption was called
        mock_encryption.encrypt_message.assert_called_once_with("Test message")

        # Verify database operations
        mock_db.collection.assert_called_once_with("messages")
        mock_collection.add.assert_called_once()
