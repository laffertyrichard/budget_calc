# src/utils/electrical_validator.py

import pandas as pd
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ElectricalCatalogValidator:
    """Validates catalog coverage for electrical estimation"""
    
    def __init__(self, catalog_mapper, electrical_estimator=None):
        """
        Initialize the electrical catalog validator
        
        Args:
            catalog_mapper: Instance of CatalogMapper
            electrical_estimator: Optional instance of ElectricalEstimator
        """
        self.catalog_mapper = catalog_mapper
        self.electrical_estimator = electrical_estimator
        
        # Import electrical estimator if not provided
        if not self.electrical_estimator:
            try:
                from src.estimators.electrical import ElectricalEstimator
                self.electrical_estimator = ElectricalEstimator()
            except ImportError:
                logger.error("Could not import ElectricalEstimator")
        
    def validate_catalog_coverage(self, tier='Luxury', square_footage=5000):
        """
        Validate catalog coverage for all standard electrical quantities
        
        Args:
            tier: Construction tier to validate
            square_footage: Square footage for testing
            
        Returns:
            Dictionary with validation results
        """
        # Get standard quantities from estimator
        test_data = {
            "square_footage": square_footage,
            "tier": tier
        }
        
        quantities = {}
        if self.electrical_estimator:
            quantities = self.electrical_estimator.calculate_quantities(**test_data)
        
        results = {
            "total_quantities": 0,
            "matched_quantities": 0,
            "missing_matches": [],
            "tier_coverage": {
                "Premium": {"matched": 0, "total": 0},
                "Luxury": {"matched": 0, "total": 0},
                "Ultra-Luxury": {"matched": 0, "total": 0}
            },
            "match_quality": {}
        }
        
        # Check coverage for each quantity across all tiers
        for quantity_name in quantities:
            if quantity_name == "units":
                continue
                
            results["total_quantities"] += 1
            quantity_matched = False
            tier_matches = {}
            
            for test_tier in ["Premium", "Luxury", "Ultra-Luxury"]:
                # Try to get matches
                if hasattr(self.catalog_mapper, 'get_electrical_catalog_items'):
                    matches = self.catalog_mapper.get_electrical_catalog_items(
                        quantity_name, test_tier
                    )
                else:
                    matches = self.catalog_mapper.get_catalog_items_for_quantity(
                        "electrical", quantity_name, test_tier
                    )
                
                results["tier_coverage"][test_tier]["total"] += 1
                
                if matches:
                    tier_matches[test_tier] = len(matches)
                    results["tier_coverage"][test_tier]["matched"] += 1
                    quantity_matched = True
                
            if quantity_matched:
                results["matched_quantities"] += 1
                results["match_quality"][quantity_name] = tier_matches
            else:
                results["missing_matches"].append(quantity_name)
        
        # Calculate coverage percentages
        for tier in results["tier_coverage"]:
            tier_data = results["tier_coverage"][tier]
            if tier_data["total"] > 0:
                tier_data["coverage_pct"] = round(
                    tier_data["matched"] / tier_data["total"] * 100, 1
                )
            else:
                tier_data["coverage_pct"] = 0
                
        results["overall_coverage_pct"] = round(
            results["matched_quantities"] / results["total_quantities"] * 100, 1
        ) if results["total_quantities"] > 0 else 0
        
        return results
    
    def generate_missing_mappings(self):
        """
        Generate suggested mappings for missing electrical quantities
        
        Returns:
            Dictionary with suggested mappings
        """
        # Get validation results
        validation = self.validate_catalog_coverage()
        
        suggestions = {}
        
        for quantity_name in validation["missing_matches"]:
            # Generate search terms from quantity name
            search_terms = self._derive_search_terms(quantity_name)
            
            # Sample items that could match from the catalog
            potential_items = []
            if hasattr(self.catalog_mapper, 'catalog'):
                for term in search_terms:
                    matches = self.catalog_mapper.catalog[
                        (self.catalog_mapper.catalog['EstimatorModule'] == "electrical") &
                        (self.catalog_mapper.catalog['SearchItem'].str.contains(term, case=False, na=False))
                    ]
                    
                    if not matches.empty:
                        for _, item in matches.head(2).iterrows():
                            potential_items.append({
                                "id": item["ID"],
                                "name": item["Item"]
                            })
            
            # Create suggestion
            suggestions[quantity_name] = {
                "search_terms": search_terms,
                "potential_items": potential_items,
                "suggested_mapping": {
                    "search_terms": search_terms,
                    "tier_item_ids": {
                        "Premium": [],
                        "Luxury": [],
                        "Ultra-Luxury": []
                    }
                }
            }
        
        return suggestions
    
    def _derive_search_terms(self, quantity_name):
        """
        Derive search terms from quantity name
        
        Args:
            quantity_name: Name of the quantity
            
        Returns:
            List of search terms
        """
        terms = []
        
        # Split by underscore
        parts = quantity_name.split('_')
        terms.extend(parts)
        
        # Handle plurals
        for part in parts:
            if part.endswith('s'):
                terms.append(part[:-1])  # singular
            else:
                terms.append(part + 's')  # plural
                
        # Add electrical specific synonyms
        electrical_terms = {
            "outlet": ["receptacle", "plug"],
            "switch": ["control"],
            "light": ["fixture", "lighting"],
            "recessed": ["can", "pot", "downlight"]
        }
        
        for part in parts:
            if part in electrical_terms:
                terms.extend(electrical_terms[part])
                
        return list(set(terms))
    
    def export_mappings_to_json(self, output_file):
        """
        Export suggested mappings to a JSON file
        
        Args:
            output_file: Path to the output JSON file
            
        Returns:
            True if successful, False otherwise
        """
        suggestions = self.generate_missing_mappings()
        
        # Format for catalog_mappings.json
        formatted_mappings = {
            "electrical": {}
        }
        
        for quantity, data in suggestions.items():
            formatted_mappings["electrical"][quantity] = data["suggested_mapping"]
        
        try:
            with open(output_file, 'w') as f:
                json.dump(formatted_mappings, f, indent=2)
            logger.info(f"Exported missing mappings to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting mappings: {e}")
            return False
    
    def generate_validation_report(self):
        """
        Generate a text report of validation results
        
        Returns:
            String with validation report
        """
        validation = self.validate_catalog_coverage()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ELECTRICAL CATALOG VALIDATION REPORT")
        report_lines.append("=" * 80)
        
        # Overall summary
        report_lines.append(f"\nOverall Coverage: {validation['overall_coverage_pct']}% "
                           f"({validation['matched_quantities']}/{validation['total_quantities']} quantities)")
        
        # Tier coverage
        report_lines.append("\nTier Coverage:")
        for tier, data in validation["tier_coverage"].items():
            report_lines.append(f"  {tier}: {data.get('coverage_pct', 0)}% "
                               f"({data.get('matched', 0)}/{data.get('total', 0)} quantities)")
        
        # Missing quantities
        if validation["missing_matches"]:
            report_lines.append("\nMissing Matches:")
            for quantity in validation["missing_matches"]:
                report_lines.append(f"  - {quantity}")
                
                # Show suggested search terms
                search_terms = self._derive_search_terms(quantity)
                report_lines.append(f"    Suggested search terms: {', '.join(search_terms)}")
        
        # Match quality details
        report_lines.append("\nMatch Quality Details:")
        for quantity, tier_matches in validation["match_quality"].items():
            report_lines.append(f"  - {quantity}:")
            for tier, count in tier_matches.items():
                report_lines.append(f"    {tier}: {count} matches")
        
        return "\n".join(report_lines)

def main():
    """
    Command line entry point for the electrical catalog validator
    """
    import argparse
    from src.utils.catalog_mapper import CatalogMapper
    from src.estimators.electrical import ElectricalEstimator
    
    parser = argparse.ArgumentParser(description='Validate electrical catalog coverage')
    parser.add_argument('--catalog', required=True, help='Path to enhanced catalog CSV')
    parser.add_argument('--mappings', help='Path to mappings JSON (optional)')
    parser.add_argument('--output', help='Path to output JSON file for suggested mappings')
    parser.add_argument('--report', action='store_true', help='Generate a detailed report')
    
    args = parser.parse_args()
    
    # Initialize components
    catalog_mapper = CatalogMapper(args.catalog, args.mappings)
    electrical_estimator = ElectricalEstimator()
    
    # Create validator
    validator = ElectricalCatalogValidator(catalog_mapper, electrical_estimator)
    
    # Generate validation report
    if args.report:
        report = validator.generate_validation_report()
        print(report)
    
    # Export suggested mappings
    if args.output:
        success = validator.export_mappings_to_json(args.output)
        if success:
            print(f"Exported suggested mappings to {args.output}")
        else:
            print("Failed to export mappings")

if __name__ == "__main__":
    main()