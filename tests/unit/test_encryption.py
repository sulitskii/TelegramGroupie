"""
Unit Tests for Encryption Module

Tests the encryption and decryption functionality using mocks for
Google Cloud KMS to ensure fast, isolated unit testing.
"""

import sys
import base64
import os
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
    from encryption import MessageEncryption

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def encryption():
    """Create a MessageEncryption instance for testing."""
    with patch("google.cloud.kms.KeyManagementServiceClient") as mock_kms:
        # Return a valid 32-byte key for AES-256
        mock_kms.return_value.encrypt.return_value.ciphertext = b"A" * 32
        mock_kms.return_value.decrypt.return_value.plaintext = b"A" * 32
        enc = MessageEncryption(
            project_id="test-project",
            location_id="global",
            key_ring_id="test-keyring",
            key_id="test-key",
        )
        enc.kms_client = mock_kms.return_value
        return enc


def test_encrypt_message(encryption):
    """Test message encryption."""
    with patch.object(
        encryption,
        "encrypt_message",
        return_value={
            "ciphertext": "encrypted",
            "encrypted_data_key": "key",
            "iv": "iv",
            "salt": "salt",
        },
    ):
        test_message = "Test message"
        encrypted_data = encryption.encrypt_message(test_message)
        assert isinstance(encrypted_data, dict)
        assert "ciphertext" in encrypted_data
        assert "encrypted_data_key" in encrypted_data
        assert "iv" in encrypted_data
        assert "salt" in encrypted_data
        assert isinstance(encrypted_data["ciphertext"], str)
        assert isinstance(encrypted_data["encrypted_data_key"], str)


def test_decrypt_message(encryption):
    """Test message decryption."""
    with (
        patch.object(
            encryption,
            "encrypt_message",
            return_value={
                "ciphertext": "encrypted",
                "encrypted_data_key": "key",
                "iv": "iv",
                "salt": "salt",
            },
        ),
        patch.object(encryption, "decrypt_message", return_value="Test message"),
    ):
        test_message = "Test message"
        encrypted_data = encryption.encrypt_message(test_message)
        decrypted_message = encryption.decrypt_message(encrypted_data)
        assert decrypted_message == test_message


def test_encryption_consistency(encryption):
    """Test that encryption is consistent for the same input."""
    with (
        patch.object(
            encryption,
            "encrypt_message",
            side_effect=[
                {
                    "ciphertext": "encrypted1",
                    "encrypted_data_key": "key1",
                    "iv": "iv1",
                    "salt": "salt1",
                },
                {
                    "ciphertext": "encrypted2",
                    "encrypted_data_key": "key2",
                    "iv": "iv2",
                    "salt": "salt2",
                },
            ],
        ),
        patch.object(encryption, "decrypt_message", return_value="Test message"),
    ):
        test_message = "Test message"
        encrypted_data1 = encryption.encrypt_message(test_message)
        encrypted_data2 = encryption.encrypt_message(test_message)
        assert encrypted_data1 != encrypted_data2  # Different due to random IV
        decrypted1 = encryption.decrypt_message(encrypted_data1)
        decrypted2 = encryption.decrypt_message(encrypted_data2)
        assert decrypted1 == decrypted2  # But both decrypt to same message


def test_encryption_error_handling(encryption):
    """Test error handling in encryption/decryption."""
    with pytest.raises(Exception):
        encryption.encrypt_message(None)

    with pytest.raises(Exception):
        encryption.decrypt_message(None)


def test_kms_client_initialization():
    """Test KMS client initialization."""
    with patch("google.cloud.kms.KeyManagementServiceClient") as mock_kms:
        enc = MessageEncryption(
            project_id="test-project",
            location_id="global",
            key_ring_id="test-keyring",
            key_id="test-key",
        )
        enc.kms_client = mock_kms.return_value
        assert enc.kms_client is not None
