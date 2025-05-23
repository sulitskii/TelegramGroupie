import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import base64
import os
from datetime import datetime

# Mock telegram imports
sys.modules['telegram'] = Mock()
sys.modules['telegram.ext'] = Mock()

# Mock Firestore and KMS clients before importing main
with patch('google.cloud.firestore.Client') as mock_firestore, \
     patch('google.cloud.kms.KeyManagementServiceClient') as mock_kms:
    mock_firestore.return_value = Mock()
    mock_kms.return_value = Mock()
    from main import app, process_message
    from encryption import MessageEncryption

# Fixtures
@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def encryption():
    """Create a MessageEncryption instance for testing."""
    with patch('google.cloud.kms.KeyManagementServiceClient') as mock_kms:
        mock_kms.return_value.encrypt.return_value.ciphertext = b'A'*32
        mock_kms.return_value.decrypt.return_value.plaintext = b'A'*32
        enc = MessageEncryption(
            project_id='test-project',
            location_id='global',
            key_ring_id='test-keyring',
            key_id='test-key'
        )
        enc.kms_client = mock_kms.return_value
        return enc

@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram update object."""
    return {
        'update_id': 123456789,
        'message': {
            'message_id': 1,
            'from': {
                'id': 123456,
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser'
            },
            'chat': {
                'id': -100123456789,
                'title': 'Test Group',
                'type': 'group'
            },
            'date': 1234567890,
            'text': 'Test message'
        }
    }

@pytest.fixture
def mock_firestore_docs():
    """Create mock Firestore documents."""
    return [
        Mock(
            id='1',
            to_dict=lambda: {
                'message_id': 1,
                'chat_id': -100123456789,
                'chat_title': 'Test Group',
                'user_id': 123456,
                'username': 'testuser',
                'encrypted_text': {
                    'ciphertext': 'encrypted1',
                    'encrypted_data_key': 'key1',
                    'iv': 'iv1',
                    'salt': 'salt1'
                },
                'timestamp': datetime.utcnow(),
                'type': 'telegram'
            }
        ),
        Mock(
            id='2',
            to_dict=lambda: {
                'message_id': 2,
                'chat_id': -100123456789,
                'chat_title': 'Test Group',
                'user_id': 123456,
                'username': 'testuser',
                'encrypted_text': {
                    'ciphertext': 'encrypted2',
                    'encrypted_data_key': 'key2',
                    'iv': 'iv2',
                    'salt': 'salt2'
                },
                'timestamp': datetime.utcnow(),
                'type': 'telegram'
            }
        )
    ]

# Encryption Tests
def test_encrypt_message(encryption):
    """Test message encryption."""
    with patch.object(encryption, 'encrypt_message', return_value={
        'ciphertext': 'encrypted',
        'encrypted_data_key': 'key',
        'iv': 'iv',
        'salt': 'salt'
    }):
        test_message = "Test message"
        encrypted_data = encryption.encrypt_message(test_message)
        assert isinstance(encrypted_data, dict)
        assert 'ciphertext' in encrypted_data
        assert 'encrypted_data_key' in encrypted_data
        assert 'iv' in encrypted_data
        assert 'salt' in encrypted_data

def test_decrypt_message(encryption):
    """Test message decryption."""
    with patch.object(encryption, 'encrypt_message', return_value={
        'ciphertext': 'encrypted',
        'encrypted_data_key': 'key',
        'iv': 'iv',
        'salt': 'salt'
    }), patch.object(encryption, 'decrypt_message', return_value="Test message"):
        test_message = "Test message"
        encrypted_data = encryption.encrypt_message(test_message)
        decrypted_message = encryption.decrypt_message(encrypted_data)
        assert decrypted_message == test_message

def test_encryption_error_handling(encryption):
    """Test error handling in encryption/decryption."""
    with pytest.raises(Exception):
        encryption.encrypt_message(None)
    
    with pytest.raises(Exception):
        encryption.decrypt_message(None)

# API Endpoint Tests
def test_healthz_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_webhook_invalid_method(client):
    """Test webhook endpoint with invalid HTTP method."""
    response = client.get('/webhook/test-secret')
    assert response.status_code == 405

def test_webhook_valid_request(client, mock_telegram_update):
    """Test webhook endpoint with valid request."""
    async def mock_process_update_coroutine(update):
        return None
    
    with patch('main.application.process_update', new=mock_process_update_coroutine):
        with patch.dict('os.environ', {'WEBHOOK_SECRET': 'test-secret'}):
            response = client.post(
                '/webhook/test-secret',
                data=json.dumps(mock_telegram_update),
                content_type='application/json'
            )
            assert response.status_code == 200
            assert response.get_json() == {'status': 'ok'}

# Message Processing Tests
@pytest.mark.asyncio
async def test_process_message(mock_telegram_update):
    """Test the message processing function."""
    with patch('main.encryption') as mock_encryption, \
         patch('main.db') as mock_db:
        
        # Set up encryption mock
        mock_encryption.encrypt_message.return_value = {
            'ciphertext': 'encrypted',
            'encrypted_data_key': 'key',
            'iv': 'iv',
            'salt': 'salt'
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
        mock_db.collection.assert_called_once_with('messages')
        mock_collection.add.assert_called_once()

# Message Retrieval Tests
def test_get_messages(client, mock_firestore_docs):
    """Test getting messages with various filters."""
    with patch('main.db') as mock_db, \
         patch('main.encryption') as mock_encryption:
        
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs
        mock_db.collection.return_value = mock_query
        
        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"
        
        # Test without filters
        response = client.get('/messages')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['messages']) == 2
        assert 'next_page_token' in data
        
        # Verify all messages have decrypted text
        for message in data['messages']:
            assert 'text' in message
            assert message['text'] == "Decrypted message"
            assert 'encrypted_text' not in message  # Should be removed

def test_process_messages_batch(client, mock_firestore_docs):
    """Test batch processing of messages."""
    with patch('main.db') as mock_db, \
         patch('main.encryption') as mock_encryption:
        
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs
        mock_db.collection.return_value = mock_query
        
        # Mock encryption
        mock_encryption.decrypt_message.return_value = "Decrypted message"
        
        # Test batch processing
        response = client.post('/messages/batch', json={
            'chat_id': -100123456789,
            'user_id': 123456,
            'batch_size': 2
        })
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['messages']) == 2
        assert data['count'] == 2

def test_decryption_error_handling(client, mock_firestore_docs):
    """Test handling of decryption errors."""
    with patch('main.db') as mock_db, \
         patch('main.encryption') as mock_encryption:
        
        # Mock Firestore query
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = mock_firestore_docs
        mock_db.collection.return_value = mock_query
        
        # Mock encryption to raise an error
        mock_encryption.decrypt_message.side_effect = Exception("Decryption failed")
        
        # Test error handling
        response = client.get('/messages')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['messages']) == 2
        
        # All messages should have "[Encrypted]" as text due to decryption failure
        for message in data['messages']:
            assert 'text' in message
            assert message['text'] == "[Encrypted]" 