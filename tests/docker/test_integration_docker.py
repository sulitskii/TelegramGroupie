"""Lightweight Docker Integration Tests for TelegramGroupie

This module contains essential Docker-based integration tests for the TelegramGroupie
application, focusing on core functionality in a containerized environment.
"""

import concurrent.futures
import os
import time

import pytest
import requests

# Environment configuration for Docker testing
APP_URL = os.environ.get("APP_URL", "http://app:8080")

# Mark all tests in this file as docker tests
pytestmark = pytest.mark.docker


def wait_for_service(url, timeout=60, interval=2):
    """Wait for a service to be available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(interval)
    return False


@pytest.fixture(scope="session", autouse=True)
def setup_docker_environment():
    """Setup the Docker test environment."""
    print("🐳 Setting up Docker test environment")
    print(f"📍 App URL: {APP_URL}")

    # Wait for the application to be ready
    health_url = f"{APP_URL}/healthz"
    print(f"⏳ Waiting for application to be ready at {health_url}...")

    if not wait_for_service(health_url, timeout=120):
        pytest.fail(f"Application at {APP_URL} did not become ready in time")

    print("✅ Application is ready for testing!")


@pytest.fixture
def api_client():
    """Create an API client for making requests to the Docker container."""
    return APP_URL


@pytest.mark.docker
class TestDockerCore:
    """Core functionality tests in Docker environment."""

    def test_health_check(self, api_client):
        """Test the health check endpoint."""
        response = requests.get(f"{api_client}/healthz", timeout=10)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_endpoints(self, api_client):
        """Test webhook functionality."""
        # Test invalid secret
        response = requests.post(
            f"{api_client}/webhook/wrong-secret",
            json={"update_id": 123, "message": {"text": "test"}},
            timeout=10,
        )
        assert response.status_code == 404

        # Test valid webhook
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

        response = requests.post(
            f"{api_client}/webhook/test_webhook_secret_123",
            json=test_update,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_message_endpoints(self, api_client):
        """Test message retrieval endpoints."""
        # Test GET messages
        response = requests.get(f"{api_client}/messages", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

        # Test batch endpoint
        response = requests.post(
            f"{api_client}/messages/batch",
            json={"chat_id": -100123456789, "batch_size": 10},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data


@pytest.mark.docker
class TestDockerReliability:
    """Test Docker environment reliability and performance."""

    def test_concurrent_requests(self, api_client):
        """Test concurrent request handling."""

        def make_request():
            try:
                response = requests.get(f"{api_client}/healthz", timeout=10)
                return response.status_code == 200
            except:
                return False

        # Make 5 concurrent requests (lightweight test)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8

    def test_error_handling(self, api_client):
        """Test error handling."""
        # Test 404 for invalid endpoint
        response = requests.get(f"{api_client}/invalid-endpoint", timeout=10)
        assert response.status_code == 404

        # Test malformed JSON handling
        response = requests.post(
            f"{api_client}/messages/batch",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code in [400, 500]

    def test_response_times(self, api_client):
        """Test response times are reasonable."""
        start_time = time.time()
        response = requests.get(f"{api_client}/healthz", timeout=10)
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should respond quickly


if __name__ == "__main__":
    # Run Docker integration tests directly
    pytest.main([__file__, "-v", "--tb=short"])
