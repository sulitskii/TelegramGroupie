import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from main import app, process_message, webhook, healthz

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
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
                "last_name": "User"
            },
            "chat": {
                "id": -100123456789,
                "title": "Test Group",
                "type": "group"
            },
            "date": 1234567890,
            "text": "Test message"
        }
    }

def test_healthz_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'ok'

def test_webhook_invalid_method(client):
    """Test webhook endpoint with invalid HTTP method."""
    response = client.get('/webhook/test-secret')
    assert response.status_code == 403

@pytest.mark.asyncio
@patch('main.application.process_update')
async def test_webhook_valid_request(mock_process_update, client, mock_telegram_update):
    """Test webhook endpoint with valid request."""
    mock_process_update.return_value = AsyncMock()
    with patch.dict('os.environ', {'WEBHOOK_SECRET': 'test-secret'}):
        response = await client.post(
            '/webhook/test-secret',
            data=json.dumps(mock_telegram_update),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert response.data.decode('utf-8') == 'ok'
        mock_process_update.assert_called_once()

@pytest.mark.asyncio
@patch('main.logging')
async def test_process_message(mock_logging, mock_telegram_update):
    """Test the message processing function."""
    with patch('telegram.Update') as mock_update:
        mock_update.de_json.return_value = Mock(
            message=Mock(text="Test message")
        )
        await process_message(mock_update.de_json.return_value, None)
        mock_logging.info.assert_called_once_with("Received message: Test message") 