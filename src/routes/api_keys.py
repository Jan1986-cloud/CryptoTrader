"""
API Key management routes for the encrypted vault system.

This module provides secure storage and management of user API keys
with AES-256 encryption tied to individual user accounts.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from src.models.user import APIKey, db
from src.utils.encryption import get_encryption_manager, validate_api_credentials, test_api_connection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

api_keys_bp = Blueprint('api_keys', __name__)

@api_keys_bp.route('/api-keys', methods=['GET'])
@login_required
def get_api_keys():
    """Get user's API keys (without sensitive data)."""
    try:
        api_keys = APIKey.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(APIKey.created_at.desc()).all()
        
        return jsonify({
            'api_keys': [key.to_dict() for key in api_keys]
        }), 200
        
    except Exception as e:
        logger.error(f"Get API keys error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve API keys'}), 500

@api_keys_bp.route('/api-keys', methods=['POST'])
@login_required
def add_api_key():
    """Add new API key for the user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['provider', 'api_key', 'api_secret']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        provider = data['provider'].lower()
        api_key = data['api_key'].strip()
        api_secret = data['api_secret'].strip()
        passphrase = data.get('passphrase', '').strip() if data.get('passphrase') else None
        label = data.get('label', f"{provider.title()} API Key").strip()
        test_connection = data.get('test_connection', True)
        
        # Validate API credentials format
        is_valid, message = validate_api_credentials(provider, api_key, api_secret, passphrase)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already has API key for this provider
        existing_key = APIKey.query.filter_by(
            user_id=current_user.id,
            provider=provider,
            is_active=True
        ).first()
        
        if existing_key:
            return jsonify({'error': f'You already have an active {provider.title()} API key'}), 409
        
        # Test API connection if requested
        if test_connection:
            credentials = {
                'api_key': api_key,
                'api_secret': api_secret,
                'passphrase': passphrase
            }
            
            connection_ok, test_message = test_api_connection(provider, credentials)
            if not connection_ok:
                return jsonify({
                    'error': f'API connection test failed: {test_message}',
                    'connection_test_failed': True
                }), 400
        
        # Encrypt API credentials
        encryption_manager = get_encryption_manager(current_app.config['SECRET_KEY'])
        encrypted_credentials = encryption_manager.encrypt_api_credentials(
            api_key, api_secret, passphrase, current_user.id
        )
        
        # Create new API key record
        new_api_key = APIKey(
            user_id=current_user.id,
            provider=provider,
            label=label,
            encrypted_key=f"{encrypted_credentials['encrypted_key']}:{encrypted_credentials['salt_key']}",
            encrypted_secret=f"{encrypted_credentials['encrypted_secret']}:{encrypted_credentials['salt_secret']}",
            encrypted_passphrase=f"{encrypted_credentials['encrypted_passphrase']}:{encrypted_credentials['salt_passphrase']}" if encrypted_credentials['encrypted_passphrase'] else None
        )
        
        db.session.add(new_api_key)
        db.session.commit()
        
        logger.info(f"API key added for user {current_user.id}, provider: {provider}")
        
        return jsonify({
            'message': f'{provider.title()} API key added successfully',
            'api_key': new_api_key.to_dict(),
            'connection_tested': test_connection
        }), 201
        
    except Exception as e:
        logger.error(f"Add API key error for user {current_user.id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add API key'}), 500

@api_keys_bp.route('/api-keys/<int:key_id>', methods=['PUT'])
@login_required
def update_api_key(key_id):
    """Update API key label or test connection."""
    try:
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        data = request.get_json()
        
        # Update label if provided
        if 'label' in data:
            api_key.label = data['label'].strip()
        
        # Test connection if requested
        if data.get('test_connection'):
            credentials = get_decrypted_credentials(api_key)
            if credentials:
                connection_ok, test_message = test_api_connection(api_key.provider, credentials)
                if not connection_ok:
                    return jsonify({
                        'error': f'API connection test failed: {test_message}',
                        'connection_test_failed': True
                    }), 400
                
                # Update last used timestamp
                api_key.last_used = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'API key updated successfully',
            'api_key': api_key.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update API key error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to update API key'}), 500

@api_keys_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete (deactivate) API key."""
    try:
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Soft delete - deactivate instead of actual deletion
        api_key.is_active = False
        db.session.commit()
        
        logger.info(f"API key deactivated for user {current_user.id}, key_id: {key_id}")
        
        return jsonify({'message': 'API key deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete API key error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to delete API key'}), 500

@api_keys_bp.route('/api-keys/<int:key_id>/test', methods=['POST'])
@login_required
def test_api_key(key_id):
    """Test API key connection."""
    try:
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Get decrypted credentials
        credentials = get_decrypted_credentials(api_key)
        if not credentials:
            return jsonify({'error': 'Failed to decrypt API credentials'}), 500
        
        # Test connection
        connection_ok, test_message = test_api_connection(api_key.provider, credentials)
        
        if connection_ok:
            # Update last used timestamp
            api_key.last_used = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': connection_ok,
            'message': test_message,
            'provider': api_key.provider,
            'tested_at': datetime.utcnow().isoformat()
        }), 200 if connection_ok else 400
        
    except Exception as e:
        logger.error(f"Test API key error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to test API key'}), 500

@api_keys_bp.route('/api-keys/providers', methods=['GET'])
@login_required
def get_supported_providers():
    """Get list of supported API providers."""
    providers = [
        {
            'id': 'coinbase',
            'name': 'Coinbase Pro',
            'description': 'Coinbase Pro API for cryptocurrency trading',
            'required_fields': ['api_key', 'api_secret', 'passphrase'],
            'documentation_url': 'https://docs.pro.coinbase.com/',
            'sandbox_available': True
        },
        {
            'id': 'binance',
            'name': 'Binance',
            'description': 'Binance API for cryptocurrency trading',
            'required_fields': ['api_key', 'api_secret'],
            'documentation_url': 'https://binance-docs.github.io/apidocs/',
            'sandbox_available': True
        }
    ]
    
    return jsonify({'providers': providers}), 200

def get_decrypted_credentials(api_key):
    """Helper function to get decrypted credentials for an API key."""
    try:
        encryption_manager = get_encryption_manager(current_app.config['SECRET_KEY'])
        
        # Parse encrypted data and salt
        key_parts = api_key.encrypted_key.split(':')
        secret_parts = api_key.encrypted_secret.split(':')
        
        encrypted_credentials = {
            'encrypted_key': key_parts[0],
            'salt_key': key_parts[1],
            'encrypted_secret': secret_parts[0],
            'salt_secret': secret_parts[1],
            'encrypted_passphrase': None,
            'salt_passphrase': None
        }
        
        if api_key.encrypted_passphrase:
            passphrase_parts = api_key.encrypted_passphrase.split(':')
            encrypted_credentials['encrypted_passphrase'] = passphrase_parts[0]
            encrypted_credentials['salt_passphrase'] = passphrase_parts[1]
        
        return encryption_manager.decrypt_api_credentials(encrypted_credentials, api_key.user_id)
        
    except Exception as e:
        logger.error(f"Decrypt credentials error: {str(e)}")
        return None

def get_user_api_credentials(user_id, provider):
    """Get decrypted API credentials for a user and provider."""
    try:
        api_key = APIKey.query.filter_by(
            user_id=user_id,
            provider=provider.lower(),
            is_active=True
        ).first()
        
        if not api_key:
            return None
        
        # Update last used timestamp
        api_key.last_used = datetime.utcnow()
        db.session.commit()
        
        return get_decrypted_credentials(api_key)
        
    except Exception as e:
        logger.error(f"Get user API credentials error: {str(e)}")
        return None

