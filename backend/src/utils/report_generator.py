# src/utils/report_generator.py

import json
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates various report formats from estimation results"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
    
    def generate_summary_report(self, estimation_results):
        """Generate a simple text summary report"""
        if not estimation_results or 'project' not in estimation_results:
            return "Invalid estimation results"
        
        project = estimation_results['project']
        total_cost = estimation_results.get('total_cost', 0)
        
        report = []
        report.append("=" * 80)
        report.append(f"CONSTRUCTION ESTIMATION SUMMARY REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Project Information
        report.append("\nPROJECT INFORMATION")
        report.append("-" * 50)
        report.append(f"Square Footage: {project.get('square_footage'):,} sq ft")
        report.append(f"Project Tier: {project.get('tier', 'Unknown')}")
        
        # Add other project details if available
        for key, value in project.items():
            if key not in ['square_footage', 'tier']:
                report.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Cost Summary
        report.append("\nCOST SUMMARY")
        report.append("-" * 50)
        report.append(f"Total Estimated Cost: ${total_cost:,.2f}")
        
        # Category Breakdown
        if 'summary' in estimation_results and 'cost_breakdown' in estimation_results['summary']:
            report.append("\nCATEGORY BREAKDOWN")
            report.append("-" * 50)
            
            breakdown = estimation_results['summary']['cost_breakdown']
            percentages = estimation_results['summary'].get('percentage_breakdown', {})
            
            for category, cost in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                percentage = percentages.get(category, 0)
                report.append(f"{category.replace('_', ' ').title()}: ${cost:,.2f} ({percentage:.1f}%)")
        
        # Warnings
        if 'summary' in estimation_results and 'warnings' in estimation_results['summary']:
            warnings = estimation_results['summary']['warnings']
            if warnings:
                report.append("\nWARNINGS")
                report.append("-" * 50)
                for warning in warnings:
                    report.append(f"- {warning}")
        
        return "\n".join(report)
    
    def generate_detailed_report(self, estimation_results):
        """Generate a detailed report with all quantities and costs"""
        if not estimation_results or 'project' not in estimation_results:
            return "Invalid estimation results"
        
        report = []
        report.append("=" * 80)
        report.append(f"DETAILED CONSTRUCTION ESTIMATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Project Information (same as summary report)
        project = estimation_results['project']
        report.append("\nPROJECT INFORMATION")
        report.append("-" * 50)
        report.append(f"Square Footage: {project.get('square_footage'):,} sq ft")
        report.append(f"Project Tier: {project.get('tier', 'Unknown')}")
        
        # Category Details
        categories = estimation_results.get('categories', {})
        for category, category_data in categories.items():
            if category_data.get('status') == 'success':
                report.append(f"\n{category.replace('_', ' ').upper()}")
                report.append("-" * 50)
                
                # Quantities
                quantities = category_data.get('quantities', {})
                if quantities:
                    report.append("\nQuantities:")
                    for name, value in quantities.items():
                        report.append(f"  {name.replace('_', ' ').title()}: {value}")
                
                # Costed Items
                costed_items = category_data.get('costed_items', [])
                if costed_items:
                    report.append("\nCosted Items:")
                    for item in costed_items:
                        report.append(f"  {item.get('item_name')}: {item.get('quantity')} {item.get('unit')} at ${item.get('unit_cost', 0):,.2f} each = ${item.get('total_cost', 0):,.2f}")
                        if 'note' in item:
                            report.append(f"    Note: {item.get('note')}")
                
                # Category Total
                report.append(f"\nCategory Total: ${category_data.get('total_cost', 0):,.2f}")
            else:
                report.append(f"\n{category.replace('_', ' ').upper()}")
                report.append("-" * 50)
                report.append(f"Status: {category_data.get('status', 'unknown')}")
                if 'message' in category_data:
                    report.append(f"Message: {category_data.get('message')}")
        
        # Overall Total
        report.append("\n" + "=" * 50)
        report.append(f"TOTAL ESTIMATED COST: ${estimation_results.get('total_cost', 0):,.2f}")
        report.append("=" * 50)
        
        return "\n".join(report)
    
    def generate_csv_report(self, estimation_results, output_file=None):
        """Generate a CSV report of all costed items"""
        if not estimation_results or 'categories' not in estimation_results:
            return None
        
        # Collect all costed items
        all_items = []
        for category, category_data in estimation_results.get('categories', {}).items():
            if category_data.get('status') == 'success':
                for item in category_data.get('costed_items', []):
                    item_data = {
                        'Category': category,
                        'Item': item.get('item_name', ''),
                        'Item ID': item.get('item_id', ''),
                        'Quantity': item.get('quantity', 0),
                        'Unit': item.get('unit', ''),
                        'Unit Cost': item.get('unit_cost', 0),
                        'Total Cost': item.get('total_cost', 0),
                        'Markup %': item.get('markup', 0),
                        'Note': item.get('note', '')
                    }
                    all_items.append(item_data)
        
        # Create DataFrame
        df = pd.DataFrame(all_items)
        
        # Write to CSV if output file provided
        if output_file:
            try:
                df.to_csv(output_file, index=False)
                return output_file
            except Exception as e:
                logger.error(f"Error writing CSV report: {str(e)}")
                return None
        
        return df