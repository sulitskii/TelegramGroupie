"""
Integration Tests for TelegramGroupie

This module contains comprehensive integration tests for the TelegramGroupie
application using mock services for fast, reliable testing without external
dependencies. Tests complete workflows from API endpoints to data storage.
"""

import os
import sys
import threading
import time
from unittest.mock import Mock, patch

import pytest
import requests

# Mock telegram imports for integration tests
sys.modules["telegram"] = Mock()
sys.modules["telegram.ext"] = Mock()

# Mock Google Cloud services for integration tests
with (
    patch("google.cloud.firestore.Client") as mock_firestore,
    patch("google.cloud.kms.KeyManagementServiceClient") as mock_kms,
):
    mock_firestore.return_value = Mock()
    mock_kms.return_value = Mock()
    from main import app

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class IntegrationTestServer:
    """Helper class to manage the test server."""

    def __init__(self, port=5555):
        self.port = port
        self.server_thread = None
        self.base_url = f"http://localhost:{port}"

    def start(self):
        """Start the test server in a separate thread."""

        def run_server():
            app.config["TESTING"] = True
            app.run(host="localhost", port=self.port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Wait for server to start
        for _ in range(10):  # Wait up to 5 seconds
            try:
                response = requests.get(f"{self.base_url}/healthz", timeout=1)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        else:
            raise RuntimeError("Test server failed to start")

    def stop(self):
        """Stop the test server."""
        # The thread will stop when the main process exits


@pytest.fixture(scope="module")
def test_server():
    """Start a test server for integration tests."""
    server = IntegrationTestServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def api_client(test_server):
    """Create an API client for making requests."""
    return test_server.base_url


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_health_check(self, api_client):
        """Test the health check endpoint."""
        response = requests.get(f"{api_client}/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["content-type"].startswith("application/json")


class TestWebhookEndpoints:
    """Test webhook endpoints."""

    def test_webhook_get_method_not_allowed(self, api_client):
        """Test that GET requests to webhook return 405."""
        response = requests.get(f"{api_client}/webhook/test-secret")
        assert response.status_code == 405

    def test_webhook_invalid_secret(self, api_client):
        """Test webhook with invalid secret returns 404."""
        with patch.dict(os.environ, {"WEBHOOK_SECRET": "correct-secret"}):
            response = requests.post(
                f"{api_client}/webhook/wrong-secret",
                json={"update_id": 123, "message": {"text": "test"}},
            )
            assert response.status_code == 404

    @patch("main.application.process_update")
    def test_webhook_valid_request(self, mock_process_update, api_client):
        """Test webhook with valid request."""

        # Mock the async process_update function
        async def mock_coroutine(update):
            return None

        mock_process_update.side_effect = mock_coroutine

        test_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test"},
                "chat": {"id": -100123456789, "title": "Test Group"},
                "date": 1234567890,
                "text": "Test message",
            },
        }

        with patch.dict(os.environ, {"WEBHOOK_SECRET": "test-secret"}):
            response = requests.post(
                f"{api_client}/webhook/test-secret",
                json=test_update,
                headers={"Content-Type": "application/json"},
            )

            assert response.status_code == 200
            assert response.json() == {"status": "ok"}


class TestMessageEndpoints:
    """Test message retrieval endpoints."""

    @patch("main.db")
    @patch("main.encryption")
    def test_get_messages_endpoint(self, mock_encryption, mock_db, api_client):
        """Test the GET /messages endpoint."""
        # Mock database response
        mock_doc1 = Mock()
        mock_doc1.id = "msg1"
        mock_doc1.to_dict.return_value = {
            "message_id": 1,
            "chat_id": -100123456789,
            "user_id": 123456,
            "encrypted_text": {"ciphertext": "encrypted1"},
            "timestamp": "2024-01-01T00:00:00",
        }

        mock_doc2 = Mock()
        mock_doc2.id = "msg2"
        mock_doc2.to_dict.return_value = {
            "message_id": 2,
            "chat_id": -100123456789,
            "user_id": 123456,
            "encrypted_text": {"ciphertext": "encrypted2"},
            "timestamp": "2024-01-01T00:00:01",
        }

        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_db.collection.return_value = mock_query

        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"

        # Make request
        response = requests.get(f"{api_client}/messages")

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["text"] == "Decrypted message"
        assert "encrypted_text" not in data["messages"][0]  # Should be removed

    @patch("main.db")
    @patch("main.encryption")
    def test_get_messages_with_filters(self, mock_encryption, mock_db, api_client):
        """Test the GET /messages endpoint with query parameters."""
        # Mock database response
        mock_doc = Mock()
        mock_doc.id = "msg1"
        mock_doc.to_dict.return_value = {
            "message_id": 1,
            "chat_id": -100123456789,
            "user_id": 123456,
            "encrypted_text": {"ciphertext": "encrypted1"},
            "timestamp": "2024-01-01T00:00:00",
        }

        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_db.collection.return_value = mock_query

        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"

        # Make request with filters
        response = requests.get(
            f"{api_client}/messages",
            params={"chat_id": -100123456789, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 1

    @patch("main.db")
    @patch("main.encryption")
    def test_messages_batch_endpoint(self, mock_encryption, mock_db, api_client):
        """Test the POST /messages/batch endpoint."""
        # Mock database response
        mock_doc = Mock()
        mock_doc.id = "msg1"
        mock_doc.to_dict.return_value = {
            "message_id": 1,
            "chat_id": -100123456789,
            "user_id": 123456,
            "encrypted_text": {"ciphertext": "encrypted1"},
            "timestamp": "2024-01-01T00:00:00",
        }

        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_db.collection.return_value = mock_query

        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"

        # Make batch request
        response = requests.post(
            f"{api_client}/messages/batch",
            json={
                "chat_id": -100123456789,
                "user_id": 123456,
                "batch_size": 10,
            },
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data
        assert data["count"] == 1


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint(self, api_client):
        """Test accessing invalid endpoint returns 404."""
        response = requests.get(f"{api_client}/invalid-endpoint")
        assert response.status_code == 404

    @patch("main.db")
    def test_messages_endpoint_error(self, mock_db, api_client):
        """Test error handling in messages endpoint."""
        # Mock database to raise an exception
        mock_db.collection.side_effect = Exception("Database error")

        response = requests.get(f"{api_client}/messages")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestPerformance:
    """Basic performance tests."""

    def test_health_endpoint_response_time(self, api_client):
        """Test that health endpoint responds quickly."""
        start_time = time.time()
        response = requests.get(f"{api_client}/healthz")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond in less than 1 second


@pytest.mark.requires_auth
class TestAuthenticatedEndpoints:
    """Tests that require actual authentication (marked for optional running)."""

    def test_real_firestore_connection(self, api_client):
        """Test with real Firestore connection (requires auth)."""
        # This test would use real Google Cloud credentials
        # Only run if GOOGLE_APPLICATION_CREDENTIALS is set
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            pytest.skip("Requires real Google Cloud credentials")

        # Test would go here


if __name__ == "__main__":
    # Run integration tests directly
    pytest.main([__file__, "-v"])
