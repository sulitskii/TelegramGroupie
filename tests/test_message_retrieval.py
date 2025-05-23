import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

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
    from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_firestore_docs():
    """Create mock Firestore documents."""
    return [
        Mock(
            id="1",
            to_dict=lambda: {
                "message_id": 1,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 123456,
                "username": "testuser",
                "encrypted_text": {
                    "ciphertext": "encrypted1",
                    "encrypted_data_key": "key1",
                    "iv": "iv1",
                    "salt": "salt1",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
        ),
        Mock(
            id="2",
            to_dict=lambda: {
                "message_id": 2,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 123456,
                "username": "testuser",
                "encrypted_text": {
                    "ciphertext": "encrypted2",
                    "encrypted_data_key": "key2",
                    "iv": "iv2",
                    "salt": "salt2",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
        ),
        Mock(
            id="3",
            to_dict=lambda: {
                "message_id": 3,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 789012,
                "username": "otheruser",
                "encrypted_text": {
                    "ciphertext": "encrypted3",
                    "encrypted_data_key": "key3",
                    "iv": "iv3",
                    "salt": "salt3",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
        ),
    ]


def test_get_messages(client, mock_firestore_docs):
    """Test getting messages with various filters."""
    with patch("main.db") as mock_db, patch("main.encryption") as mock_encryption:
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs
        mock_db.collection.return_value = mock_query

        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"

        # Test without filters
        response = client.get("/messages")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["messages"]) == 3
        assert "next_page_token" in data

        # Verify all messages have decrypted text
        for message in data["messages"]:
            assert "text" in message
            assert message["text"] == "Decrypted message"
            assert "encrypted_text" not in message  # Should be removed


def test_process_messages_batch(client, mock_firestore_docs):
    """Test batch processing of messages."""
    with patch("main.db") as mock_db, patch("main.encryption") as mock_encryption:
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs[:2]  # Return only first 2
        mock_db.collection.return_value = mock_query

        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"

        # Test batch processing
        response = client.post(
            "/messages/batch",
            json={
                "chat_id": -100123456789,
                "user_id": 123456,
                "batch_size": 2,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["messages"]) == 2
        assert data["count"] == 2

        # Verify all messages have decrypted text
        for message in data["messages"]:
            assert "text" in message
            assert message["text"] == "Decrypted message"


def test_decryption_error_handling(client, mock_firestore_docs):
    """Test handling of decryption errors."""
    with patch("main.db") as mock_db, patch("main.encryption") as mock_encryption:
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs
        mock_db.collection.return_value = mock_query

        # Mock encryption to raise an error
        mock_encryption.decrypt_message.side_effect = Exception("Decryption failed")

        # Test error handling
        response = client.get("/messages")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["messages"]) == 3

        # All messages should have "[Encrypted]" as text due to decryption failure
        for message in data["messages"]:
            assert "text" in message
            assert message["text"] == "[Encrypted]"
