"""Docker-based Integration Tests for TelegramGroupie

This module contains Docker-based integration tests for the TelegramGroupie
application, testing containerized deployment scenarios and service interactions.
"""

import os
import time

import pytest
import requests

# Environment configuration for Docker testing
APP_URL = os.environ.get("APP_URL", "http://app:8080")
FIRESTORE_EMULATOR_HOST = os.environ.get(
    "FIRESTORE_EMULATOR_HOST", "firestore-emulator:8081"
)


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
    print(f"🔥 Firestore Emulator: {FIRESTORE_EMULATOR_HOST}")

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
class TestDockerHealthEndpoints:
    """Test health and status endpoints in Docker environment."""

    def test_health_check(self, api_client):
        """Test the health check endpoint."""
        response = requests.get(f"{api_client}/healthz", timeout=10)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["content-type"].startswith("application/json")

    def test_health_endpoint_performance(self, api_client):
        """Test that health endpoint performs well in Docker."""
        start_time = time.time()
        response = requests.get(f"{api_client}/healthz", timeout=10)
        end_time = time.time()

        assert response.status_code == 200
        # Allow more time in Docker environment
        assert (end_time - start_time) < 5.0


@pytest.mark.docker
class TestDockerWebhookEndpoints:
    """Test webhook endpoints in Docker environment."""

    def test_webhook_get_method_not_allowed(self, api_client):
        """Test that GET requests to webhook return 405."""
        response = requests.get(f"{api_client}/webhook/test-secret", timeout=10)
        assert response.status_code == 405

    def test_webhook_invalid_secret(self, api_client):
        """Test webhook with invalid secret returns 404."""
        response = requests.post(
            f"{api_client}/webhook/wrong-secret",
            json={"update_id": 123, "message": {"text": "test"}},
            timeout=10,
        )
        assert response.status_code == 404

    def test_webhook_valid_request(self, api_client):
        """Test webhook with valid request in Docker environment."""
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


@pytest.mark.docker
class TestDockerMessageEndpoints:
    """Test message retrieval endpoints in Docker environment."""

    def test_get_messages_endpoint(self, api_client):
        """Test the GET /messages endpoint in Docker."""
        response = requests.get(f"{api_client}/messages", timeout=10)

        # Should return 200 even with empty results
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_messages_with_filters(self, api_client):
        """Test the GET /messages endpoint with query parameters."""
        response = requests.get(
            f"{api_client}/messages",
            params={"chat_id": -100123456789, "limit": 10},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_messages_batch_endpoint(self, api_client):
        """Test the POST /messages/batch endpoint."""
        response = requests.post(
            f"{api_client}/messages/batch",
            json={
                "chat_id": -100123456789,
                "user_id": 123456,
                "batch_size": 10,
            },
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data
        assert isinstance(data["messages"], list)
        assert isinstance(data["count"], int)


@pytest.mark.docker
class TestDockerErrorHandling:
    """Test error handling and edge cases in Docker environment."""

    def test_invalid_endpoint(self, api_client):
        """Test accessing invalid endpoint returns 404."""
        response = requests.get(f"{api_client}/invalid-endpoint", timeout=10)
        assert response.status_code == 404

    def test_malformed_json_request(self, api_client):
        """Test handling of malformed JSON requests."""
        response = requests.post(
            f"{api_client}/messages/batch",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        # Should handle the error gracefully
        assert response.status_code in [400, 500]


@pytest.mark.docker
class TestDockerNetworking:
    """Test Docker networking and service communication."""

    def test_concurrent_requests(self, api_client):
        """Test that the application can handle concurrent requests."""
        import concurrent.futures

        def make_request():
            try:
                response = requests.get(f"{api_client}/healthz", timeout=10)
                return response.status_code == 200
            except:
                return False

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Most requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8  # At least 80% success rate

    def test_service_discovery(self, api_client):
        """Test that services can communicate within Docker network."""
        # This test verifies that our app can reach its dependencies
        response = requests.get(f"{api_client}/healthz", timeout=10)
        assert response.status_code == 200

        # The fact that we can get a response means Docker networking is working


@pytest.mark.docker
class TestDockerFirestoreIntegration:
    """Test Firestore emulator integration in Docker."""

    def test_firestore_emulator_connection(self, api_client):
        """Test that the application can connect to Firestore emulator."""
        # Test an endpoint that would use Firestore
        response = requests.get(f"{api_client}/messages", timeout=10)

        # Should not fail due to Firestore connection issues
        assert response.status_code == 200

    def test_database_operations(self, api_client):
        """Test basic database operations through the API."""
        # Test retrieving messages (should work even if empty)
        response = requests.get(f"{api_client}/messages", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert "messages" in data


@pytest.mark.docker
@pytest.mark.performance
class TestDockerPerformance:
    """Performance tests in Docker environment."""

    def test_response_times(self, api_client):
        """Test response times are reasonable in Docker."""
        endpoints = [
            "/healthz",
            "/messages",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{api_client}{endpoint}", timeout=10)
            end_time = time.time()

            assert response.status_code in [200, 404]  # 404 is ok for some endpoints
            # Allow longer response times in Docker
            assert (end_time - start_time) < 10.0


if __name__ == "__main__":
    # Run Docker integration tests directly
    pytest.main([__file__, "-v", "--tb=short"])
