#!/usr/bin/env python3
# catalog_manager.py

import argparse
import os
import sys
import json
import pandas as pd
from src.utils.catalog_enhancer import CatalogEnhancer
from src.utils.catalog_mapper import CatalogMapper

def main():
    parser = argparse.ArgumentParser(description='Construction Catalog Management Utility')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Enhance catalog command
    enhance_parser = subparsers.add_parser('enhance', help='Enhance catalog with improved naming and search attributes')
    enhance_parser.add_argument('input', help='Input catalog CSV file')
    enhance_parser.add_argument('--output', help='Output enhanced catalog CSV file')
    
    # Generate mappings command
    map_parser = subparsers.add_parser('map', help='Generate mapping suggestions between estimators and catalog')
    map_parser.add_argument('catalog', help='Enhanced catalog CSV file')
    map_parser.add_argument('--config', help='Mapping configuration file')
    map_parser.add_argument('--module', help='Focus on specific estimator module')
    map_parser.add_argument('--output', help='Output mapping suggestions to file')
    
    # Check catalog command
    check_parser = subparsers.add_parser('check', help='Check catalog for issues')
    check_parser.add_argument('catalog', help='Catalog CSV file to check')
    
    # Add mapping command
    add_parser = subparsers.add_parser('add-mapping', help='Add or update quantity mapping')
    add_parser.add_argument('catalog', help='Enhanced catalog CSV file')
    add_parser.add_argument('--config', help='Mapping configuration file')
    add_parser.add_argument('--module', required=True, help='Estimator module')
    add_parser.add_argument('--quantity', required=True, help='Quantity name')
    add_parser.add_argument('--terms', required=True, help='Search terms (comma-separated)')
    add_parser.add_argument('--items', help='Item IDs for direct mapping (comma-separated)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'enhance':
        enhancer = CatalogEnhancer()
        result = enhancer.enhance_catalog(args.input, args.output)
        if result:
            print(f"Enhanced catalog saved to: {result}")
        else:
            print("Error enhancing catalog")
            return 1
    
    elif args.command == 'map':
        mapper = CatalogMapper(args.catalog, args.config)
        suggestions = mapper.generate_mapping_suggestions(args.module)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(suggestions, f, indent=2)
            print(f"Mapping suggestions saved to: {args.output}")
        else:
            print(json.dumps(suggestions, indent=2))
    
    elif args.command == 'check':
        try:
            df = pd.read_csv(args.catalog)
            
            # Check for required columns
            required_columns = ['Item', 'Cost(Mid)', 'Unit', 'Category', 'ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"WARNING: Missing required columns: {', '.join(missing_columns)}")
            
            # Check for missing values
            for col in ['Item', 'Category', 'ID']:
                if col in df.columns:
                    missing = df[col].isna().sum()
                    if missing > 0:
                        print(f"WARNING: {missing} rows missing {col}")
            
            # Check for duplicate IDs
            if 'ID' in df.columns:
                duplicates = df['ID'].duplicated().sum()
                if duplicates > 0:
                    print(f"WARNING: {duplicates} duplicate IDs")
            
            # Print summary info
            print(f"Catalog contains {len(df)} items")
            
            if 'Category' in df.columns:
                categories = df['Category'].value_counts()
                print("\nCategory distribution:")
                for category, count in categories.items():
                    print(f"  {category}: {count}")
            
            if 'Unit' in df.columns:
                units = df['Unit'].value_counts()
                print("\nUnit distribution:")
                for unit, count in units.items():
                    print(f"  {unit}: {count}")
            
            print("\nCatalog looks good!")
        
        except Exception as e:
            print(f"Error checking catalog: {str(e)}")
            return 1
    
    elif args.command == 'add-mapping':
        mapper = CatalogMapper(args.catalog, args.config)
        
        search_terms = [term.strip() for term in args.terms.split(',')]
        
        mapping_data = {
            "search_terms": search_terms
        }
        
        if args.items:
            item_ids = [item_id.strip() for item_id in args.items.split(',')]
            
            # Find these items in the catalog to determine their tiers
            items_by_tier = {"Premium": [], "Luxury": [], "Ultra-Luxury": []}
            
            for item_id in item_ids:
                item = mapper.catalog[mapper.catalog['ID'] == item_id]
                if not item.empty:
                    tier = item.iloc[0].get('ConstructionTier', 'Luxury')
                    items_by_tier[tier].append(item_id)
            
            mapping_data["tier_item_ids"] = items_by_tier
        
        result = mapper.add_quantity_mapping(args.module, args.quantity, mapping_data)
        
        if result:
            print(f"Added mapping for {args.module}.{args.quantity}")
        else:
            print("Error adding mapping")
            return 1
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())