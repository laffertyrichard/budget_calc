#!/usr/bin/env python3
"""
Estimator Quantities Report Generator

This script runs all estimator modules with sample project data
and generates a comprehensive report of all calculated quantities.
The report includes units and sample values to aid in catalog matching.
"""

import os
import sys
import json
import logging
import importlib
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
# assuming this script is in the backend directory
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import estimator modules - update this list based on your logs and available modules
estimator_modules = [
    "foundation",
    "structural",
    "electrical",
    "plumbing", 
    "hvac",
    "drywall_interior",
    "roofing",
    "windows_doors",  # was called doors_windows in logs
    "flooring",
    "tile",
    "painting_coatings",
    "finish_carpentry",
    "cabinetry",
    "countertops",
    "landscape_hardscape",  # was called landscape in logs
    "cleaning", 
    "specialty"  # was missing or had issues in logs
]

def load_estimator(module_name: str):
    """Dynamically load an estimator module with better debug output."""
    try:
        logger.debug(f"Attempting to import module: src.estimators.{module_name}")
        module = importlib.import_module(f"src.estimators.{module_name}")
        
        # Get the estimator class (assumed to be named CategoryEstimator)
        class_name = f"{module_name.title().replace('_', '')}Estimator"
        logger.debug(f"Looking for class: {class_name}")
        
        # Check if the class exists in the module
        if not hasattr(module, class_name):
            logger.error(f"Class {class_name} not found in module src.estimators.{module_name}")
            # List available classes in the module for debugging
            available_classes = [name for name in dir(module) if name.endswith('Estimator')]
            if available_classes:
                logger.debug(f"Available classes in module: {', '.join(available_classes)}")
            return None
            
        estimator_class = getattr(module, class_name)
        estimator = estimator_class()
        
        # Check if the estimator has the necessary methods
        if not hasattr(estimator, 'calculate_quantities'):
            logger.error(f"Estimator {class_name} is missing the calculate_quantities method")
            return None
            
        logger.debug(f"Successfully loaded {class_name}")
        return estimator
        
    except (ImportError, AttributeError) as e:
        logger.error(f"Could not load estimator for {module_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error initializing estimator for {module_name}: {str(e)}", exc_info=True)
        return None

def guess_quantity_unit(quantity_name: str) -> str:
    """Guess the most likely unit for a quantity based on its name."""
    name = quantity_name.lower()
    
    if any(term in name for term in ['_sf', 'square_feet', 'area', 'sqft']):
        return 'SF'
    elif any(term in name for term in ['_lf', 'linear_feet', 'length']):
        return 'LF'
    elif any(term in name for term in ['_cy', 'cubic_yards', 'concrete']):
        return 'CY'
    elif any(term in name for term in ['_count', '_ea', 'quantity']):
        return 'EA'
    elif any(term in name for term in ['gallons', '_gal']):
        return 'GAL'
    elif any(term in name for term in ['percentage', '_pct']):
        return '%'
    elif any(term in name for term in ['_amp', 'amperage']):
        return 'AMP'
    elif any(term in name for term in ['tonnage', 'ton']):
        return 'TON'
    elif any(term in name for term in ['_bf', 'board_feet']):
        return 'BF'
    elif any(term in name for term in ['_cf', 'cubic_feet']):
        return 'CF'
    elif any(term in name for term in ['_sy', 'square_yard']):
        return 'SY'
    
    # Default to 'EA' if no match
    return 'EA'

def extract_units_from_estimator(quantities: Dict) -> Dict[str, str]:
    """Extract units from quantities dictionary if available, or guess them."""
    units = {}
    
    # Check if units are provided in structured format
    if isinstance(quantities, dict) and 'units' in quantities:
        return quantities['units']
    
    # Otherwise, try to guess units from quantity names
    for quantity_name in quantities:
        if quantity_name != 'units':  # Skip the units dict if present
            units[quantity_name] = guess_quantity_unit(quantity_name)
    
    return units

def calculate_sample_quantities(module_name: str, estimator) -> Tuple[Dict, Dict[str, str]]:
    """Calculate sample quantities for an estimator with different project sizes and tiers."""
    
    # Define sample projects (Small/Premium, Medium/Luxury, Large/Ultra-Luxury)
    sample_projects = [
        {"square_footage": 3500, "tier": "Premium", "bedroom_count": 3, "primary_bath_count": 1, 
         "secondary_bath_count": 1, "powder_room_count": 0},
        {"square_footage": 6500, "tier": "Luxury", "bedroom_count": 4, "primary_bath_count": 1, 
         "secondary_bath_count": 2, "powder_room_count": 1},
        {"square_footage": 12000, "tier": "Ultra-Luxury", "bedroom_count": 5, "primary_bath_count": 2, 
         "secondary_bath_count": 3, "powder_room_count": 2}
    ]
    
    # Get quantities for each project
    results = []
    
    for project in sample_projects:
        try:
            logger.debug(f"Calculating {module_name} quantities for {project['tier']} project")
            quantities = estimator.calculate_quantities(**project)
            if not quantities:
                logger.warning(f"Module {module_name} returned empty quantities for {project['tier']}")
            else:
                logger.debug(f"Received {len(quantities)} quantities from {module_name}")
            results.append(quantities)
        except Exception as e:
            logger.error(f"Error calculating quantities for {module_name} with {project['tier']}: {str(e)}", 
                         exc_info=True)
            results.append({})
    
    # Merge quantities from all projects to ensure we have a complete list
    all_quantities = {}
    for quantity_set in results:
        if not isinstance(quantity_set, dict):
            logger.warning(f"Module {module_name} returned non-dict result: {type(quantity_set)}")
            continue
            
        for key, value in quantity_set.items():
            if key != 'units':  # Skip units dictionary
                all_quantities[key] = value
    
    # Extract units or guess them
    units = extract_units_from_estimator(all_quantities)
    
    return all_quantities, units

def format_report(module_data: Dict[str, Dict], output_format: str = 'md') -> str:
    """Format the quantity report in the specified format (md, csv, json)."""
    
    if output_format == 'json':
        return json.dumps(module_data, indent=2)
    
    elif output_format == 'csv':
        rows = []
        headers = ['Module', 'Quantity', 'Unit', 'Sample Value']
        
        for module, data in module_data.items():
            quantities = data.get('quantities', {})
            units = data.get('units', {})
            
            for qty_name, qty_value in quantities.items():
                unit = units.get(qty_name, '')
                rows.append([module, qty_name, unit, str(qty_value)])
                
        # Convert to CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()
    
    else:  # Default to markdown
        report = ["# Estimator Quantities Report\n"]
        report.append("This report lists all quantities calculated by each estimator module, including units and sample values.\n")
        
        # Table of contents
        report.append("## Table of Contents")
        for module in module_data.keys():
            module_name = module.replace('_', ' ').title()
            report.append(f"- [{module_name}](#{module})")
        report.append("")
        
        # Module data
        for module, data in module_data.items():
            module_name = module.replace('_', ' ').title()
            report.append(f"## <a id='{module}'></a>{module_name}")
            
            if data.get('error'):
                report.append(f"**Error:** {data['error']}\n")
                continue
                
            quantities = data.get('quantities', {})
            units = data.get('units', {})
            
            if not quantities:
                report.append("No quantities calculated for this module.\n")
                continue
            
            report.append("| Quantity | Unit | Sample Value |")
            report.append("| --- | --- | --- |")
            
            for qty_name, qty_value in sorted(quantities.items()):
                unit = units.get(qty_name, '')
                # Format numbers appropriately
                if isinstance(qty_value, (int, float)):
                    if float(qty_value).is_integer():
                        formatted_value = f"{int(qty_value):,}"
                    else:
                        formatted_value = f"{float(qty_value):,.2f}"
                else:
                    formatted_value = str(qty_value)
                    
                report.append(f"| {qty_name} | {unit} | {formatted_value} |")
            
            report.append("")  # Add spacing between modules
            
        return "\n".join(report)

def generate_catalog_mapping_stubs(module_data: Dict[str, Dict], output_dir: Optional[str] = None) -> None:
    """Generate catalog mapping stubs for each module."""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    for module, data in module_data.items():
        quantities = data.get('quantities', {})
        units = data.get('units', {})
        
        if not quantities:
            continue
            
        # Create mapping structure
        mappings = {
            module: {
                "item_mappings": {}
            }
        }
        
        # Add stub for each quantity
        for qty_name in quantities.keys():
            # Generate search terms from the quantity name
            search_terms = []
            for part in qty_name.split('_'):
                if part and len(part) > 2:  # Skip very short parts
                    search_terms.append(part)
            
            mappings[module]["item_mappings"][qty_name] = {
                "search_terms": search_terms,
                "tier_item_ids": {
                    "Premium": [],
                    "Luxury": [],
                    "Ultra-Luxury": []
                }
            }
        
        # Output as JSON
        if output_dir:
            with open(os.path.join(output_dir, f"{module}_mappings.json"), 'w') as f:
                json.dump(mappings, f, indent=2)

def export_to_excel(module_data: Dict[str, Dict], output_file: str) -> None:
    """Export the complete report to an Excel file for easier manual matching."""
    if not module_data:
        return
    
    data_rows = []
    
    for module, data in module_data.items():
        quantities = data.get('quantities', {})
        units = data.get('units', {})
        
        for qty_name, qty_value in quantities.items():
            unit = units.get(qty_name, '')
            
            # Format the quantity value
            if isinstance(qty_value, (int, float)):
                if float(qty_value).is_integer():
                    formatted_value = int(qty_value)
                else:
                    formatted_value = float(qty_value)
            else:
                formatted_value = str(qty_value)
            
            # Create a row for the quantity
            row = {
                'Module': module,
                'Quantity': qty_name,
                'Unit': unit,
                'Sample Value': formatted_value,
                'Catalog Item ID (Premium)': '',
                'Catalog Item ID (Luxury)': '',
                'Catalog Item ID (Ultra-Luxury)': '',
                'Search Terms': ' '.join(part for part in qty_name.split('_') if part and len(part) > 2)
            }
            
            data_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data_rows)
    
    # Write to Excel
    df.to_excel(output_file, index=False)
    print(f"Report exported to Excel: {output_file}")

def save_json_data(module_data: Dict[str, Dict], output_file: str) -> None:
    """Save the raw module data as a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(module_data, f, indent=2)
    print(f"Raw data saved to {output_file}")

def main():
    """Generate a comprehensive report of all estimator quantities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate an estimator quantities report')
    parser.add_argument('--format', choices=['md', 'csv', 'json'], default='md',
                        help='Output format (markdown, CSV, or JSON)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--excel', help='Export to Excel file for manual matching')
    parser.add_argument('--mapping-stubs', help='Generate mapping stub JSON files in the specified directory')
    parser.add_argument('--json-output', help='Save the raw data as a JSON file for other tools')
    parser.add_argument('--list-modules', action='store_true', 
                        help='List all available estimator modules and exit')
    
    args = parser.parse_args()
    
    if args.list_modules:
        # Scan the estimators directory to find all available modules
        estimators_dir = current_dir / 'src' / 'estimators'
        available_modules = []
        
        if estimators_dir.exists():
            for file_path in estimators_dir.glob('*.py'):
                if not file_path.name.startswith('__'):
                    module_name = file_path.stem
                    available_modules.append(module_name)
            
            print("Available estimator modules:")
            for module in sorted(available_modules):
                print(f"- {module}")
        else:
            print(f"Estimators directory not found: {estimators_dir}")
        
        return
    
    # Store data for all modules
    module_data = {}
    
    # Process each estimator module
    for module_name in estimator_modules:
        print(f"Processing {module_name} estimator...")
        
        estimator = load_estimator(module_name)
        if not estimator:
            module_data[module_name] = {"error": "Failed to load estimator"}
            continue
        
        try:
            quantities, units = calculate_sample_quantities(module_name, estimator)
            
            if not quantities:
                print(f"Warning: No quantities generated for {module_name}")
                module_data[module_name] = {"error": "No quantities generated"}
            else:
                module_data[module_name] = {
                    "quantities": quantities,
                    "units": units
                }
        except Exception as e:
            print(f"Error processing {module_name}: {str(e)}")
            module_data[module_name] = {"error": str(e)}
    
    # Save raw data as JSON if requested
    if args.json_output:
        save_json_data(module_data, args.json_output)
    
    # Format the report
    report = format_report(module_data, args.format)
    
    # Output the report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)
    
    # Generate mapping stubs if requested
    if args.mapping_stubs:
        generate_catalog_mapping_stubs(module_data, args.mapping_stubs)
        print(f"Mapping stubs generated in {args.mapping_stubs}")
    
    # Export to Excel if requested
    if args.excel:
        export_to_excel(module_data, args.excel)

if __name__ == "__main__":
    main()