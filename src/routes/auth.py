from flask import Blueprint, request, jsonify, session, current_app, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from src.models.user import User, UserSession, db
from datetime import datetime, timedelta
import secrets
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def send_verification_email(user, token):
    """Send email verification email (placeholder - implement with actual email service)."""
    # TODO: Implement with SendGrid or SMTP
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    logger.info(f"Email verification URL for {user.email}: {verification_url}")
    # In production, send actual email here
    return True

def send_password_reset_email(user, token):
    """Send password reset email (placeholder - implement with actual email service)."""
    # TODO: Implement with SendGrid or SMTP
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    logger.info(f"Password reset URL for {user.email}: {reset_url}")
    # In production, send actual email here
    return True

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        # Generate email verification token
        verification_token = user.generate_email_verification_token()
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': user.to_dict(),
            'verification_required': True
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        remember_me = data.get('remember_me', False)
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Check email verification
        if not user.email_verified:
            return jsonify({
                'error': 'Email not verified. Please check your email for verification link.',
                'verification_required': True
            }), 401
        
        # Update last login
        user.update_last_login()
        
        # Create user session
        session_token = secrets.token_urlsafe(32)
        user_session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            expires_at=datetime.utcnow() + timedelta(days=30 if remember_me else 1)
        )
        
        db.session.add(user_session)
        db.session.commit()
        
        # Set session data
        session['user_id'] = user.id
        session['session_token'] = session_token
        session.permanent = remember_me
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'session_token': session_token,
            'requires_subscription': not user.has_active_subscription()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint."""
    try:
        # Deactivate current session
        session_token = session.get('session_token')
        if session_token:
            user_session = UserSession.query.filter_by(
                session_token=session_token,
                user_id=current_user.id
            ).first()
            if user_session:
                user_session.is_active = False
                db.session.commit()
        
        # Clear session
        session.clear()
        logout_user()
        
        logger.info(f"User logged out: {current_user.email}")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification endpoint."""
    try:
        user = User.query.filter_by(email_verification_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid verification token'}), 400
        
        if user.verify_email_token(token):
            db.session.commit()
            logger.info(f"Email verified for user: {user.email}")
            return jsonify({'message': 'Email verified successfully. You can now log in.'}), 200
        else:
            return jsonify({'error': 'Verification token expired or invalid'}), 400
            
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({'error': 'Email verification failed'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.email_verified:
            return jsonify({'error': 'Email already verified'}), 400
        
        # Generate new verification token
        verification_token = user.generate_email_verification_token()
        db.session.commit()
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        return jsonify({'message': 'Verification email sent'}), 200
        
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Failed to resend verification email'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Forgot password endpoint."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate password reset token
            reset_token = user.generate_password_reset_token()
            db.session.commit()
            
            # Send password reset email
            send_password_reset_email(user, reset_token)
            
            logger.info(f"Password reset requested for: {email}")
        
        # Always return success to prevent email enumeration
        return jsonify({'message': 'If the email exists, a password reset link has been sent'}), 200
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'Failed to process password reset request'}), 500

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset endpoint."""
    try:
        user = User.query.filter_by(password_reset_token=token).first()
        
        if not user or not user.verify_password_reset_token(token):
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        if request.method == 'GET':
            # Return token validation status
            return jsonify({'message': 'Valid reset token', 'email': user.email}), 200
        
        # POST - actually reset password
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Reset password
        user.reset_password(new_password)
        db.session.commit()
        
        logger.info(f"Password reset completed for: {user.email}")
        
        return jsonify({'message': 'Password reset successful. You can now log in with your new password.'}), 200
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Password reset failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile."""
    try:
        return jsonify({
            'user': current_user.to_dict(),
            'has_active_subscription': current_user.has_active_subscription()
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user profile."""
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            current_user.last_name = data['last_name'].strip()
        
        db.session.commit()
        
        logger.info(f"Profile updated for: {current_user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for: {current_user.email}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    """Get user's active sessions."""
    try:
        sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.last_activity.desc()).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        return jsonify({'error': 'Failed to get sessions'}), 500

@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def revoke_session(session_id):
    """Revoke a specific session."""
    try:
        user_session = UserSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not user_session:
            return jsonify({'error': 'Session not found'}), 404
        
        user_session.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Session revoked successfully'}), 200
        
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}")
        return jsonify({'error': 'Failed to revoke session'}), 500

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """Check authentication status."""
    try:
        if current_user.is_authenticated:
            return jsonify({
                'authenticated': True,
                'user': current_user.to_dict(),
                'has_active_subscription': current_user.has_active_subscription()
            }), 200
        else:
            return jsonify({'authenticated': False}), 200
            
    except Exception as e:
        logger.error(f"Check auth error: {str(e)}")
        return jsonify({'authenticated': False}), 200

