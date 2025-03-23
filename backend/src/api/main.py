#!/usr/bin/env python3
"""
Construction Quantity Estimation System
Combined entry point for CLI and API versions
"""

import argparse
import json
import logging
import sys
import os
from src.core.estimation_engine import EstimationEngine
from src.utils.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("construction_estimator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_cli_mode(args):
    """Run in CLI mode with the standard estimation workflow"""
    # Validate input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    # Load input data
    with open(args.input, 'r') as f:
        project_data = json.load(f)
    
    # Initialize estimator and generate results
    estimator = EstimationEngine()
    results = estimator.estimate_project(project_data)
    
    # Log and print all estimator module outputs
    for category, output in results.get('categories', {}).items():
        logger.info(f"Category: {category}, Output: {output}")
        print(f"Category: {category}, Output: {output}")
    
    # Save results to JSON
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Generate report
    report_generator = ReportGenerator()
    report = report_generator.generate_detailed_report(results)
    
    # Save report to file
    with open(args.report, 'w') as f:
        f.write(report)
        print(f"Report saved to {args.report}")
    
    # Generate CSV if requested
    if args.csv:
        csv_file = report_generator.generate_csv_report(results, args.csv)
        if csv_file:
            print(f"CSV report saved to {csv_file}")
    
    # Print summary to console
    summary = report_generator.generate_summary_report(results)
    print("\n" + "=" * 80)
    print(summary)
    print("=" * 80)
    
    # Generate and save estimator module report
    estimator_report = generate_estimator_report(results)
    with open(args.estimator_report, 'w') as f:
        f.write(estimator_report)
        print(f"Estimator report saved to {args.estimator_report}")

def run_api_mode(args):
    """Run in API mode, starting the FastAPI server"""
    try:
        import uvicorn
        from src.api.app import app
        
        print(f"Starting API server on {args.host}:{args.port}")
        print(f"API documentation available at http://{args.host}:{args.port}/docs")
        uvicorn.run(app, host=args.host, port=args.port)
    except ImportError:
        logger.error("API dependencies not installed. Please run: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting API server: {str(e)}")
        sys.exit(1)

def generate_estimator_report(results):
    """Generate a report for estimator module outputs"""
    report_lines = []
    report_lines.append("ESTIMATOR MODULE OUTPUTS")
    report_lines.append("=" * 80)
    
    for category, output in results.get('categories', {}).items():
        report_lines.append(f"Category: {category}")
        report_lines.append("-" * 80)
        report_lines.append(json.dumps(output, indent=2))
        report_lines.append("=" * 80)
    
    logger.info("Generated estimator module report")
    print("Generated estimator module report")
    
    return "\n".join(report_lines)

def main():
    """Main entry point with mode selection"""
    # Create parent parser for shared arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--mode', type=str, choices=['cli', 'api'], default='cli',
                        help='Run mode: cli for command line interface, api for web API server')
    
    # Create the main parser
    parser = argparse.ArgumentParser(description='Construction Budget Calculator')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # CLI mode subparser
    cli_parser = subparsers.add_parser('cli', help='Command Line Interface mode')
    cli_parser.add_argument('--input', type=str, required=True, help='Input JSON file with project data')
    cli_parser.add_argument('--output', type=str, default='estimation_results.json', 
                        help='Output file for results')
    cli_parser.add_argument('--report', type=str, default='estimation_report.txt', 
                        help='Output file for text report')
    cli_parser.add_argument('--csv', type=str, help='Output CSV file for costed items')
    cli_parser.add_argument('--estimator_report', type=str, default='estimator_report.txt', 
                        help='Output file for estimator module report')
    
    # API mode subparser
    api_parser = subparsers.add_parser('api', help='API Server mode')
    api_parser.add_argument('--host', type=str, default='0.0.0.0', 
                        help='Host address to bind the API server')
    api_parser.add_argument('--port', type=int, default=5001, 
                        help='Port to run the API server')
    
    args = parser.parse_args()
    
    # Default to cli mode if no mode specified
    if not args.mode:
        args.mode = 'cli'
        parser.print_help()
        sys.exit(1)
    
    # Execute the chosen mode
    if args.mode == 'cli':
        run_cli_mode(args)
    else:
        run_api_mode(args)

if __name__ == "__main__":
    main()