"""Mock encryption implementation for testing"""

import base64
from typing import Any


class MockMessageEncryption:
    """Mock encryption class for testing"""

    def __init__(
        self, project_id=None, location_id=None, key_ring_id=None, key_id=None
    ):
        # Store parameters for testing purposes
        self.project_id = project_id or "test-project"
        self.location_id = location_id or "global"
        self.key_ring_id = key_ring_id or "test-key-ring"
        self.key_id = key_id or "test-key"

        # Mock encryption key (in real implementation, this would be from KMS)
        self.mock_key = "mock_encryption_key_for_testing"

    def encrypt_message(self, plaintext: str) -> dict[str, Any]:
        """Mock encryption that base64 encodes the text
        In real implementation, this would use Google Cloud KMS
        """
        if not plaintext:
            return {
                "ciphertext": "",
                "encrypted_data_key": "",
                "iv": "",
                "salt": "",
            }

        # Simple base64 encoding as mock encryption
        mock_ciphertext = base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")

        return {
            "ciphertext": mock_ciphertext,
            "encrypted_data_key": f"mock_key_{len(plaintext)}",
            "iv": f"mock_iv_{hash(plaintext) % 1000}",
            "salt": f"mock_salt_{len(plaintext)}",
        }

    def decrypt_message(self, encrypted_data: dict[str, Any]) -> str:
        """Mock decryption that base64 decodes the text
        In real implementation, this would use Google Cloud KMS
        """
        if not encrypted_data or not encrypted_data.get("ciphertext"):
            return ""

        try:
            # Simple base64 decoding as mock decryption
            ciphertext = encrypted_data["ciphertext"]

            # Handle both string and dict formats for encrypted data
            if isinstance(ciphertext, dict):
                # If it's already a dict, extract the actual ciphertext
                ciphertext = ciphertext.get("ciphertext", "")

            if not ciphertext:
                return "[Mock: Empty encrypted data]"

            # Mock decryption using base64 decode
            try:
                decrypted_bytes = base64.b64decode(ciphertext.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
            except Exception:
                # If base64 decode fails, return mock decrypted text
                return f"[Mock: Decrypted] {ciphertext[:50]}..."

        except Exception as e:
            return f"[Mock: Decryption Error] {e!s}"

    def get_key_info(self) -> dict[str, str]:
        """Return mock key information"""
        return {
            "project_id": self.project_id,
            "location_id": self.location_id,
            "key_ring_id": self.key_ring_id,
            "key_id": self.key_id,
            "key_path": f"projects/{self.project_id}/locations/{self.location_id}/keyRings/{self.key_ring_id}/cryptoKeys/{self.key_id}",
        }
