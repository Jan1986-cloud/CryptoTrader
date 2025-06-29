"""
Encryption utilities for secure API key storage.

This module provides AES-256 encryption for storing user API keys securely.
Each user's keys are encrypted with a unique key derived from their user ID and app secret.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, app_secret_key):
        """Initialize with app secret key."""
        self.app_secret_key = app_secret_key.encode() if isinstance(app_secret_key, str) else app_secret_key
    
    def _derive_key(self, user_id, salt=None):
        """Derive encryption key for a specific user."""
        if salt is None:
            salt = hashlib.sha256(f"user_{user_id}".encode()).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.app_secret_key))
        return Fernet(key), salt
    
    def encrypt_data(self, data, user_id):
        """Encrypt data for a specific user."""
        try:
            if not data:
                return None, None
            
            fernet, salt = self._derive_key(user_id)
            encrypted_data = fernet.encrypt(data.encode())
            
            # Return base64 encoded encrypted data and salt
            return base64.urlsafe_b64encode(encrypted_data).decode(), base64.urlsafe_b64encode(salt).decode()
        
        except Exception as e:
            logger.error(f"Encryption error for user {user_id}: {str(e)}")
            raise Exception("Failed to encrypt data")
    
    def decrypt_data(self, encrypted_data, salt, user_id):
        """Decrypt data for a specific user."""
        try:
            if not encrypted_data or not salt:
                return None
            
            # Decode base64 data
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            salt_bytes = base64.urlsafe_b64decode(salt.encode())
            
            fernet, _ = self._derive_key(user_id, salt_bytes)
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
        
        except Exception as e:
            logger.error(f"Decryption error for user {user_id}: {str(e)}")
            raise Exception("Failed to decrypt data")
    
    def encrypt_api_credentials(self, api_key, api_secret, passphrase, user_id):
        """Encrypt API credentials for storage."""
        try:
            encrypted_key, salt_key = self.encrypt_data(api_key, user_id)
            encrypted_secret, salt_secret = self.encrypt_data(api_secret, user_id)
            encrypted_passphrase, salt_passphrase = None, None
            
            if passphrase:
                encrypted_passphrase, salt_passphrase = self.encrypt_data(passphrase, user_id)
            
            return {
                'encrypted_key': encrypted_key,
                'salt_key': salt_key,
                'encrypted_secret': encrypted_secret,
                'salt_secret': salt_secret,
                'encrypted_passphrase': encrypted_passphrase,
                'salt_passphrase': salt_passphrase
            }
        
        except Exception as e:
            logger.error(f"API credentials encryption error for user {user_id}: {str(e)}")
            raise Exception("Failed to encrypt API credentials")
    
    def decrypt_api_credentials(self, encrypted_credentials, user_id):
        """Decrypt API credentials for use."""
        try:
            api_key = self.decrypt_data(
                encrypted_credentials['encrypted_key'],
                encrypted_credentials['salt_key'],
                user_id
            )
            
            api_secret = self.decrypt_data(
                encrypted_credentials['encrypted_secret'],
                encrypted_credentials['salt_secret'],
                user_id
            )
            
            passphrase = None
            if encrypted_credentials.get('encrypted_passphrase') and encrypted_credentials.get('salt_passphrase'):
                passphrase = self.decrypt_data(
                    encrypted_credentials['encrypted_passphrase'],
                    encrypted_credentials['salt_passphrase'],
                    user_id
                )
            
            return {
                'api_key': api_key,
                'api_secret': api_secret,
                'passphrase': passphrase
            }
        
        except Exception as e:
            logger.error(f"API credentials decryption error for user {user_id}: {str(e)}")
            raise Exception("Failed to decrypt API credentials")


def get_encryption_manager(app_secret_key):
    """Get encryption manager instance."""
    return EncryptionManager(app_secret_key)


def validate_api_credentials(provider, api_key, api_secret, passphrase=None):
    """Validate API credentials format based on provider."""
    if provider.lower() == 'coinbase':
        # Coinbase API key validation
        if not api_key or len(api_key) < 32:
            return False, "Invalid Coinbase API key format"
        
        if not api_secret or len(api_secret) < 32:
            return False, "Invalid Coinbase API secret format"
        
        if not passphrase or len(passphrase) < 8:
            return False, "Coinbase passphrase is required and must be at least 8 characters"
        
        return True, "Valid Coinbase credentials"
    
    elif provider.lower() == 'binance':
        # Binance API key validation
        if not api_key or len(api_key) < 32:
            return False, "Invalid Binance API key format"
        
        if not api_secret or len(api_secret) < 32:
            return False, "Invalid Binance API secret format"
        
        return True, "Valid Binance credentials"
    
    else:
        return False, f"Unsupported provider: {provider}"


def test_api_connection(provider, credentials):
    """Test API connection with provided credentials."""
    try:
        if provider.lower() == 'coinbase':
            # Test Coinbase connection
            import cbpro
            auth_client = cbpro.AuthenticatedClient(
                credentials['api_key'],
                credentials['api_secret'],
                credentials['passphrase'],
                sandbox=False  # Set to True for testing
            )
            
            # Try to get accounts
            accounts = auth_client.get_accounts()
            if 'message' in accounts:
                return False, f"Coinbase API error: {accounts['message']}"
            
            return True, "Coinbase connection successful"
        
        elif provider.lower() == 'binance':
            # Test Binance connection
            from binance.client import Client
            client = Client(
                credentials['api_key'],
                credentials['api_secret']
            )
            
            # Try to get account info
            account_info = client.get_account()
            return True, "Binance connection successful"
        
        else:
            return False, f"Connection test not implemented for {provider}"
    
    except ImportError:
        return False, f"{provider} client library not installed"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"

