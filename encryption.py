from google.cloud import kms
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import logging

class MessageEncryption:
    def __init__(self, project_id, location_id, key_ring_id, key_id):
        self.client = kms.KeyManagementServiceClient()
        self.key_name = f"projects/{project_id}/locations/{location_id}/keyRings/{key_ring_id}/cryptoKeys/{key_id}"
        
        # Generate a secure salt for PBKDF2
        self.salt = os.urandom(16)
        
    def _derive_key(self, password):
        """Derive a key from the password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def encrypt_message(self, message):
        """Encrypt a message using Google Cloud KMS"""
        try:
            # Generate a random data key
            data_key = os.urandom(32)
            
            # Encrypt the data key using KMS
            encrypt_request = {
                "name": self.key_name,
                "plaintext": data_key
            }
            encrypt_response = self.client.encrypt(request=encrypt_request)
            encrypted_data_key = encrypt_response.ciphertext
            
            # Generate a random IV
            iv = os.urandom(12)
            
            # Encrypt the message using AES-GCM
            cipher = Cipher(
                algorithms.AES(data_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Add associated data (optional, for additional security)
            encryptor.authenticate_additional_data(b"message")
            
            # Encrypt the message
            ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
            
            # Combine all components
            encrypted_data = {
                'encrypted_data_key': base64.b64encode(encrypted_data_key).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8'),
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
                'salt': base64.b64encode(self.salt).decode('utf-8')
            }
            
            return encrypted_data
            
        except Exception as e:
            logging.error(f"Encryption error: {str(e)}")
            raise

    def decrypt_message(self, encrypted_data):
        """Decrypt a message using Google Cloud KMS"""
        try:
            # Decode the components
            encrypted_data_key = base64.b64decode(encrypted_data['encrypted_data_key'])
            iv = base64.b64decode(encrypted_data['iv'])
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            tag = base64.b64decode(encrypted_data['tag'])
            
            # Decrypt the data key using KMS
            decrypt_request = {
                "name": self.key_name,
                "ciphertext": encrypted_data_key
            }
            decrypt_response = self.client.decrypt(request=decrypt_request)
            data_key = decrypt_response.plaintext
            
            # Decrypt the message using AES-GCM
            cipher = Cipher(
                algorithms.AES(data_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Add associated data (must match encryption)
            decryptor.authenticate_additional_data(b"message")
            
            # Decrypt the message
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logging.error(f"Decryption error: {str(e)}")
            raise 