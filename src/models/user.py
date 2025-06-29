from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets
import string

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for SaaS authentication and subscription management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Email verification
    email_verification_token = db.Column(db.String(100), unique=True)
    email_verification_expires = db.Column(db.DateTime)
    
    # Password reset
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
    
    # Subscription management
    subscription_status = db.Column(db.String(50), default='inactive')  # inactive, active, cancelled, past_due
    subscription_id = db.Column(db.String(255))  # Stripe subscription ID
    stripe_customer_id = db.Column(db.String(255))  # Stripe customer ID
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    analysis_cache = db.relationship('AnalysisCache', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        """Generate email verification token."""
        self.email_verification_token = self._generate_token()
        self.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        return self.email_verification_token
    
    def verify_email_token(self, token):
        """Verify email verification token."""
        if (self.email_verification_token == token and 
            self.email_verification_expires and 
            datetime.utcnow() < self.email_verification_expires):
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_expires = None
            return True
        return False
    
    def generate_password_reset_token(self):
        """Generate password reset token."""
        self.password_reset_token = self._generate_token()
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify password reset token."""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            datetime.utcnow() < self.password_reset_expires):
            return True
        return False
    
    def reset_password(self, new_password):
        """Reset password and clear reset token."""
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def _generate_token(self):
        """Generate a secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def has_active_subscription(self):
        """Check if user has an active subscription."""
        return (self.subscription_status == 'active' and 
                self.subscription_end and 
                datetime.utcnow() < self.subscription_end)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def get_full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'subscription_status': self.subscription_status,
            'has_active_subscription': self.has_active_subscription(),
            'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None,
        }
        
        if include_sensitive:
            data.update({
                'stripe_customer_id': self.stripe_customer_id,
                'subscription_id': self.subscription_id
            })
        
        return data


class APIKey(db.Model):
    """Encrypted API key storage for users."""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # API provider information
    provider = db.Column(db.String(50), nullable=False)  # 'coinbase', 'binance', etc.
    label = db.Column(db.String(100))  # User-friendly label
    
    # Encrypted credentials
    encrypted_key = db.Column(db.Text, nullable=False)
    encrypted_secret = db.Column(db.Text, nullable=False)
    encrypted_passphrase = db.Column(db.Text)  # For Coinbase Pro
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<APIKey {self.provider} for User {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary (without sensitive data)."""
        return {
            'id': self.id,
            'provider': self.provider,
            'label': self.label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active
        }


class AnalysisCache(db.Model):
    """Cache for AI analysis results."""
    
    __tablename__ = 'analysis_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Analysis metadata
    symbol = db.Column(db.String(20), nullable=False)
    timeframe = db.Column(db.String(10), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    
    # Analysis data (JSON)
    analysis_data = db.Column(db.JSON, nullable=False)
    
    # Cache metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<AnalysisCache {self.symbol} for User {self.user_id}>'
    
    def is_expired(self):
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'analysis_type': self.analysis_type,
            'analysis_data': self.analysis_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }


class UserSession(db.Model):
    """User session management."""
    
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session data
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Session status
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<UserSession {self.session_token[:8]}... for User {self.user_id}>'
    
    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'session_token': self.session_token,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }

