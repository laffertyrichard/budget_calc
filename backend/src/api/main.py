"""
Entry point for running the Construction Budget Calculator API server.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path to allow importing modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_api_server():
    """Run the API server."""
    from src.api.server import run_server as start_api
    start_api()

def run_estimation_cli(args):
    """Run the CLI estimation tool."""
    from src.core.estimation_engine import EstimationEngine
    
    engine = EstimationEngine(os.path.join("config", "settings.json"))
    
    if args.load:
        # Load existing estimation
        data = engine.load_estimation(args.load)
        if data:
            print(f"Loaded estimation: {args.load}")
            # Do something with the loaded data
        else:
            print(f"Failed to load estimation: {args.load}")
    elif args.project:
        # Run a new estimation
        import json
        try:
            with open(args.project, 'r') as f:
                project_data = json.load(f)
                
            results = engine.estimate_project(project_data)
            
            if args.save:
                engine.save_estimation(results, args.save)
                print(f"Estimation saved as: {args.save}")
            
            print(f"Estimation complete for {project_data.get('square_footage')} sq ft project")
        except Exception as e:
            print(f"Error estimating project: {str(e)}")
    else:
        print("No action specified. Use --project or --load arguments.")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Construction Budget Calculator')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # API server command
    api_parser = subparsers.add_parser('api', help='Run the API server')
    
    # CLI estimation command
    cli_parser = subparsers.add_parser('estimate', help='Run the estimation engine')
    cli_parser.add_argument('--project', help='Path to project data JSON file')
    cli_parser.add_argument('--load', help='Name of saved estimation to load')
    cli_parser.add_argument('--save', help='Name to save the estimation under')
    
    args = parser.parse_args()
    
    if args.command == 'api' or not args.command:
        # Default to API server if no command is specified
        run_api_server()
    elif args.command == 'estimate':
        run_estimation_cli(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()