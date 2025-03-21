#!/usr/bin/env python3
"""
Construction Quantity Estimation System
Main entry point for CLI version
"""

import argparse
import json
import logging
import sys
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

def main():
    parser = argparse.ArgumentParser(description='Construction Budget Calculator')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file with project data')
    parser.add_argument('--output', type=str, default='estimation_results.json', help='Output file for results')
    parser.add_argument('--report', type=str, default='estimation_report.txt', help='Output file for text report')
    parser.add_argument('--csv', type=str, help='Output CSV file for costed items')
    parser.add_argument('--estimator_report', type=str, default='estimator_report.txt', help='Output file for estimator module report')
    args = parser.parse_args()
    
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

if __name__ == "__main__":
    main()