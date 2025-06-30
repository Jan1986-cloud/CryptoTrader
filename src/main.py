import os
import sys
from datetime import datetime
# DON'T CHANGE: Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_login import LoginManager, current_user
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime
import logging

# Import configuration
from config import config

# Import models
from src.models.user import db, User, UserSession

# Import blueprints
from src.routes.auth import auth_bp
from src.routes.api_keys import api_keys_bp
from src.routes.analysis import analysis_bp
from src.routes.payments import payments_bp

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, '..', 'frontend', 'dist')
    app = Flask(__name__, static_folder=dist_dir, static_url_path='')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        return User.query.get(int(user_id))
    
    @login_manager.request_loader
    def load_user_from_request(request):
        """Load user from session token."""
        # Check session token
        session_token = request.headers.get('Authorization')
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]  # Remove 'Bearer ' prefix
            
            user_session = UserSession.query.filter_by(
                session_token=session_token,
                is_active=True
            ).first()
            
            if user_session and not user_session.is_expired():
                # Update last activity
                user_session.last_activity = datetime.utcnow()
                db.session.commit()
                return User.query.get(user_session.user_id)
        
        return None
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    
    # Initialize database migrations
    migrate = Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_keys_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    
    # Create database tables
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization warning: {e}")
        print("Application will continue without database (suitable for testing)")
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Railway."""
        return jsonify({
            'status': 'healthy',
            'app': app.config['APP_NAME'],
            'environment': app.config['FLASK_ENV']
        }), 200
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'app_name': app.config['APP_NAME'],
            'environment': app.config['FLASK_ENV'],
            'version': '1.0.0',
            'endpoints': {
                'authentication': '/api/auth',
                'health': '/api/health'
            }
        }), 200
    
    # Subscription check middleware
    @app.before_request
    def check_subscription():
        """Check subscription status for protected routes."""
        # Skip subscription check for certain routes
        skip_routes = [
            '/api/health',
            '/api/info',
            '/api/auth',
            '/static',
            '/'
        ]
        
        # Check if route should be skipped
        for skip_route in skip_routes:
            if request.path.startswith(skip_route):
                return
        
        # Check if user is authenticated and has active subscription
        if current_user.is_authenticated:
            if not current_user.has_active_subscription():
                return jsonify({
                    'error': 'Active subscription required',
                    'subscription_required': True,
                    'subscription_status': current_user.subscription_status
                }), 402  # Payment Required
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    # Static file serving
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        """Serve static files and SPA routes."""
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({'error': 'Static folder not configured'}), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({'error': 'Frontend not found'}), 404
    
    return app

# Create app instance only when running directly
def get_app():
    return create_app()

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # For WSGI servers
    app = None

