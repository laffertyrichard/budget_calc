"""
Main API server implementation for the Construction Budget Calculator.
This file defines the Flask application and configures it.
"""

from flask import Flask
from flask_cors import CORS
import logging
import os
from pathlib import Path

# Import routes
from src.api.routes import register_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config=None):
    """Create and configure the Flask application."""
    
    # Create the Flask app
    app = Flask(__name__)
    
    # Enable CORS for all routes and all origins
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    # Add OPTIONS method handler for all routes
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Load configuration
    if config:
        app.config.update(config)
    else:
        # Default configuration
        app.config.update(
            DEBUG=os.environ.get('DEBUG', 'True').lower() == 'true',
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
            DATA_DIR=os.environ.get('DATA_DIR', str(Path(__file__).parent.parent.parent / 'data')),
            CONFIG_DIR=os.environ.get('CONFIG_DIR', str(Path(__file__).parent.parent.parent / 'config'))
        )
    
    # Register routes
    register_routes(app)
    
    logger.info("API Server initialized")
    return app

def run_server():
    """Run the API server."""
    app = create_app()
    host = os.environ.get('HOST', '127.0.0.1')  # Changed to localhost instead of 0.0.0.0
    port = int(os.environ.get('PORT', 5001))  # Ensure the port is set to 5001
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting API server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()