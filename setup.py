#!/usr/bin/env python3

"""
Setup script for the Cryptocurrency Trading System.

This script installs all required dependencies and sets up the project structure.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages."""
    print("Installing required dependencies...")
    
    requirements = [
        "pandas",
        "numpy",
        "requests",
        "matplotlib",
        "plotly",
        "dash",
        "dash-bootstrap-components",
        "ta",  # Technical analysis library
        "python-dotenv",
        "pytest",
        "pytest-cov",
        "black",  # Code formatter
        "isort",  # Import sorter
        "flake8",  # Linter
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + requirements)
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories if they don't exist."""
    print("Creating project directories...")
    
    # Define directories to create
    directories = [
        "data",
        "data/historical",
        "data/backtest_results",
        "logs",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
    ]
    
    # Create directories
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    
    return True

def create_env_file():
    """Create a template .env file for configuration."""
    print("Creating .env template file...")
    
    env_content = """# Cryptocurrency Trading System Environment Variables

# API Keys (replace with your actual keys)
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_trading
DB_USER=postgres
DB_PASSWORD=password

# Application Settings
LOG_LEVEL=INFO
DEMO_MODE=True
"""
    
    try:
        with open(".env.template", "w") as f:
            f.write(env_content)
        print("Created .env.template file")
        return True
    except Exception as e:
        print(f"Error creating .env.template file: {e}")
        return False

def setup_project():
    """Run the full setup process."""
    print("Setting up Cryptocurrency Trading System...")
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Setup aborted.")
        return False
    
    # Create directories
    if not create_directories():
        print("Failed to create directories. Setup aborted.")
        return False
    
    # Create .env template
    if not create_env_file():
        print("Failed to create .env template. Setup aborted.")
        return False
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and add your API keys")
    print("2. Run integration_test.py to verify the setup")
    print("3. Run src/main.py to start the application")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)
