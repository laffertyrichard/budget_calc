#!/usr/bin/env python3
"""
Catalog Tier Mapper

This script maps catalog items to tiers based on cost levels:
- Low cost → Premium tier
- Mid cost → Luxury tier
- High cost → Ultra-Luxury tier

It then generates a CSV file for mapping estimator quantities to these tiered catalog items.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add the current directory to the Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

def load_catalog(catalog_path: str) -> pd.DataFrame:
    """Load the catalog CSV file and assign tiers based on cost."""
    try:
        # Load the catalog
        catalog = pd.read_csv(catalog_path)
        print(f"Loaded catalog with {len(catalog)} items")
        
        # Create tier assignments if they don't exist
        if 'ConstructionTier' not in catalog.columns:
            # Create tier assignments based on cost levels
            catalog['ConstructionTier'] = 'Unknown'
            
            # Check if we have the cost columns
            if all(col in catalog.columns for col in ['Cost (Low)', 'Cost(Mid)', 'Cost (High)']):
                # Assign tiers based on which cost value is used
                for idx, row in catalog.iterrows():
                    low_cost = row.get('Cost (Low)')
                    mid_cost = row.get('Cost(Mid)')
                    high_cost = row.get('Cost (High)')
                    
                    # Create unique tier IDs by appending suffixes
                    if pd.notna(low_cost):
                        catalog.at[idx, 'PremiumID'] = f"{row.get('ID', '')}_P"
                    
                    if pd.notna(mid_cost):
                        catalog.at[idx, 'LuxuryID'] = f"{row.get('ID', '')}_L"
                    
                    if pd.notna(high_cost):
                        catalog.at[idx, 'UltraID'] = f"{row.get('ID', '')}_U"
        else:
            # If ConstructionTier exists, create IDs based on that
            for idx, row in catalog.iterrows():
                tier = row.get('ConstructionTier')
                
                if tier == 'Premium':
                    catalog.at[idx, 'PremiumID'] = f"{row.get('ID', '')}_P"
                elif tier == 'Luxury':
                    catalog.at[idx, 'LuxuryID'] = f"{row.get('ID', '')}_L"
                elif tier == 'Ultra-Luxury':
                    catalog.at[idx, 'UltraID'] = f"{row.get('ID', '')}_U"
        
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

def find_matching_items(catalog: pd.DataFrame, module_name: str, quantity_name: str, unit: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Find catalog items that match a quantity, grouped by tier."""
    if catalog.empty:
        return [], [], []
    
    # Extract search terms from the quantity name
    search_terms = []
    for part in quantity_name.split('_'):
        if part and len(part) > 2:  # Skip very short parts
            search_terms.append(part)
    
    # Find items matching any search term
    matches = []
    for term in search_terms:
        term_matches = catalog[
            catalog['Item'].str.contains(term, case=False, na=False) |
            (catalog['SearchItem'].str.contains(term, case=False, na=False) if 'SearchItem' in catalog.columns else False)
        ]
        matches.append(term_matches)
    
    # Combine all matches
    if not matches:
        return [], [], []
    
    all_matches = pd.concat(matches).drop_duplicates()
    
    # Filter by module if 'EstimatorModule' exists
    if 'EstimatorModule' in all_matches.columns:
        module_matches = all_matches[all_matches['EstimatorModule'] == module_name]
        if not module_matches.empty:
            all_matches = module_matches
    
    # Filter by unit compatibility if possible
    if 'Unit' in all_matches.columns and unit:
        unit_compatible_matches = all_matches[
            (all_matches['Unit'] == unit) |
            (all_matches['Unit'].str.contains(unit, case=False, na=False)) |
            (unit.lower() in all_matches['Unit'].str.lower())
        ]
        
        if not unit_compatible_matches.empty:
            all_matches = unit_compatible_matches
    
    # Group matches by tier
    premium_matches = []
    luxury_matches = []
    ultra_matches = []
    
    for _, row in all_matches.iterrows():
        item_info = {
            'ID': row.get('ID', ''),
            'Item': row.get('Item', 'Unknown'),
            'Unit': row.get('Unit', ''),
            'Cost': 0
        }
        
        # Add to premium tier (with Premium ID and Low cost)
        if 'PremiumID' in row and pd.notna(row['PremiumID']):
            premium_item = item_info.copy()
            premium_item['ID'] = row['PremiumID']
            premium_item['Cost'] = row.get('Cost (Low)', 0)
            premium_matches.append(premium_item)
        
        # Add to luxury tier (with Luxury ID and Mid cost)
        if 'LuxuryID' in row and pd.notna(row['LuxuryID']):
            luxury_item = item_info.copy()
            luxury_item['ID'] = row['LuxuryID']
            luxury_item['Cost'] = row.get('Cost(Mid)', 0)
            luxury_matches.append(luxury_item)
        
        # Add to ultra tier (with Ultra ID and High cost)
        if 'UltraID' in row and pd.notna(row['UltraID']):
            ultra_item = item_info.copy()
            ultra_item['ID'] = row['UltraID']
            ultra_item['Cost'] = row.get('Cost (High)', 0)
            ultra_matches.append(ultra_item)
        
        # If we don't have tier IDs, check the ConstructionTier
        if 'ConstructionTier' in row and not any(f"{x}ID" in row for x in ['Premium', 'Luxury', 'Ultra']):
            if row['ConstructionTier'] == 'Premium':
                premium_matches.append(item_info)
            elif row['ConstructionTier'] == 'Luxury':
                luxury_matches.append(item_info)
            elif row['ConstructionTier'] == 'Ultra-Luxury':
                ultra_matches.append(item_info)
    
    return premium_matches, luxury_matches, ultra_matches

def generate_mapping_csv(module_data: Dict, catalog: pd.DataFrame, output_path: str) -> None:
    """Generate a CSV file for manual mapping with tiered catalog items."""
    rows = []
    
    for module_name, data in module_data.items():
        quantities = data.get('quantities', {})
        units = data.get('units', {})
        
        if not quantities:
            continue
            
        for qty_name, qty_value in quantities.items():
            if qty_name == 'units':  # Skip the units dictionary if present
                continue
                
            unit = units.get(qty_name, '')
            
            # Find matching items for this quantity
            premium_matches, luxury_matches, ultra_matches = find_matching_items(
                catalog, module_name, qty_name, unit
            )
            
            # Extract search terms
            search_terms = []
            for part in qty_name.split('_'):
                if part and len(part) > 2:
                    search_terms.append(part)
            
            # Create a row for this quantity
            row = {
                'Module': module_name,
                'Quantity': qty_name,
                'Unit': unit,
                'Sample Value': qty_value,
                'Search Terms': ', '.join(search_terms)
            }
            
            # Add Premium tier matches
            if premium_matches:
                row['Premium Catalog ID'] = premium_matches[0]['ID']
                row['Premium Item'] = premium_matches[0]['Item']
                row['Premium Cost'] = premium_matches[0]['Cost']
            else:
                row['Premium Catalog ID'] = ''
                row['Premium Item'] = ''
                row['Premium Cost'] = ''
            
            # Add Luxury tier matches
            if luxury_matches:
                row['Luxury Catalog ID'] = luxury_matches[0]['ID']
                row['Luxury Item'] = luxury_matches[0]['Item']
                row['Luxury Cost'] = luxury_matches[0]['Cost']
            else:
                row['Luxury Catalog ID'] = ''
                row['Luxury Item'] = ''
                row['Luxury Cost'] = ''
            
            # Add Ultra-Luxury tier matches
            if ultra_matches:
                row['Ultra Catalog ID'] = ultra_matches[0]['ID']
                row['Ultra Item'] = ultra_matches[0]['Item']
                row['Ultra Cost'] = ultra_matches[0]['Cost']
            else:
                row['Ultra Catalog ID'] = ''
                row['Ultra Item'] = ''
                row['Ultra Cost'] = ''
            
            # Additional columns for manual selection
            row['Selected Premium ID'] = row['Premium Catalog ID']
            row['Selected Luxury ID'] = row['Luxury Catalog ID']
            row['Selected Ultra ID'] = row['Ultra Catalog ID']
            
            rows.append(row)
    
    # Create DataFrame and export
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Generated mapping CSV: {output_path}")

def generate_mapping_files(csv_path: str, output_dir: str) -> None:
    """Generate mapping JSON files from a completed CSV file."""
    try:
        # Load the CSV with manual mappings
        df = pd.read_csv(csv_path)
        
        # Group by module
        modules = df['Module'].unique()
        
        for module_name in modules:
            # Create mapping structure
            mapping = {
                module_name: {
                    "item_mappings": {}
                }
            }
            
            # Get quantities for this module
            module_rows = df[df['Module'] == module_name]
            
            # Process each quantity
            for _, row in module_rows.iterrows():
                quantity_name = row['Quantity']
                
                # Get search terms
                search_terms = []
                if pd.notna(row.get('Search Terms')):
                    search_terms = [term.strip() for term in row['Search Terms'].split(',') if term.strip()]
                else:
                    # Generate search terms from quantity name
                    for part in quantity_name.split('_'):
                        if part and len(part) > 2:
                            search_terms.append(part)
                
                # Get selected IDs
                tier_item_ids = {
                    "Premium": [],
                    "Luxury": [],
                    "Ultra-Luxury": []
                }
                
                if pd.notna(row.get('Selected Premium ID')) and row['Selected Premium ID']:
                    tier_item_ids['Premium'] = [row['Selected Premium ID']]
                
                if pd.notna(row.get('Selected Luxury ID')) and row['Selected Luxury ID']:
                    tier_item_ids['Luxury'] = [row['Selected Luxury ID']]
                
                if pd.notna(row.get('Selected Ultra ID')) and row['Selected Ultra ID']:
                    tier_item_ids['Ultra-Luxury'] = [row['Selected Ultra ID']]
                
                # Add mapping for this quantity
                mapping[module_name]["item_mappings"][quantity_name] = {
                    "search_terms": search_terms,
                    "tier_item_ids": tier_item_ids
                }
            
            # Save mapping file
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{module_name}_mappings.json")
            
            with open(output_file, 'w') as f:
                json.dump(mapping, f, indent=2)
                
            print(f"Generated mapping file: {output_file}")
    
    except Exception as e:
        print(f"Error generating mapping files: {str(e)}")

def main():
    """Main function for the catalog tier mapper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Map catalog items to tiers and generate mapping CSV')
    parser.add_argument('--catalog', required=True, help='Path to the catalog CSV file')
    parser.add_argument('--json-data', required=True, help='Path to the estimator quantities JSON file')
    parser.add_argument('--output', required=True, help='Path to the output CSV file')
    parser.add_argument('--from-csv', help='Generate mapping files from a completed CSV file')
    parser.add_argument('--output-dir', help='Directory to save mapping JSON files')
    
    args = parser.parse_args()
    
    # Generate mapping files from a completed CSV
    if args.from_csv and args.output_dir:
        generate_mapping_files(args.from_csv, args.output_dir)
        return
    
    # Load the catalog and assign tiers
    catalog = load_catalog(args.catalog)
    
    # Load the estimator quantities data
    module_data = load_json_data(args.json_data)
    
    # Generate the mapping CSV
    generate_mapping_csv(module_data, catalog, args.output)

if __name__ == "__main__":
    main()