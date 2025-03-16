# src/utils/catalog_validator.py

import pandas as pd
import logging
import json
import os
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

class CatalogValidator:
    """Utility for validating catalog data"""
    
    def __init__(self, config_path: str = 'config/settings.json'):
        """Initialize with path to configuration file"""
        self.config = self._load_json(config_path)
        self.mappings = self._load_json(os.path.join('config', 'mappings.json'))
        self.catalog = None
        self.enhanced_catalog = None
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'info': []
        }
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load and parse a JSON file"""
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            self.validation_results['errors'].append(f"File not found: {path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in: {path}")
            self.validation_results['errors'].append(f"Invalid JSON format in: {path}")
            return {}
    
    def load_catalog(self, path: Optional[str] = None) -> pd.DataFrame:
        """Load the catalog CSV file"""
        catalog_path = path or self.config.get('data', {}).get('catalog_path', 'data/catalog.csv')
        
        try:
            self.catalog = pd.read_csv(catalog_path)
            self.validation_results['info'].append(f"Loaded catalog with {len(self.catalog)} items")
            return self.catalog
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {catalog_path}")
            self.validation_results['errors'].append(f"Catalog file not found: {catalog_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            self.validation_results['errors'].append(f"Error loading catalog: {str(e)}")
            return pd.DataFrame()
    
    def load_enhanced_catalog(self, path: Optional[str] = None) -> pd.DataFrame:
        """Load the enhanced catalog CSV file"""
        enhanced_catalog_path = path or self.config.get('data', {}).get('enhanced_catalog_path')
        
        if not enhanced_catalog_path:
            self.validation_results['warnings'].append("Enhanced catalog path not defined in config")
            return pd.DataFrame()
        
        try:
            self.enhanced_catalog = pd.read_csv(enhanced_catalog_path)
            self.validation_results['info'].append(f"Loaded enhanced catalog with {len(self.enhanced_catalog)} items")
            return self.enhanced_catalog
        except FileNotFoundError:
            logger.error(f"Enhanced catalog file not found: {enhanced_catalog_path}")
            self.validation_results['warnings'].append(f"Enhanced catalog file not found: {enhanced_catalog_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading enhanced catalog: {str(e)}")
            self.validation_results['errors'].append(f"Error loading enhanced catalog: {str(e)}")
            return pd.DataFrame()
    
    def validate(self) -> Dict[str, List[str]]:
        """Run all validation checks"""
        # Reset validation results
        self.validation_results = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Load catalogs if not already loaded
        if self.catalog is None:
            self.load_catalog()
        
        if self.enhanced_catalog is None:
            self.load_enhanced_catalog()
        
        # Run validation checks on base catalog
        if not self.catalog.empty:
            self._validate_required_columns()
            self._validate_data_types()
            self._validate_cost_values()
            self._validate_id_uniqueness()
            self._validate_categories()
        
        # Run validation checks on enhanced catalog
        if not self.enhanced_catalog.empty:
            self._validate_enhanced_catalog()
            self._validate_enhanced_mappings()
        
        # Validate mapping between catalogs
        if not self.catalog.empty and not self.enhanced_catalog.empty:
            self._validate_catalog_consistency()
        
        return self.validation_results
    
    def _validate_required_columns(self):
        """Validate that the catalog has all required columns"""
        required_columns = ['Item', 'Cost(Mid)', 'Unit', 'Category', 'ID']
        
        missing_columns = [col for col in required_columns if col not in self.catalog.columns]
        
        if missing_columns:
            self.validation_results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
        else:
            self.validation_results['info'].append("All required columns present")
    
    def _validate_data_types(self):
        """Validate that catalog data has correct types"""
        # Check for non-numeric values in numeric columns
        numeric_columns = ['Cost(Mid)', 'Cost (Low)', 'Cost (High)', 'Markup Percentage']
        
        for col in numeric_columns:
            if col in self.catalog.columns:
                # Check if column is numeric
                non_numeric = self.catalog[~pd.to_numeric(self.catalog[col], errors='coerce').notna()]
                
                if not non_numeric.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(non_numeric)} non-numeric values in column '{col}'"
                    )
                    # Show a few examples
                    for _, row in non_numeric.head(3).iterrows():
                        self.validation_results['errors'].append(
                            f"  ID: {row.get('ID', 'N/A')}, Item: {row.get('Item', 'N/A')}, {col}: {row.get(col, 'N/A')}"
                        )
    
    def _validate_cost_values(self):
        """Validate that cost values make sense"""
        # Check for negative costs
        for col in ['Cost(Mid)', 'Cost (Low)', 'Cost (High)']:
            if col in self.catalog.columns:
                negative_costs = self.catalog[pd.to_numeric(self.catalog[col], errors='coerce') < 0]
                
                if not negative_costs.empty:
                    self.validation_results['errors'].append(
                        f"Found {len(negative_costs)} negative values in column '{col}'"
                    )
                    # Show a few examples
                    for _, row in negative_costs.head(3).iterrows():
                        self.validation_results['errors'].append(
                            f"  ID: {row.get('ID', 'N/A')}, Item: {row.get('Item', 'N/A')}, {col}: {row.get(col, 'N/A')}"
                        )
        
        # Check if Low <= Mid <= High
        if all(col in self.catalog.columns for col in ['Cost (Low)', 'Cost(Mid)', 'Cost (High)']):
            # Convert to numeric and handle errors
            low = pd.to_numeric(self.catalog['Cost (Low)'], errors='coerce')
            mid = pd.to_numeric(self.catalog['Cost(Mid)'], errors='coerce')
            high = pd.to_numeric(self.catalog['Cost (High)'], errors='coerce')
            
            # Check if low > mid
            low_gt_mid = self.catalog[(low > mid) & low.notna() & mid.notna()]
            if not low_gt_mid.empty:
                self.validation_results['errors'].append(
                    f"Found {len(low_gt_mid)} items where 'Cost (Low)' > 'Cost(Mid)'"
                )
                
            # Check if mid > high
            mid_gt_high = self.catalog[(mid > high) & mid.notna() & high.notna()]
            if not mid_gt_high.empty:
                self.validation_results['errors'].append(
                    f"Found {len(mid_gt_high)} items where 'Cost(Mid)' > 'Cost (High)'"
                )
    
    def _validate_id_uniqueness(self):
        """Validate that IDs are unique"""
        if 'ID' in self.catalog.columns:
            duplicate_ids = self.catalog[self.catalog['ID'].duplicated(keep=False)]
            
            if not duplicate_ids.empty:
                self.validation_results['errors'].append(
                    f"Found {len(duplicate_ids)} items with duplicate IDs"
                )
                # Group by ID and show duplicates
                for id_val, group in duplicate_ids.groupby('ID'):
                    self.validation_results['errors'].append(
                        f"  ID: {id_val} appears {len(group)} times"
                    )
    
    def _validate_categories(self):
        """Validate that categories match defined mappings"""
        if 'Category' in self.catalog.columns:
            # Get all unique categories
            unique_categories = self.catalog['Category'].unique()
            
            # Get all defined categories from mappings
            defined_categories = []
            for mapping in self.mappings.get('category_mappings', {}).values():
                defined_categories.extend(mapping.get('catalog_categories', []))
            
            # Find categories not in mappings
            undefined_categories = [cat for cat in unique_categories if cat not in defined_categories]
            
            if undefined_categories:
                self.validation_results['warnings'].append(
                    f"Found {len(undefined_categories)} categories not defined in mappings: "
                    f"{', '.join(str(c) for c in undefined_categories)}"
                )
    
    def _validate_enhanced_catalog(self):
        """Validate the enhanced catalog structure"""
        # Check for required enhanced columns
        enhanced_columns = ['SearchItem', 'EstimatorModule', 'QualityTier', 'ConstructionTier']
        
        missing_columns = [col for col in enhanced_columns if col not in self.enhanced_catalog.columns]
        
        if missing_columns:
            self.validation_results['warnings'].append(
                f"Enhanced catalog is missing some columns: {', '.join(missing_columns)}"
            )
        else:
            self.validation_results['info'].append("Enhanced catalog has all required columns")
        
        # Check that all items have an estimator module assigned
        if 'EstimatorModule' in self.enhanced_catalog.columns:
            missing_module = self.enhanced_catalog[self.enhanced_catalog['EstimatorModule'].isna() | 
                                                 (self.enhanced_catalog['EstimatorModule'] == '')]
            
            if not missing_module.empty:
                self.validation_results['warnings'].append(
                    f"Found {len(missing_module)} items without an estimator module assigned"
                )
        
        # Check that all items have a construction tier assigned
        if 'ConstructionTier' in self.enhanced_catalog.columns:
            missing_tier = self.enhanced_catalog[self.enhanced_catalog['ConstructionTier'].isna() | 
                                               (self.enhanced_catalog['ConstructionTier'] == '')]
            
            if not missing_tier.empty:
                self.validation_results['warnings'].append(
                    f"Found {len(missing_tier)} items without a construction tier assigned"
                )
    
    def _validate_enhanced_mappings(self):
        """Validate enhanced catalog mappings"""
        # Check that all EstimatorModule values are valid
        if 'EstimatorModule' in self.enhanced_catalog.columns:
            # Get all unique module values
            unique_modules = self.enhanced_catalog['EstimatorModule'].dropna().unique()
            
            # Get all defined estimator modules from mappings
            defined_modules = list(self.mappings.get('category_mappings', {}).keys())
            
            # Find modules not in mappings
            undefined_modules = [mod for mod in unique_modules if mod not in defined_modules]
            
            if undefined_modules:
                self.validation_results['warnings'].append(
                    f"Found {len(undefined_modules)} estimator modules not defined in mappings: "
                    f"{', '.join(str(m) for m in undefined_modules)}"
                )
        
        # Check that all ConstructionTier values are valid
        if 'ConstructionTier' in self.enhanced_catalog.columns:
            # Get all unique tier values
            unique_tiers = self.enhanced_catalog['ConstructionTier'].dropna().unique()
            
            # Get all defined tiers from config
            defined_tiers = list(self.config.get('estimation', {}).get('tiers', {}).keys())
            
            # Find tiers not in config
            undefined_tiers = [tier for tier in unique_tiers if tier not in defined_tiers]
            
            if undefined_tiers:
                self.validation_results['warnings'].append(
                    f"Found {len(undefined_tiers)} construction tiers not defined in config: "
                    f"{', '.join(str(t) for t in undefined_tiers)}"
                )
    
    def _validate_catalog_consistency(self):
        """Validate consistency between base and enhanced catalogs"""
        # Check that all IDs in base catalog are in enhanced catalog
        if 'ID' in self.catalog.columns and 'ID' in self.enhanced_catalog.columns:
            base_ids = set(self.catalog['ID'].dropna())
            enhanced_ids = set(self.enhanced_catalog['ID'].dropna())
            
            # Find IDs in base but not in enhanced
            missing_in_enhanced = base_ids - enhanced_ids
            
            if missing_in_enhanced:
                self.validation_results['warnings'].append(
                    f"Found {len(missing_in_enhanced)} items in base catalog not in enhanced catalog"
                )
                if len(missing_in_enhanced) <= 5:
                    self.validation_results['warnings'].append(
                        f"  Missing IDs: {', '.join(str(i) for i in missing_in_enhanced)}"
                    )
            
            # Find IDs in enhanced but not in base
            extra_in_enhanced = enhanced_ids - base_ids
            
            if extra_in_enhanced:
                self.validation_results['warnings'].append(
                    f"Found {len(extra_in_enhanced)} items in enhanced catalog not in base catalog"
                )
                if len(extra_in_enhanced) <= 5:
                    self.validation_results['warnings'].append(
                        f"  Extra IDs: {', '.join(str(i) for i in extra_in_enhanced)}"
                    )
    
    def check_estimation_coverage(self) -> Dict[str, Dict[str, Any]]:
        """Check if all estimator quantities have matching catalog items"""
        coverage_results = {}
        
        # Load catalogs if not already loaded
        if self.catalog is None:
            self.load_catalog()
        
        if self.enhanced_catalog is None:
            self.load_enhanced_catalog()
        
        # Load catalog mapping configuration
        mapping_path = self.config.get('data', {}).get('catalog_mappings_path', 'config/catalog_mappings.json')
        catalog_mappings = self._load_json(mapping_path)
        
        # Iterate through all defined estimator modules
        for module_name, module_info in catalog_mappings.get('estimator_modules', {}).items():
            module_coverage = {
                'total_quantities': 0,
                'mapped_quantities': 0,
                'unmapped_quantities': [],
                'tier_coverage': {
                    'Premium': 0,
                    'Luxury': 0,
                    'Ultra-Luxury': 0
                }
            }
            
            # Check each quantity mapping
            for quantity_name, mapping_info in module_info.get('quantity_mappings', {}).items():
                module_coverage['total_quantities'] += 1
                
                # Check if it has search terms
                has_search_terms = 'search_terms' in mapping_info and mapping_info['search_terms']
                
                # Check tier coverage
                tier_items = mapping_info.get('tier_item_ids', {})
                for tier in ['Premium', 'Luxury', 'Ultra-Luxury']:
                    if tier in tier_items and tier_items[tier]:
                        module_coverage['tier_coverage'][tier] += 1
                
                # Consider it mapped if it has search terms or at least one tier has items
                if has_search_terms or any(tier_items.get(tier) for tier in ['Premium', 'Luxury', 'Ultra-Luxury']):
                    module_coverage['mapped_quantities'] += 1
                else:
                    module_coverage['unmapped_quantities'].append(quantity_name)
            
            coverage_results[module_name] = module_coverage
        
        # Calculate overall coverage
        total_quantities = sum(m['total_quantities'] for m in coverage_results.values())
        mapped_quantities = sum(m['mapped_quantities'] for m in coverage_results.values())
        
        overall_coverage = {
            'total_modules': len(coverage_results),
            'total_quantities': total_quantities,
            'mapped_quantities': mapped_quantities,
            'coverage_percentage': round((mapped_quantities / total_quantities * 100) if total_quantities > 0 else 0, 1),
            'tier_coverage': {
                'Premium': sum(m['tier_coverage']['Premium'] for m in coverage_results.values()),
                'Luxury': sum(m['tier_coverage']['Luxury'] for m in coverage_results.values()),
                'Ultra-Luxury': sum(m['tier_coverage']['Ultra-Luxury'] for m in coverage_results.values())
            }
        }
        
        coverage_results['overall'] = overall_coverage
        
        return coverage_results
    
    def check_duplicate_cost_items(self) -> List[Dict[str, Any]]:
        """Check for potential duplicate items in the catalog"""
        if self.catalog is None:
            self.load_catalog()
            
        if self.catalog.empty:
            return []
            
        # Create a clean version of item names for comparison
        self.catalog['CleanItem'] = self.catalog['Item'].str.lower().str.replace(r'[^\w\s]', '', regex=True).str.strip()
        
        # Group by clean name and find groups with more than one item
        duplicates = []
        
        for clean_name, group in self.catalog.groupby('CleanItem'):
            if len(group) > 1:
                # Check if costs are significantly different
                costs = group['Cost(Mid)'].dropna().tolist()
                max_cost = max(costs) if costs else 0
                min_cost = min(costs) if costs else 0
                
                # Consider it notable if the max is at least 25% more than the min
                cost_difference = (max_cost - min_cost) / min_cost if min_cost > 0 else 0
                
                if cost_difference >= 0.25:
                    duplicates.append({
                        'clean_name': clean_name,
                        'count': len(group),
                        'cost_difference_pct': round(cost_difference * 100, 1),
                        'items': group[['ID', 'Item', 'Category', 'Cost(Mid)']].to_dict('records')
                    })
        
        # Sort by count (most duplicates first)
        duplicates.sort(key=lambda x: x['count'], reverse=True)
        
        return duplicates
    
    def generate_report(self) -> str:
        """Generate a text report of validation results"""
        if not self.validation_results['errors'] and not self.validation_results['warnings'] and not self.validation_results['info']:
            self.validate()
            
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CATALOG VALIDATION REPORT")
        report_lines.append("=" * 80)
        
        # Add validation results
        report_lines.append("\nVALIDATION RESULTS:")
        
        if self.validation_results['errors']:
            report_lines.append("\nERRORS:")
            for error in self.validation_results['errors']:
                report_lines.append(f"- {error}")
        else:
            report_lines.append("\nNo errors found.")
            
        if self.validation_results['warnings']:
            report_lines.append("\nWARNINGS:")
            for warning in self.validation_results['warnings']:
                report_lines.append(f"- {warning}")
        else:
            report_lines.append("\nNo warnings found.")
            
        if self.validation_results['info']:
            report_lines.append("\nINFO:")
            for info in self.validation_results['info']:
                report_lines.append(f"- {info}")
            
        # Add coverage results
        coverage_results = self.check_estimation_coverage()
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("ESTIMATION COVERAGE ANALYSIS")
        report_lines.append("=" * 80)
        
        overall = coverage_results.get('overall', {})
        
        report_lines.append(f"\nOverall Coverage: {overall.get('coverage_percentage', 0)}% ({overall.get('mapped_quantities', 0)}/{overall.get('total_quantities', 0)} quantities)")
        report_lines.append(f"Total Modules: {overall.get('total_modules', 0)}")
        
        report_lines.append("\nTier Coverage:")
        for tier in ['Premium', 'Luxury', 'Ultra-Luxury']:
            tier_count = overall.get('tier_coverage', {}).get(tier, 0)
            tier_pct = round((tier_count / overall.get('total_quantities', 1)) * 100, 1)
            report_lines.append(f"- {tier}: {tier_pct}% ({tier_count}/{overall.get('total_quantities', 0)} quantities)")
        
        report_lines.append("\nModule Coverage:")
        for module, data in coverage_results.items():
            if module == 'overall':
                continue
                
            if data['total_quantities'] > 0:
                coverage_pct = round((data['mapped_quantities'] / data['total_quantities']) * 100, 1)
                report_lines.append(f"- {module}: {coverage_pct}% ({data['mapped_quantities']}/{data['total_quantities']} quantities)")
                
                if data['unmapped_quantities']:
                    report_lines.append(f"  Unmapped: {', '.join(data['unmapped_quantities'])}")
        
        # Add duplicate analysis
        duplicates = self.check_duplicate_cost_items()
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("DUPLICATE ITEM ANALYSIS")
        report_lines.append("=" * 80)
        
        if duplicates:
            report_lines.append(f"\nFound {len(duplicates)} potential duplicate items with significant cost differences:")
            
            for i, dup in enumerate(duplicates[:10]):  # Show only top 10
                report_lines.append(f"\n{i+1}. \"{dup['clean_name']}\" ({dup['count']} occurrences, {dup['cost_difference_pct']}% cost difference)")
                
                for item in dup['items']:
                    report_lines.append(f"   - {item['ID']}: {item['Item']} (${item['Cost(Mid)']:.2f}, {item['Category']})")
                    
            if len(duplicates) > 10:
                report_lines.append(f"\n... and {len(duplicates) - 10} more potential duplicates.")
        else:
            report_lines.append("\nNo potential duplicate items found.")
            
        return "\n".join(report_lines)

def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate construction catalog data')
    parser.add_argument('--config', help='Path to configuration file', default='config/settings.json')
    parser.add_argument('--catalog', help='Path to catalog CSV file')
    parser.add_argument('--enhanced', help='Path to enhanced catalog CSV file')
    parser.add_argument('--report', help='Generate a detailed report', action='store_true')
    parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create validator
    validator = CatalogValidator(args.config)
    
    # Load catalogs
    if args.catalog:
        validator.load_catalog(args.catalog)
    else:
        validator.load_catalog()
        
    if args.enhanced:
        validator.load_enhanced_catalog(args.enhanced)
    else:
        validator.load_enhanced_catalog()
    
    # Run validation
    results = validator.validate()
    
    # Print validation results
    print("\nValidation Results:")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"- {error}")
    else:
        print("\nNo errors found.")
        
    if results['warnings']:
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"- {warning}")
    else:
        print("\nNo warnings found.")
        
    if results['info']:
        print("\nInfo:")
        for info in results['info']:
            print(f"- {info}")
    
    # Generate report if requested
    if args.report:
        report = validator.generate_report()
        
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(report)
                print(f"\nDetailed report saved to: {args.output}")
            except Exception as e:
                print(f"\nError saving report: {str(e)}")
        else:
            print("\n" + report)
    
    return 0

if __name__ == "__main__":
    main()