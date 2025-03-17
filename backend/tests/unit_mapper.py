#!/usr/bin/env python3
"""
Unit Mapper Utility (Simple Version)

This script helps map estimator quantities to catalog items by:
1. Loading the output JSON from the estimator quantity script
2. Loading the catalog items
3. Generating a CSV file for manual mapping
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the current directory to the Python path
# assuming this script is in the backend directory
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

def load_catalog(catalog_path: str) -> pd.DataFrame:
    """Load the enhanced catalog CSV file."""
    try:
        catalog = pd.read_csv(catalog_path)
        print(f"Loaded catalog with {len(catalog)} items")
        return catalog
    except Exception as e:
        print(f"Error loading catalog: {str(e)}")
        return pd.DataFrame()

def load_json_data(json_path: str) -> Dict:
    """Load the JSON data from a file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON data: {str(e)}")
        return {}

def generate_mapping_csv(module_data: Dict, catalog: pd.DataFrame, output_path: str) -> None:
    """Generate a CSV file for manual mapping."""
    rows = []
    
    for module_name, data in module_data.items():
        quantities = data.get('quantities', {})
        units = data.get('units', {})
        
        if not quantities:
            continue
            
        for qty_name, qty_value in quantities.items():
            unit = units.get(qty_name, '')
            
            # Create a row for this quantity
            row = {
                'Module': module_name,
                'Quantity': qty_name,
                'Unit': unit,
                'Sample Value': qty_value,
                'Premium Catalog ID': '',
                'Luxury Catalog ID': '',
                'Ultra-Luxury Catalog ID': ''
            }
            
            rows.append(row)
    
    # Create DataFrame and export
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Generated mapping CSV: {output_path}")

def main():
    """Main function for the unit mapper utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate CSV for catalog mapping')
    parser.add_argument('--catalog', help='Path to the catalog CSV file')
    parser.add_argument('--json-data', help='Path to the estimator quantities JSON file')
    parser.add_argument('--output', help='Path to the output CSV file')
    
    args = parser.parse_args()
    
    # Load the catalog if provided
    catalog = None
    if args.catalog:
        catalog = load_catalog(args.catalog)
    
    # Load the estimator quantities data
    module_data = {}
    if args.json_data:
        module_data = load_json_data(args.json_data)
    
    # Generate the mapping CSV
    if module_data and args.output:
        generate_mapping_csv(module_data, catalog, args.output)
    else:
        print("Please provide --json-data and --output arguments")

if __name__ == "__main__":
    main()