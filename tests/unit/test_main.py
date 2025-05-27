"""
Unit Tests for Flask Application Core

Tests the main Flask application functionality including health endpoints,
webhook processing, and message handling using dependency injection for
external dependencies.
"""

import json
import sys
from unittest.mock import Mock, patch

import pytest

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

# Mock telegram imports before importing main
sys.modules["telegram"] = Mock()
sys.modules["telegram.ext"] = Mock()

from main import create_app  # noqa: E402
from service_container import reset_service_container  # noqa: E402


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
    """Test webhook endpoint with valid request using dependency injection."""
    with patch.dict("os.environ", {"WEBHOOK_SECRET": "test-secret"}):
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
        assert response.status_code == 500


def test_webhook_no_message_update(client):
    """Test webhook endpoint with update that has no message."""
    update_without_message = {
        "update_id": 123456789,
        "edited_message": {
            "message_id": 1,
            "text": "Edited message",
        },
    }

    with patch.dict("os.environ", {"WEBHOOK_SECRET": "test-secret"}):
        response = client.post(
            "/webhook/test-secret",
            data=json.dumps(update_without_message),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}


def test_webhook_malformed_json(client):
    """Test webhook endpoint with malformed JSON."""
    with patch.dict("os.environ", {"WEBHOOK_SECRET": "test-secret"}):
        response = client.post(
            "/webhook/test-secret",
            data="invalid json",
            content_type="application/json",
        )
        assert response.status_code == 500


def test_messages_endpoint(client):
    """Test the messages retrieval endpoint using injected test services."""
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "next_page_token" in data
    assert isinstance(data["messages"], list)


def test_messages_endpoint_with_filters(client):
    """Test the messages endpoint with query filters."""
    response = client.get("/messages?chat_id=-100123456789&user_id=123456&limit=10")
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert isinstance(data["messages"], list)


def test_messages_batch_endpoint(client):
    """Test the batch messages processing endpoint."""
    request_data = {"chat_id": -100123456789, "user_id": 123456, "batch_size": 5}

    response = client.post(
        "/messages/batch",
        data=json.dumps(request_data),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "messages" in data
    assert "count" in data
    assert isinstance(data["messages"], list)


def test_app_uses_dependency_injection():
    """Test that the app correctly uses dependency injection without TESTING flags."""
    # Reset service container
    reset_service_container()

    # Create test app
    app = create_app(environment="test")

    # Verify the app was created successfully
    assert app is not None
    assert app.config is not None

    # Verify routes exist
    with app.app_context():
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/healthz" in [r for r in routes if "<" not in r]
        assert any("/webhook/" in route for route in routes)
        assert "/messages" in [r for r in routes if "<" not in r]


def test_app_can_be_created_multiple_times():
    """Test that multiple app instances can be created with clean state."""
    # Reset and create first app
    reset_service_container()
    app1 = create_app(environment="test")

    # Reset and create second app
    reset_service_container()
    app2 = create_app(environment="test")

    # Both should work independently
    assert app1 is not None
    assert app2 is not None

    # Test both apps work
    with app1.test_client() as client1:
        response1 = client1.get("/healthz")
        assert response1.status_code == 200

    with app2.test_client() as client2:
        response2 = client2.get("/healthz")
        assert response2.status_code == 200
