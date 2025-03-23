# src/core/estimation_engine.py (key fixes)

import logging
import importlib
import os
import pandas as pd 
from typing import Dict, Any, Union, List, Optional
from datetime import datetime
from src.core.data_loader import DataLoader
from src.utils.catalog_mapper import CatalogMapper
from src.core.material_manager import MaterialManager

logger = logging.getLogger(__name__)

class EstimationEngine:
    """Core estimation engine that integrates quantities with costs"""
    
    def __init__(self, config_path='config/settings.json'):
        """Initialize the estimation engine"""
        self.data_loader = DataLoader(config_path)
        self.config = self.data_loader.config
        self.mappings = self.data_loader.mappings
        self.catalog = self.data_loader.load_catalog()
        self.estimators = self._initialize_estimators()
        self.current_project_data = {}  # Store current project data
        self._match_cache = {}  # Cache for catalog matches
        
        # Add caching for electrical lookups
        self._electrical_cache = {}
        self._unmatched_electrical = []
        self._prefiltered_catalogs = {}
        
        # Initialize catalog mapper if enhanced catalog exists
        enhanced_catalog_path = self.config.get('data', {}).get('enhanced_catalog_path')
        if (enhanced_catalog_path and os.path.exists(enhanced_catalog_path)):
            self.catalog_mapper = CatalogMapper(enhanced_catalog_path)
        else:
            self.catalog_mapper = None
    
    def _initialize_estimators(self):
        """Initialize all estimator modules based on mappings with better error handling"""
        estimators = {}
        
        for category in self.mappings.get('category_mappings', {}):
            try:
                # Dynamically import the estimator module
                module_name = f"src.estimators.{category}"
                logger.info(f"Attempting to load module: {module_name}")
                try:
                    module = importlib.import_module(module_name)
                    # Get the estimator class (assumed to be named CategoryEstimator)
                    class_name = f"{category.title().replace('_', '')}Estimator"
                    logger.info(f"Attempting to load class: {class_name} from module: {module_name}")
                    estimator_class = getattr(module, class_name)
                    estimator = estimator_class()
                    
                    # Pass config to estimator if it accepts it
                    if hasattr(estimator, 'set_config'):
                        estimator.set_config(self.config)
                        
                    estimators[category] = estimator
                    logger.info(f"Loaded estimator for {category}")
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not load estimator for {category}: {str(e)}")
                    # Add a placeholder that will later be properly implemented
                    estimators[category] = None
            except Exception as e:
                logger.error(f"Error initializing estimator for {category}: {str(e)}")
                estimators[category] = None
        
        logger.info(f"Initialized estimators: {list(estimators.keys())}")
        return estimators
    
    def validate_project_data(self, project_data):
        """Validate project data to ensure required fields are present and valid"""
        required_fields = ['square_footage']
        validation_results = {
            'is_valid': True,
            'missing_fields': [],
            'invalid_values': [],
            'warnings': []
        }
        
        # Check for missing required fields
        for field in required_fields:
            if field not in project_data:
                validation_results['is_valid'] = False
                validation_results['missing_fields'].append(field)
        
        # Validate field values
        if 'square_footage' in project_data:
            if not isinstance(project_data['square_footage'], (int, float)):
                validation_results['is_valid'] = False
                validation_results['invalid_values'].append({
                    'field': 'square_footage',
                    'value': project_data['square_footage'],
                    'message': 'Square footage must be a number'
                })
            elif project_data['square_footage'] <= 0:
                validation_results['is_valid'] = False
                validation_results['invalid_values'].append({
                    'field': 'square_footage',
                    'value': project_data['square_footage'],
                    'message': 'Square footage must be a positive number'
                })
            elif project_data['square_footage'] > 25000:
                validation_results['warnings'].append('Square footage exceeds typical residential size')
        
        # Check for valid tier if provided
        if 'tier' in project_data:
            valid_tiers = ['Premium', 'Luxury', 'Ultra-Luxury']
            if project_data['tier'] not in valid_tiers:
                validation_results['is_valid'] = False
                validation_results['invalid_values'].append({
                    'field': 'tier',
                    'value': project_data['tier'],
                    'message': f'Tier must be one of: {", ".join(valid_tiers)}'
                })
        
        # Validate bath counts
        for field in ['primary_bath_count', 'secondary_bath_count', 'powder_room_count']:
            if field in project_data:
                if not isinstance(project_data[field], (int, float)) or project_data[field] < 0:
                    validation_results['is_valid'] = False
                    validation_results['invalid_values'].append({
                        'field': field,
                        'value': project_data[field],
                        'message': f'{field.replace("_", " ").title()} must be a non-negative number'
                    })
        
        # Validate bedroom count
        if 'bedroom_count' in project_data:
            if not isinstance(project_data['bedroom_count'], (int, float)) or project_data['bedroom_count'] <= 0:
                validation_results['is_valid'] = False
                validation_results['invalid_values'].append({
                    'field': 'bedroom_count',
                    'value': project_data['bedroom_count'],
                    'message': 'Bedroom count must be a positive number'
                })
            elif project_data['bedroom_count'] > 10:
                validation_results['warnings'].append('Bedroom count is unusually high')
        
        return validation_results
    
    def estimate_project(self, project_data):
        """Run estimation for all categories based on project data with improved error handling"""
        # Store the current project data for reference in other methods
        self.current_project_data = project_data.copy()
        
        # Clear caches before new estimation
        self._electrical_cache = {}
        self._unmatched_electrical = []
        self._prefiltered_catalogs = {}
        self._match_cache = {}
        
        # Validate project data
        validation_results = self.validate_project_data(project_data)
        if not validation_results['is_valid']:
            return {
                'status': 'validation_error',
                'validation_results': validation_results,
                'message': 'Invalid project data'
            }
        
        results = {
            'project': project_data.copy(),
            'categories': {},
            'summary': {
                'cost_breakdown': {},
                'warnings': validation_results.get('warnings', []),
                'metadata': {
                    'estimation_date': datetime.now().isoformat(),
                    'catalog_version': getattr(self.catalog, 'version', 'unknown'),
                    'catalog_item_count': len(self.catalog) if self.catalog is not None else 0
                }
            }
        }
        
        # Determine tier if not provided
        if 'tier' not in project_data:
            square_footage = project_data.get('square_footage', 0)
            project_data['tier'] = self._determine_tier(square_footage)
            results['project']['tier'] = project_data['tier']
        
        # Run estimation for each category
        total_cost = 0
        category_costs = {}
        
        for category, estimator in self.estimators.items():
            logger.info(f"Estimating category: {category}")
            print(f"Estimating category: {category}")
            if estimator is None:
                results['categories'][category] = {
                    'status': 'not_implemented',
                    'message': f"Estimator for {category} is not yet implemented"
                }
                results['summary']['warnings'].append(f"Category '{category}' has no estimator implementation")
                continue
                
            try:
                # Calculate quantities
                quantities = estimator.calculate_quantities(
                    square_footage=project_data.get('square_footage', 0),
                    tier=project_data.get('tier', 'Premium'),
                    **{k: v for k, v in project_data.items() if k not in ['square_footage', 'tier']}  # Pass remaining project data as kwargs
                )
                logger.info(f"Calculated quantities for {category}: {quantities}")
                print(f"Calculated quantities for {category}: {quantities}")
                
                # Match with catalog costs if quantities were calculated
                if quantities:
                    costed_items = self._apply_costs(category, quantities)
                    logger.info(f"Costed items for {category}: {costed_items}")
                    print(f"Costed items for {category}: {costed_items}")
                    
                    # Check for missing matches
                    quantity_keys = set(quantities.keys())
                    matched_quantities = set(item['original_quantity_name'] for item in costed_items if 'original_quantity_name' in item)
                    unmatched_quantities = quantity_keys - matched_quantities
                    
                    # Filter out known non-quantity keys like 'units'
                    unmatched_quantities = [q for q in unmatched_quantities if q != 'units']
                    
                    if unmatched_quantities:
                        warning_msg = f"Category '{category}' has {len(unmatched_quantities)} unmatched quantities: {', '.join(unmatched_quantities)}"
                        results['summary']['warnings'].append(warning_msg)
                    
                    # Calculate totals
                    category_cost = sum(item.get('total_cost', 0) for item in costed_items)
                    total_cost += category_cost
                    category_costs[category] = category_cost
                    
                    results['categories'][category] = {
                        'status': 'success',
                        'quantities': quantities,
                        'costed_items': costed_items,
                        'total_cost': category_cost,
                        'unmatched_quantities': list(unmatched_quantities)
                    }
                else:
                    results['categories'][category] = {
                        'status': 'no_quantities',
                        'message': f"No quantities calculated for {category}"
                    }
                    results['summary']['warnings'].append(f"Category '{category}' produced no quantities")
            except Exception as e:
                logger.error(f"Error estimating {category}: {str(e)}", exc_info=True)
                results['categories'][category] = {
                    'status': 'error',
                    'message': str(e)
                }
                results['summary']['warnings'].append(f"Error in category '{category}': {str(e)}")
        
        # Add this function to sanitize NaN values
        def sanitize_cost(cost):
            """Replace NaN values with 0 for cost calculations"""
            if pd.isna(cost):
                return 0
            return cost
        
        # Sanitize category costs
        category_costs = {}
        for category, data in results['categories'].items():
            if data.get('status') == 'success':
                # Get the total cost, default to 0 if NaN
                cost = sanitize_cost(data.get('total_cost', 0))
                category_costs[category] = cost
        
        # Calculate the total cost
        total_cost = sum(sanitize_cost(cost) for cost in category_costs.values())
        
        # Add summary data
        results['summary']['cost_breakdown'] = category_costs
        results['total_cost'] = total_cost
        
        # Add percentage breakdown
        if total_cost > 0:
            results['summary']['percentage_breakdown'] = {
                category: (sanitize_cost(cost) / total_cost) * 100 
                for category, cost in category_costs.items()
            }
        
        # Clear the match cache after estimation
        self._match_cache = {}
        
        return results

    def _determine_tier(self, square_footage):
        """Determine project tier based on square footage"""
        tiers = self.config.get('estimation', {}).get('tiers', {})
        
        for tier, tier_info in tiers.items():
            min_sf = tier_info.get('min_sf', 0)
            max_sf = tier_info.get('max_sf')
            
            if min_sf <= square_footage and (max_sf is None or square_footage < max_sf):
                return tier
        
        # Return default tier if no match
        return self.config.get('estimation', {}).get('default_tier', 'Premium')
    
    def _extract_quantity_unit(self, quantities, quantity_name):
        """Extract unit from quantities dictionary if available."""
        # Check if units are provided in structured format
        if isinstance(quantities, dict) and 'units' in quantities and quantity_name in quantities.get('units', {}):
            return quantities['units'].get(quantity_name)
        
        # Try to guess from quantity name
        return self._guess_quantity_unit(quantity_name)
    
    def _apply_costs(self, category, quantities):
        """Apply costs from catalog to calculated quantities with direct lookups only"""
        if not quantities:
            logger.warning(f"No quantities provided for category: {category}")
            return []
            
        costed_items = []
        
        # Special handling for electrical service if this is the electrical category
        if category == "electrical" and "electrical_service_name" in quantities and "main_panel_size" in quantities:
            electrical_service_name = quantities["electrical_service_name"]
            main_panel_size = quantities["main_panel_size"]
            main_panel_quantity = quantities.get("main_panel_quantity", 1)
            
            # Find the exact match for this electrical service
            service_matches = self.catalog[
                (self.catalog['Item'].str.contains(electrical_service_name, case=False, na=False)) &
                (self.catalog['Item'].str.contains(str(main_panel_size), case=False, na=False))
            ]
            
            if not service_matches.empty:
                item = service_matches.iloc[0]
                unit_cost = item.get('Cost(Mid)', 0)
                total_cost = unit_cost * main_panel_quantity
                
                costed_items.append({
                    'item_id': item.get('ID', ''),
                    'item_name': item.get('Item', ''),
                    'category': item.get('Category', ''),
                    'quantity': main_panel_quantity,  # Use 1 or specified panel quantity, NOT the amp size
                    'unit': item.get('Unit', 'Each'),
                    'unit_cost': unit_cost,
                    'total_cost': total_cost,
                    'markup': item.get('Markup Percentage', 0),
                    'note': "Direct match for electrical service",
                    'original_quantity_name': "electrical_service",
                    'original_quantity_value': electrical_service_name
                })
                logger.info(f"Costed electrical service: {item.get('Item', '')} (quantity: {main_panel_quantity})")
        
        # Define quantities to skip for electrical service
        skip_quantities = ["electrical_service_name", "main_panel_size", "main_panel_quantity"] if category == "electrical" else []
        
        # Get category mapping
        category_mapping = self.mappings.get('category_mappings', {}).get(category, {})
        item_mappings = category_mapping.get('item_mappings', {})
        
        # Process each quantity
        for quantity_name, quantity_value in quantities.items():
            # Skip non-quantity keys like 'units'
            if quantity_name == 'units' or not quantity_value or quantity_name in skip_quantities:
                continue
            
            # Look for direct ID mappings first
            if quantity_name in item_mappings and item_mappings[quantity_name].get('item_ids'):
                item_ids = item_mappings[quantity_name].get('item_ids', [])
                
                # Find items with these IDs
                for item_id in item_ids:
                    matching_items = self.catalog[self.catalog['ID'] == item_id]
                    
                    if not matching_items.empty:
                        for _, item in matching_items.iterrows():
                            # Extract unit if provided
                            unit = self._extract_quantity_unit(quantities, quantity_name)
                            
                            # Calculate conversion factor if needed
                            catalog_unit = item.get('Unit', 'EA')
                            conversion_factor = self._get_unit_conversion_factor(unit, catalog_unit) or 1.0
                            
                            # Apply conversion factor
                            adjusted_quantity = quantity_value * conversion_factor
                            
                            # Calculate cost
                            unit_cost = item.get('Cost(Mid)', 0)
                            total_cost = unit_cost * adjusted_quantity
                            
                            # Add to costed items
                            costed_items.append({
                                'item_id': item_id,
                                'item_name': item.get('Item', ''),
                                'category': item.get('Category', ''),
                                'quantity': adjusted_quantity,
                                'unit': catalog_unit,
                                'unit_cost': unit_cost,
                                'total_cost': total_cost,
                                'markup': item.get('Markup Percentage', 0),
                                'note': "Direct match by ID",
                                'original_quantity_name': quantity_name,
                                'original_quantity_value': quantity_value
                            })
                            logger.info(f"Costed item by ID: {costed_items[-1]}")
                        
                        # We've found and processed matches, continue to next quantity
                        continue
                
                # If we get here, no items with those IDs were found
                logger.warning(f"No catalog items found with IDs {item_ids} for {quantity_name}")
            else:
                # Fallback for items without direct catalog match
                costed_items.append({
                    'item_name': quantity_name.replace('_', ' ').title(),
                    'quantity': quantity_value,
                    'unit': 'EA',
                    'unit_cost': 0,
                    'total_cost': 0,
                    'note': 'No catalog match found',
                    'original_quantity_name': quantity_name,
                    'original_quantity_value': quantity_value
                })
                logger.warning(f"No catalog match found for {quantity_name}")
        
        return costed_items
    
    def _prefilter_electrical_catalog(self):
        """Pre-filter catalog items for electrical category with error handling"""
        try:
            if hasattr(self.catalog_mapper, 'catalog') and not self.catalog_mapper.catalog.empty:
                # Extract all electrical items once
                electrical_catalog = self.catalog_mapper.catalog[
                    self.catalog_mapper.catalog['EstimatorModule'] == 'electrical'
                ]
                
                if not electrical_catalog.empty:
                    self._prefiltered_catalogs['electrical'] = electrical_catalog
                    
                    # Further segment by tier for faster lookups
                    self._prefiltered_catalogs['electrical_by_tier'] = {
                        "Premium": electrical_catalog[electrical_catalog['ConstructionTier'] == 'Premium'],
                        "Luxury": electrical_catalog[electrical_catalog['ConstructionTier'] == 'Luxury'],
                        "Ultra-Luxury": electrical_catalog[electrical_catalog['ConstructionTier'] == 'Ultra-Luxury']
                    }
                    
                    # Segment by component type for even faster lookups
                    component_terms = {
                        "outlets": ["outlet", "receptacle", "plug", "gfci"],
                        "switches": ["switch", "dimmer", "control"],
                        "lights": ["light", "fixture", "lamp", "recessed", "chandelier", "pendant"],
                        "panels": ["panel", "circuit", "breaker"]
                    }
                    
                    self._prefiltered_catalogs['electrical_by_component'] = {}
                    
                    for component, terms in component_terms.items():
                        component_filter = '|'.join(terms)
                        component_items = electrical_catalog[
                            electrical_catalog['SearchItem'].str.contains(component_filter, case=False, na=False)
                        ]
                        self._prefiltered_catalogs['electrical_by_component'][component] = component_items
        except Exception as e:
            logger.warning(f"Error pre-filtering electrical catalog: {str(e)}")
            # Continue without pre-filtering

    def _apply_costs_electrical(self, quantities):
        """
        Apply costs from catalog to electrical quantities with dynamic service selection
        """
        if not quantities:
            return []
        
        costed_items = []
        
        # Determine the electrical service based on distribution calculation
        electrical_service_name = quantities.get('electrical_service_name')
        main_panel_size = quantities.get('main_panel_size')
        main_panel_quantity = quantities.get('main_panel_quantity', 1)
        
        if electrical_service_name and main_panel_size:
            try:
                # Find matching catalog item for the electrical service
                matching_items = self.data_loader.catalog[
                    (self.data_loader.catalog['Item'].str.contains(electrical_service_name, case=False)) & 
                    (self.data_loader.catalog['Item'].str.contains(str(main_panel_size), case=False))
                ]
                
                # If matching items found, create costed item (only add the first/best match)
                if not matching_items.empty:
                    item = matching_items.iloc[0]
                    
                    # Calculate cost details
                    costed_item = {
                        'item_id': item.get('ID', ''),
                        'item_name': item.get('Item', electrical_service_name),
                        'category': item.get('Category', 'Electrical'),
                        'quantity': main_panel_quantity,  # Use panel quantity, NOT amp size
                        'unit': 'Each',
                        'unit_cost': float(item.get('Cost(Mid)', 0)),
                        'total_cost': float(item.get('Cost(Mid)', 0)) * main_panel_quantity,
                        'markup': float(item.get('Markup Percentage', 0)),
                        'note': 'Direct match for electrical service',
                        'original_quantity_name': 'electrical_service',
                        'original_quantity_value': electrical_service_name
                    }
                    
                    costed_items.append(costed_item)
                    logger.info(f"Costed electrical service: {item.get('Item', '')} (quantity: {main_panel_quantity})")
            except Exception as e:
                logger.warning(f"Error matching electrical service: {str(e)}")
        
        # Define quantities to ignore (service-related or circuit-related)
        ignore_quantities = [
            'electrical_service_name', 'main_panel_size', 'main_panel_quantity', 
            'units', 'sub_panels', 'total_baseline_circuits', 
            'total_additional_circuits', 'total_circuits'
        ]
        
        # Process other electrical quantities
        for quantity_name, quantity_value in quantities.items():
            # Skip ignored or zero-value quantities
            if quantity_name in ignore_quantities or not quantity_value:
                continue
            
            # Skip circuit quantities
            if quantity_name.endswith('_circuits'):
                continue
            
            try:
                # Find matching catalog items for the quantity
                matching_items = self.data_loader.catalog[
                    self.data_loader.catalog['Item'].str.contains(
                        quantity_name.replace('_', ' '), 
                        case=False
                    )
                ]
                
                if not matching_items.empty:
                    item = matching_items.iloc[0]
                    
                    costed_item = {
                        'item_id': item.get('ID', ''),
                        'item_name': item.get('Item', quantity_name.replace('_', ' ').title()),
                        'category': item.get('Category', 'Electrical'),
                        'quantity': quantity_value,
                        'unit': item.get('Unit', 'EA'),
                        'unit_cost': float(item.get('Cost(Mid)', 0)),
                        'total_cost': float(item.get('Cost(Mid)', 0)) * quantity_value,
                        'markup': float(item.get('Markup Percentage', 0)),
                        'note': f'Derived from {quantity_name}',
                        'original_quantity_name': quantity_name,
                        'original_quantity_value': quantity_value
                    }
                    
                    costed_items.append(costed_item)
                else:
                    # Fallback for items without direct catalog match
                    costed_items.append({
                        'item_name': quantity_name.replace('_', ' ').title(),
                        'quantity': quantity_value,
                        'unit': 'EA',
                        'unit_cost': 0,
                        'total_cost': 0,
                        'note': 'No catalog match found',
                        'original_quantity_name': quantity_name,
                        'original_quantity_value': quantity_value
                    })
            except Exception as e:
                logger.warning(f"Error processing electrical quantity {quantity_name}: {str(e)}")
        
        return costed_items

    def save_estimation(self, estimation_results, filename):
        """Save estimation results to a file"""
        return self.data_loader.save_estimation(estimation_results, filename)
        
    def load_estimation(self, filename):
        """Load a saved estimation"""
        return self.data_loader.load_estimation(filename)
    
    def _guess_quantity_unit(self, quantity_name: str) -> str:
        """Guess the most likely unit for a quantity based on its name"""
        name = quantity_name.lower()
        
        if any(term in name for term in ['_sf', 'square_feet', 'area', 'sqft']):
            return 'SF'
        elif any(term in name for term in ['_lf', 'linear_feet', 'length']):
            return 'LF'
        elif any(term in name for term in ['_cy', 'cubic_yards', 'concrete']):
            return 'CY'
        elif any(term in name for term in ['_ea', 'count', 'quantity']):
            return 'EA'
        elif any(term in name for term in ['gallons', '_gal']):
            return 'GAL'
        
        # Default to 'EA' if no match
        return 'EA'

    def _get_unit_conversion_factor(self, from_unit: str, to_unit: str) -> Union[float, None]:
        """Get conversion factor between units, or None if incompatible"""
        # If units are the same, no conversion needed
        if from_unit == to_unit:
            return 1.0
        
        # Define common conversions
        conversions = {
            # Area conversions
            ('SF', 'SY'): 1/9,   # Square feet to square yards
            ('SY', 'SF'): 9,     # Square yards to square feet
            ('SF', 'SQFT'): 1,   # Common unit aliases
            ('SQFT', 'SF'): 1,
            
            # Length conversions
            ('LF', 'FT'): 1,     # Linear feet to feet (same)
            ('FT', 'LF'): 1,
            
            # Volume conversions
            ('CY', 'CF'): 27,    # Cubic yards to cubic feet
            ('CF', 'CY'): 1/27,
            
            # Count/quantity conversions
            ('EA', 'EACH'): 1,   # Each (same)
            ('EACH', 'EA'): 1,
            
            # Liquid measure
            ('GAL', 'GALLON'): 1,
            ('GALLON', 'GAL'): 1
        }
        
        # Check if conversion exists
        key = (from_unit.upper(), to_unit.upper())
        if key in conversions:
            return conversions[key]
        
        # No valid conversion found
        return None
    
    def get_benchmark_data(self, tier=None):
        """Get benchmark cost data for comparison."""
        # This would typically load from a benchmark database
        # For now, we'll return some hardcoded values for demonstration
        benchmarks = {
            "Premium": {
                "foundation": 15.0,  # $ per square foot
                "structural": 22.5,
                "electrical": 12.0,
                "plumbing": 18.0,
                "hvac": 10.0,
                "interior_finishes": 35.0,
                "cabinetry": 20.0
            },
            "Luxury": {
                "foundation": 18.0,
                "structural": 28.0,
                "electrical": 18.0,
                "plumbing": 25.0,
                "hvac": 15.0,
                "interior_finishes": 55.0,
                "cabinetry": 40.0
            },
            "Ultra-Luxury": {
                "foundation": 22.0,
                "structural": 35.0,
                "electrical": 28.0,
                "plumbing": 40.0,
                "hvac": 24.0,
                "interior_finishes": 90.0,
                "cabinetry": 75.0
            }
        }
        
        if tier:
            return benchmarks.get(tier, {})
        return benchmarks
    
    def generate_visualization_data(self, estimation_results):
        """Generate data formatted for visualization tools."""
        if not estimation_results or 'summary' not in estimation_results:
            return {}
        
        # Prepare data for pie chart of category breakdown
        category_breakdown = []
        if 'cost_breakdown' in estimation_results['summary']:
            for category, cost in estimation_results['summary']['cost_breakdown'].items():
                percentage = 0
                if 'percentage_breakdown' in estimation_results['summary']:
                    percentage = estimation_results['summary']['percentage_breakdown'].get(category, 0)
                    
                category_breakdown.append({
                    'category': category.replace('_', ' ').title(),
                    'cost': cost,
                    'percentage': round(percentage, 1)
                })
        
        # Prepare data for comparison with industry benchmarks
        tier = estimation_results['project'].get('tier', 'Luxury')
        square_footage = estimation_results['project'].get('square_footage', 0)
        benchmarks = self.get_benchmark_data(tier)
        comparison_data = []
        
        for category, cost in estimation_results['summary'].get('cost_breakdown', {}).items():
            benchmark = benchmarks.get(category, 0)
            per_sqft = cost / square_footage if square_footage > 0 else 0
            
            comparison_data.append({
                'category': category.replace('_', ' ').title(),
                'actual': round(per_sqft, 2),
                'benchmark': benchmark,
                'difference': round(per_sqft - benchmark, 2),
                'percentage_diff': round(((per_sqft - benchmark) / benchmark * 100) if benchmark > 0 else 0, 1)
            })
        
        return {
            'category_breakdown': category_breakdown,
            'benchmark_comparison': comparison_data
        }

    def _calculate_cost_for_item(self, item, quantity, markup_percentage=None):
        """Calculate the cost for a specific item with the given quantity."""
        unit_cost = item.get('Cost (Mid)')
        
        # Handle NaN, None or empty cost values
        if pd.isna(unit_cost) or unit_cost is None or unit_cost == '':
            # For allowance items, default to 0 instead of NaN
            if 'allowance' in item.get('Item', '').lower():
                unit_cost = 0
            # Try to use Low cost if available
            elif item.get('Cost (Low)') and not pd.isna(item.get('Cost (Low)')):
                unit_cost = item.get('Cost (Low)')
            # Otherwise just use 0
            else:
                unit_cost = 0
        
        # Convert to float if it's a string
        if isinstance(unit_cost, str):
            try:
                unit_cost = float(unit_cost.replace('$', '').replace(',', ''))
            except ValueError:
                unit_cost = 0
                
        # Calculate total cost
        total_cost = quantity * unit_cost
        
        # Get markup percentage
        if markup_percentage is None:
            markup_percentage = item.get('Markup Percentage', 0)
            
        # Return the calculated values
        return {
            'unit_cost': unit_cost,
            'total_cost': total_cost,
            'markup': markup_percentage
        }

# Extension to src/core/estimation_engine.py

class EnhancedEstimationEngine(EstimationEngine):
    """Extended estimation engine that supports room-level and trade-level customization"""
    
    def __init__(self, config_path='config/settings.json'):
        """Initialize the enhanced estimation engine"""
        super().__init__(config_path)
        self.room_registry = {}  # Store room estimator references
        
    def estimate_detailed_project(self, enhanced_project_data):
        """
        Run estimation for a project with room-level and trade-level customization
        
        Args:
            enhanced_project_data (dict): Project data with rooms and trade-specific configurations
            
        Returns:
            dict: Estimation results with detailed breakdown
        """
        # Initialize logger
        logger.info(f"Starting detailed estimation for project: {enhanced_project_data.get('project_name', 'Unnamed')}")
        
        # Store the current project data for reference
        self.current_project_data = enhanced_project_data.copy()
        
        # Clear caches before new estimation
        self._electrical_cache = {}
        self._unmatched_electrical = []
        self._prefiltered_catalogs = {}
        self._match_cache = {}
        
        # Extract basic project info
        square_footage = enhanced_project_data.get('square_footage', 0)
        global_tier = enhanced_project_data.get('global_tier') or enhanced_project_data.get('tier', 'Luxury')
        
        # Initialize results structure
        results = {
            'project': enhanced_project_data.copy(),
            'categories': {},
            'rooms': {},
            'summary': {
                'cost_breakdown': {},
                'room_breakdown': {},
                'warnings': [],
                'metadata': {
                    'estimation_date': datetime.now().isoformat(),
                    'catalog_version': getattr(self.catalog, 'version', 'unknown'),
                    'catalog_item_count': len(self.catalog) if self.catalog is not None else 0
                }
            },
            'total_cost': 0
        }
        
        # Process global estimation first (for baseline)
        logger.info("Calculating global estimation baseline")
        basic_project_data = {
            'square_footage': square_footage,
            'tier': global_tier
        }
        
        # Add any other global parameters that might be needed by estimators
        for key, value in enhanced_project_data.items():
            if key not in ['rooms', 'trades', 'global_tier', 'project_name', 'construction_type']:
                basic_project_data[key] = value
        
        global_estimate = self.estimate_project(basic_project_data)
        
        # Extract global category costs for reference
        global_category_costs = {}
        for category, data in global_estimate.get('categories', {}).items():
            if data.get('status') == 'success':
                global_category_costs[category] = data.get('total_cost', 0)
        
        # Process room-specific estimations
        rooms_data = enhanced_project_data.get('rooms', {})
        trades_data = enhanced_project_data.get('trades', {})
        
        total_cost = 0
        category_costs = {}
        room_costs = {}
        
        # Process each room
        for room_id, room in rooms_data.items():
            logger.info(f"Processing room: {room.get('name')}")
            room_estimate = self._estimate_room(
                room, 
                global_tier, 
                trades_data, 
                global_category_costs
            )
            
            results['rooms'][room_id] = room_estimate
            room_costs[room_id] = room_estimate.get('total_cost', 0)
            total_cost += room_estimate.get('total_cost', 0)
            
            # Aggregate category costs
            for category, cost in room_estimate.get('category_costs', {}).items():
                if category in category_costs:
                    category_costs[category] += cost
                else:
                    category_costs[category] = cost
        
        # Process non-room categories (those that aren't associated with specific rooms)
        non_room_categories = self._get_non_room_categories()
        for category in non_room_categories:
            if category in global_estimate.get('categories', {}):
                results['categories'][category] = global_estimate['categories'][category]
                if global_estimate['categories'][category].get('status') == 'success':
                    cost = global_estimate['categories'][category].get('total_cost', 0)
                    category_costs[category] = cost
                    total_cost += cost
        
        # Add summary data
        results['summary']['cost_breakdown'] = category_costs
        results['summary']['room_breakdown'] = room_costs
        results['total_cost'] = total_cost
        
        # Add percentage breakdown
        if total_cost > 0:
            results['summary']['percentage_breakdown'] = {
                category: (cost / total_cost) * 100 
                for category, cost in category_costs.items()
            }
        
        # Clear the match cache after estimation
        self._match_cache = {}
        
        return results
    
    def _estimate_room(self, room, global_tier, trades_data, global_category_costs):
        """
        Estimate costs for a specific room
        
        Args:
            room (dict): Room data including type, size, and tier
            global_tier (str): Global project tier
            trades_data (dict): Global trade tier overrides
            global_category_costs (dict): Global category costs for reference
            
        Returns:
            dict: Room estimation results
        """
        # Determine effective room tier
        room_tier = room.get('tier', global_tier)
        room_sf = room.get('square_footage', 0)
        room_type = room.get('type', 'generic')
        
        # Initialize room result
        room_result = {
            'name': room.get('name', 'Unnamed Room'),
            'type': room_type,
            'square_footage': room_sf,
            'tier': room_tier,
            'categories': {},
            'category_costs': {},
            'total_cost': 0,
            'warnings': []
        }
        
        # Determine which categories apply to this room type
        applicable_categories = self._get_room_applicable_categories(room_type)
        
        # Calculate room-specific allocation factors
        # This determines how much of the total house's category quantities
        # should be allocated to this specific room
        allocation_factors = self._calculate_room_allocation_factors(
            room_type, 
            room_sf, 
            self.current_project_data.get('square_footage', 0)
        )
        
        # Process each applicable category
        for category in applicable_categories:
            # Skip if category is not implemented
            if category not in self.estimators or self.estimators[category] is None:
                continue
                
            # Get estimator instance
            estimator = self.estimators[category]
            
            # Determine category tier (room trade > global trade > room > global)
            category_tier = self._determine_category_tier(
                category, 
                room.get('trades', {}), 
                trades_data, 
                room_tier, 
                global_tier
            )
            
            try:
                # Create category-specific project data
                category_project_data = {
                    'square_footage': room_sf,
                    'tier': category_tier,
                    'room_type': room_type,
                    'is_room_calculation': True,
                    'allocation_factor': allocation_factors.get(category, 1.0)
                }
                
                # Add room-specific parameters that might be needed
                if room_type == 'kitchen':
                    category_project_data['is_kitchen'] = True
                elif room_type.endswith('bath'):
                    category_project_data['is_bathroom'] = True
                    if room_type == 'primary_bath':
                        category_project_data['is_primary_bath'] = True
                    elif room_type == 'secondary_bath':
                        category_project_data['is_secondary_bath'] = True
                
                # Calculate quantities for this room and category
                quantities = estimator.calculate_quantities(
                    **category_project_data
                )
                
                # Skip if no quantities were calculated
                if not quantities:
                    continue
                
                # Match with catalog costs
                costed_items = self._apply_costs(category, quantities)
                
                # Calculate category total
                category_cost = sum(item.get('total_cost', 0) for item in costed_items)
                
                # Store category results
                room_result['categories'][category] = {
                    'status': 'success',
                    'quantities': quantities,
                    'costed_items': costed_items,
                    'total_cost': category_cost,
                    'tier': category_tier
                }
                
                room_result['category_costs'][category] = category_cost
                room_result['total_cost'] += category_cost
                
            except Exception as e:
                logger.error(f"Error estimating {category} for room {room.get('name')}: {str(e)}", exc_info=True)
                room_result['categories'][category] = {
                    'status': 'error',
                    'message': str(e)
                }
                room_result['warnings'].append(f"Error in category '{category}': {str(e)}")
        
        return room_result
    
    def _determine_category_tier(self, category, room_trades, global_trades, room_tier, global_tier):
        """
        Determine the effective tier for a specific category in a room
        Priority: Room-trade > Global-trade > Room > Global
        """
        # Check for room-specific trade tier
        if category in room_trades and 'tier' in room_trades[category]:
            return room_trades[category]['tier']
            
        # Check for global trade tier
        if category in global_trades:
            return global_trades[category]
            
        # Use room tier
        return room_tier
    
    def _get_room_applicable_categories(self, room_type):
        """Determine which categories apply to a specific room type"""
        # Base categories that apply to all rooms
        base_categories = [
            'drywall_interior', 
            'painting_coatings', 
            'electrical',
            'thermal_fire_suppression',
            'finish_carpentry'
        ]
        
        # Add room-specific categories
        if room_type in ['primary_bath', 'secondary_bath', 'powder_room']:
            return base_categories + ['plumbing', 'tile', 'cabinetry', 'countertops']
        elif room_type == 'kitchen':
            return base_categories + ['plumbing', 'cabinetry', 'countertops', 'tile']
        elif room_type in ['utility', 'laundry']:
            return base_categories + ['plumbing', 'cabinetry']
        else:
            # For bedrooms, living areas, etc.
            return base_categories
    
    def _get_non_room_categories(self):
        """Get categories that are not associated with specific rooms"""
        return [
            'foundation',
            'structural',
            'hvac',  # Could be room-specific but typically whole-house
            'roofing',
            'windows_doors',
            'landscape_hardscape',
            'cleaning',
            'preparations_preliminaries',
            'specialty'
        ]
    
    def _calculate_room_allocation_factors(self, room_type, room_sf, total_sf):
        """
        Calculate allocation factors for different categories based on room type and size
        
        Returns a dictionary mapping category names to allocation factors (0.0-1.0)
        """
        # Base allocation factor is proportional to square footage
        base_factor = room_sf / total_sf if total_sf > 0 else 0
        
        # Initialize with default factors
        factors = {
            'electrical': base_factor,
            'drywall_interior': base_factor,
            'painting_coatings': base_factor,
            'thermal_fire_suppression': base_factor,
            'finish_carpentry': base_factor
        }
        
        # Adjust factors based on room type
        if room_type in ['primary_bath', 'secondary_bath']:
            # Bathrooms typically have more electrical, plumbing fixtures per SF
            factors['electrical'] = base_factor * 1.5
            factors['plumbing'] = base_factor * 3.0
            factors['tile'] = base_factor * 2.5
        elif room_type == 'kitchen':
            # Kitchens have more electrical, cabinetry per SF
            factors['electrical'] = base_factor * 2.0
            factors['cabinetry'] = base_factor * 3.0
            factors['countertops'] = base_factor * 2.5
        
        return factors
        
    def _resolve_effective_tier(self, context):
        """
        Resolve the effective tier for a given context based on tier priority
        
        Args:
            context (dict): Contains all tier-related context:
                - room_id: ID of the current room (optional)
                - category: Category being estimated
                - global_tier: Project-level tier
                - room_tier: Room-specific tier (optional)
                - trade_tiers: Global trade tier overrides (optional)
                - room_trade_tiers: Room-specific trade tier overrides (optional)
        
        Returns:
            str: The effective tier to use ('Premium', 'Luxury', or 'Ultra-Luxury')
        """
        # Priority order (highest to lowest):
        # 1. Room-specific trade tier
        # 2. Global trade tier
        # 3. Room-specific tier
        # 4. Global tier
        
        category = context.get('category')
        global_tier = context.get('global_tier', 'Luxury')
        
        # Check if we're in a room-specific calculation
        if context.get('room_id'):
            room_tier = context.get('room_tier')
            room_trade_tiers = context.get('room_trade_tiers', {})
            
            # 1. Check for room-specific trade tier
            if category in room_trade_tiers and 'tier' in room_trade_tiers[category]:
                return room_trade_tiers[category]['tier']
        
        # 2. Check for global trade tier
        trade_tiers = context.get('trade_tiers', {})
        if category in trade_tiers:
            return trade_tiers[category]
        
        # 3. Check for room-specific tier (if in room context)
        if context.get('room_id') and context.get('room_tier'):
            return context.get('room_tier')
        
        # 4. Fall back to global tier
        return global_tier
    
    def _modify_quantities_for_tier(self, quantities, base_tier, target_tier):
        """
        Adjust quantities based on tier differences
        
        Args:
            quantities (dict): Dictionary of calculated quantities
            base_tier (str): Tier used for initial calculations
            target_tier (str): Tier to adjust quantities to
        
        Returns:
            dict: Adjusted quantities
        """
        if base_tier == target_tier:
            return quantities  # No adjustment needed
        
        # Define tier adjustment factors
        tier_factors = {
            # Format: (from_tier, to_tier): {category: {quantity: factor}}
            ('Premium', 'Luxury'): {
                'electrical': {
                    'recessed_lights': 1.25,
                    'pendants': 1.5,
                    'chandeliers': 1.3,
                    'total_outlets_switches': 1.2
                },
                'plumbing': {
                    'primary_shower_valves': 1.5,  # More shower heads in luxury
                    'tankless_water_heaters': 1.5
                },
                'cabinetry': {
                    'kitchen_base_cabinets_lf': 1.2,
                    'kitchen_island_lf': 1.5
                }
            },
            ('Premium', 'Ultra-Luxury'): {
                'electrical': {
                    'recessed_lights': 1.5,
                    'pendants': 2.0,
                    'chandeliers': 2.0,
                    'total_outlets_switches': 1.4
                },
                'plumbing': {
                    'primary_shower_valves': 2.0,
                    'tankless_water_heaters': 2.0
                },
                'cabinetry': {
                    'kitchen_base_cabinets_lf': 1.4,
                    'kitchen_island_lf': 2.0
                }
            },
            ('Luxury', 'Ultra-Luxury'): {
                'electrical': {
                    'recessed_lights': 1.2,
                    'pendants': 1.33,
                    'chandeliers': 1.5,
                    'total_outlets_switches': 1.15
                },
                'plumbing': {
                    'primary_shower_valves': 1.33,
                    'tankless_water_heaters': 1.33
                },
                'cabinetry': {
                    'kitchen_base_cabinets_lf': 1.15,
                    'kitchen_island_lf': 1.33
                }
            }
        }
        
        # Also define the reverse relationships
        for key, adjustments in list(tier_factors.items()):
            from_tier, to_tier = key
            tier_factors[(to_tier, from_tier)] = {
                category: {quantity: 1/factor for quantity, factor in quantities.items()}
                for category, quantities in adjustments.items()
            }
        
        # Apply the adjustments
        adjusted_quantities = quantities.copy()
        adjustment_key = (base_tier, target_tier)
        
        if adjustment_key in tier_factors:
            category_adjustments = tier_factors[adjustment_key].get(self.current_category, {})
            for quantity_name, factor in category_adjustments.items():
                if quantity_name in adjusted_quantities:
                    adjusted_quantities[quantity_name] = adjusted_quantities[quantity_name] * factor
        
        return adjusted_quantities