"""
API routes for the Construction Budget Calculator.
This file defines all the HTTP endpoints for interacting with the estimation engine.
"""

from flask import request, jsonify, Blueprint, current_app
import logging
import json
import os
from pathlib import Path

# Import core estimation functionality
from src.core.estimation_engine import EstimationEngine
from src.core.data_loader import DataLoader

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_blueprint = Blueprint('api', __name__)

# Initialize the estimation engine
estimation_engine = None

def get_estimation_engine():
    """Get or create the estimation engine instance."""
    global estimation_engine
    if estimation_engine is None:
        config_path = os.path.join(current_app.config['CONFIG_DIR'], 'settings.json')
        estimation_engine = EstimationEngine(config_path)
    return estimation_engine

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    try:
        # Initialize the estimation engine to check config
        engine = get_estimation_engine()
        
        # Get available estimators
        available_estimators = [name for name, estimator in engine.estimators.items() if estimator is not None]
        
        return jsonify({
            'status': 'ok',
            'message': 'Construction Budget Calculator API is operational',
            'available_estimators': available_estimators,
            'config_loaded': engine.config is not None and len(engine.config) > 0,
            'catalog_loaded': engine.catalog is not None and not engine.catalog.empty
        }), 200
    except Exception as e:
        logger.exception(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error during health check: {str(e)}'
        }), 500

@api_blueprint.route('/estimate', methods=['POST'])
def create_estimate():
    """
    Create a new construction cost estimate.
    
    Request JSON format:
    {
        "square_footage": 5000,
        "tier": "Premium", // Optional, defaults to value based on square footage
        "bedroom_count": 4,
        "primary_bath_count": 1,
        "secondary_bath_count": 2,
        "powder_room_count": 1,
        "additional_parameters": {
            // Any additional parameters needed by specific estimators
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required parameters
        required_params = ['square_footage', 'bedroom_count']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Ensure square footage is a positive number
        if not isinstance(data['square_footage'], (int, float)) or data['square_footage'] <= 0:
            return jsonify({'error': 'Square footage must be a positive number'}), 400
        
        # Get the estimation engine
        engine = get_estimation_engine()
        
        # Run estimation
        results = engine.estimate_project(data)
        
        # Return the results
        return jsonify(results), 200
        
    except Exception as e:
        logger.exception(f"Error creating estimate: {str(e)}")
        return jsonify({'error': f'Failed to create estimate: {str(e)}'}), 500

@api_blueprint.route('/save/<name>', methods=['POST'])
def save_estimate(name):
    """
    Save an estimate with the given name.
    
    URL Parameters:
    - name: Name to save the estimate under
    
    Request body should contain the estimation data.
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate name (prevent directory traversal, etc.)
        if not name or '/' in name or '\\' in name or '..' in name:
            return jsonify({'error': 'Invalid name provided'}), 400
        
        # Get the estimation engine
        engine = get_estimation_engine()
        
        # Save the estimation
        success = engine.save_estimation(data, name)
        
        if success:
            return jsonify({'success': True, 'message': f'Estimate saved as {name}'}), 200
        else:
            return jsonify({'error': 'Failed to save estimate'}), 500
        
    except Exception as e:
        logger.exception(f"Error saving estimate: {str(e)}")
        return jsonify({'error': f'Failed to save estimate: {str(e)}'}), 500

@api_blueprint.route('/load/<name>', methods=['GET'])
def load_estimate(name):
    """
    Load an estimate with the given name.
    
    URL Parameters:
    - name: Name of the estimate to load
    """
    try:
        # Validate name (prevent directory traversal, etc.)
        if not name or '/' in name or '\\' in name or '..' in name:
            return jsonify({'error': 'Invalid name provided'}), 400
        
        # Get the estimation engine
        engine = get_estimation_engine()
        
        # Load the estimation
        data = engine.load_estimation(name)
        
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': f'Estimate {name} not found'}), 404
        
    except Exception as e:
        logger.exception(f"Error loading estimate: {str(e)}")
        return jsonify({'error': f'Failed to load estimate: {str(e)}'}), 500

@api_blueprint.route('/catalog', methods=['GET'])
def get_catalog():
    """Get the full product catalog."""
    try:
        # Get the data loader
        data_loader = DataLoader(os.path.join(current_app.config['CONFIG_DIR'], 'settings.json'))
        
        # Load the catalog
        catalog = data_loader.load_catalog()
        
        # Convert to list of dictionaries for JSON serialization
        catalog_list = catalog.to_dict('records')
        
        return jsonify(catalog_list), 200
        
    except Exception as e:
        logger.exception(f"Error getting catalog: {str(e)}")
        return jsonify({'error': f'Failed to get catalog: {str(e)}'}), 500

@api_blueprint.route('/list-saved', methods=['GET'])
def list_saved_estimates():
    """List all saved estimates."""
    try:
        # Get settings from config
        with open(os.path.join(current_app.config['CONFIG_DIR'], 'settings.json'), 'r') as f:
            settings = json.load(f)
        
        # Get path to estimations directory
        estimations_path = os.path.join(
            current_app.config['DATA_DIR'], 
            settings.get('data', {}).get('estimations_path', 'estimations')
        )
        
        # List all JSON files in the directory
        if os.path.exists(estimations_path):
            saved_estimates = [
                path.stem for path in Path(estimations_path).glob('*.json')
            ]
            return jsonify(saved_estimates), 200
        else:
            return jsonify([]), 200
        
    except Exception as e:
        logger.exception(f"Error listing saved estimates: {str(e)}")
        return jsonify({'error': f'Failed to list saved estimates: {str(e)}'}), 500

def register_routes(app):
    """Register all API routes with the Flask app."""
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Add a root route for basic connectivity testing
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Construction Budget Calculator API root endpoint',
            'api_endpoints': ['/api/health', '/api/estimate', '/api/save/<name>', '/api/load/<name>', '/api/list-saved']
        })
        
    # Log the registered routes for debugging
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} ({', '.join(rule.methods)})")