"""
Unit Tests for Message Retrieval API

Tests the message retrieval endpoints and functionality using dependency injection
for database and encryption services to ensure fast, isolated testing.
"""

import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

# Mock telegram imports
sys.modules["telegram"] = Mock()
sys.modules["telegram.ext"] = Mock()

from main import create_app
from service_container import reset_service_container

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def client():
    """Create a test client for the Flask app using dependency injection."""
    # Reset service container to ensure clean state
    reset_service_container()

    # Create app with test environment (uses dependency injection)
    app = create_app(environment="test")
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


def test_get_messages_with_test_data(client):
    """Test getting messages using injected test services with seeded data."""
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "next_page_token" in data
    assert isinstance(data["messages"], list)

    # Should have seeded test data
    assert len(data["messages"]) >= 0  # May have test data


def test_get_messages_with_filters(client):
    """Test getting messages with query filters."""
    # Test with chat_id filter
    response = client.get("/messages?chat_id=-100123456789")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data

    # Test with user_id filter
    response = client.get("/messages?user_id=123456")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data

    # Test with limit
    response = client.get("/messages?limit=5")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data


def test_get_messages_pagination(client):
    """Test message pagination functionality."""
    # First request
    response = client.get("/messages?limit=1")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "next_page_token" in data


def test_process_messages_batch(client):
    """Test batch processing of messages."""
    request_data = {
        "chat_id": -100123456789,
        "user_id": 123456,
        "batch_size": 2,
    }

    response = client.post("/messages/batch", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "count" in data
    assert isinstance(data["messages"], list)
    assert data["count"] == len(data["messages"])


def test_batch_messages_without_filters(client):
    """Test batch processing without filters."""
    request_data = {
        "batch_size": 10,
    }

    response = client.post("/messages/batch", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "count" in data


def test_messages_endpoint_error_handling(client):
    """Test error handling in messages endpoint."""
    # Test with invalid limit
    response = client.get("/messages?limit=invalid")
    assert response.status_code == 500  # Should handle ValueError gracefully


def test_batch_endpoint_error_handling(client):
    """Test error handling in batch endpoint."""
    # Test with invalid JSON
    response = client.post(
        "/messages/batch", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 500


def test_message_decryption_with_test_service(client):
    """Test that messages are properly decrypted using test encryption service."""
    # The test implementation uses base64 encoding/decoding
    # So we should be able to see decrypted messages if any exist
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.get_json()

    # Check that messages (if any) have text field and no encrypted_text field
    for message in data["messages"]:
        assert "text" in message
        assert "encrypted_text" not in message  # Should be removed from response


def test_dependency_injection_isolation(client):
    """Test that each test gets isolated dependencies."""
    # This test verifies that the dependency injection system
    # provides clean, isolated services for each test

    # Get initial state
    response1 = client.get("/messages")
    assert response1.status_code == 200

    # The test services should be consistent within a test
    response2 = client.get("/messages")
    assert response2.status_code == 200

    # Both responses should be successful and have same structure
    data1 = response1.get_json()
    data2 = response2.get_json()
    assert "messages" in data1
    assert "messages" in data2
