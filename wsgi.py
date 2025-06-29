#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
"""

import os
import sys

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from src.main import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # This is for development only
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

