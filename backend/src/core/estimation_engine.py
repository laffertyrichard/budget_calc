# src/core/estimation_engine.py (key fixes)

import logging
import importlib
import os
from typing import Dict, Any, Union, List, Optional
from datetime import datetime
from src.core.data_loader import DataLoader
from src.utils.catalog_mapper import CatalogMapper

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
        
        # Pre-filter electrical catalog for optimization if needed
        try:
            if 'electrical' in self.estimators and self.estimators['electrical'] and self.catalog_mapper:
                self._prefilter_electrical_catalog()
        except Exception as e:
            logger.warning(f"Error pre-filtering electrical catalog: {str(e)}")
        
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
                # Special handling for electrical category
                if category == 'electrical':
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
                        try:
                            costed_items = self._apply_costs_electrical(quantities)
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
                        except Exception as e:
                            # If an error occurs in the specialized flow, fall back to standard flow
                            logger.warning(f"Error in specialized electrical flow: {str(e)}, falling back to standard flow")
                            costed_items = self._apply_costs(category, quantities)
                            
                            category_cost = sum(item.get('total_cost', 0) for item in costed_items)
                            total_cost += category_cost
                            category_costs[category] = category_cost
                            
                            results['categories'][category] = {
                                'status': 'success',
                                'quantities': quantities,
                                'costed_items': costed_items,
                                'total_cost': category_cost,
                                'note': 'Used standard estimation flow due to error in specialized flow'
                            }
                    else:
                        results['categories'][category] = {
                            'status': 'no_quantities',
                            'message': f"No quantities calculated for {category}"
                        }
                        results['summary']['warnings'].append(f"Category '{category}' produced no quantities")
                else:
                    # Regular handling for non-electrical categories
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
        
        # Add summary data
        results['summary']['cost_breakdown'] = category_costs
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
        """Apply costs from catalog to calculated quantities with enhanced matching and caching"""
        if not quantities:
            logger.warning(f"No quantities provided for category: {category}")
            return []
            
        costed_items = []
        
        # Use enhanced mapping if available
        if self.catalog_mapper:
            # Process each quantity
            for quantity_name, quantity_value in quantities.items():
                # Skip non-quantity keys like 'units'
                if quantity_name == 'units' or not quantity_value:
                    continue
                
                # Extract unit if provided
                unit = self._extract_quantity_unit(quantities, quantity_name)
                
                # Get construction tier
                tier = self.current_project_data.get('tier', 'Luxury')
                
                # Use cached matching to improve performance
                cache_key = f"{category}:{quantity_name}:{tier}"
                
                if cache_key in self._match_cache:
                    matching_items = self._match_cache[cache_key]
                else:
                    # Get matching catalog items
                    matching_items = self.catalog_mapper.get_catalog_items_for_quantity(
                        category, quantity_name, tier
                    )
                    # Cache the result for future use
                    self._match_cache[cache_key] = matching_items
                
                if not matching_items:
                    # Log that no match was found
                    logger.warning(f"No catalog match found for {category}.{quantity_name}")
                    continue
                
                # Use the first (best) match
                item = matching_items[0]
                
                # Check unit compatibility
                catalog_unit = item.get('Unit', 'EA')
                conversion_factor = None
                
                if unit and catalog_unit:
                    conversion_factor = self.catalog_mapper.get_unit_conversion_factor(unit, catalog_unit)
                
                if conversion_factor is None:
                    # Units are incompatible or not specified
                    conversion_factor = 1.0
                    note = f"WARNING: Possible unit mismatch (guessed {unit} to {catalog_unit})"
                else:
                    # Units are compatible
                    if unit == catalog_unit:
                        note = "Direct match"
                    else:
                        note = f"Converted units ({unit} to {catalog_unit})"
                
                # Apply conversion factor
                adjusted_quantity = quantity_value * conversion_factor
                
                # Calculate cost
                unit_cost = item.get('Cost(Mid)', 0)
                total_cost = unit_cost * adjusted_quantity
                
                # Add to costed items
                costed_items.append({
                    'item_id': item.get('ID', ''),
                    'item_name': item.get('Item', ''),
                    'category': item.get('Category', ''),
                    'subcategory': item.get('Subcategory', ''),
                    'quantity': adjusted_quantity,
                    'unit': catalog_unit,
                    'unit_cost': unit_cost,
                    'total_cost': total_cost,
                    'markup': item.get('Markup Percentage', 0),
                    'note': note,
                    'quality_tier': item.get('QualityTier', ''),
                    'original_quantity_name': quantity_name,
                    'original_quantity_value': quantity_value,
                    'original_unit': unit
                })
                logger.info(f"Costed item: {costed_items[-1]}")
                print(f"Costed item: {costed_items[-1]}")
        else:
            # Fall back to original matching method if enhanced catalog not available
            # Pre-filter the catalog for this category to avoid repeated filtering
            category_items = self.data_loader.get_category_items(category)
            
            for quantity_name, quantity_value in quantities.items():
                if quantity_name == 'units' or not quantity_value:
                    continue
                    
                # Get matching items using the original method
                matching_items = category_items[
                    category_items['Item'].str.contains(quantity_name, case=False, na=False)
                ]
                
                if matching_items.empty:
                    # No match found, use first item from category as fallback
                    if not category_items.empty:
                        item = category_items.iloc[0]
                        costed_items.append({
                            'item_id': item.get('ID', ''),
                            'item_name': item.get('Item', 'Unknown Item'),
                            'category': item.get('Category', ''),
                            'quantity': quantity_value,
                            'unit': item.get('Unit', 'EA'),
                            'unit_cost': float(item.get('Cost(Mid)', 0)),
                            'total_cost': float(item.get('Cost(Mid)', 0)) * quantity_value,
                            'markup': float(item.get('Markup Percentage', 0)),
                            'note': "Approximate cost - item matched by category",
                            'original_quantity_name': quantity_name,
                            'original_quantity_value': quantity_value
                        })
                        logger.info(f"Costed item (fallback): {costed_items[-1]}")
                        print(f"Costed item (fallback): {costed_items[-1]}")
                else:
                    # For each matching item, add it to costed items
                    for _, item in matching_items.iterrows():
                        costed_items.append({
                            'item_id': item.get('ID', ''),
                            'item_name': item.get('Item', 'Unknown Item'),
                            'category': item.get('Category', ''),
                            'quantity': quantity_value,
                            'unit': item.get('Unit', 'EA'),
                            'unit_cost': float(item.get('Cost(Mid)', 0)),
                            'total_cost': float(item.get('Cost(Mid)', 0)) * quantity_value,
                            'markup': float(item.get('Markup Percentage', 0)),
                            'note': "Direct match found",
                            'original_quantity_name': quantity_name,
                            'original_quantity_value': quantity_value
                        })
                        logger.info(f"Costed item (direct match): {costed_items[-1]}")
                        print(f"Costed item (direct match): {costed_items[-1]}")
        
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
        """Apply costs from catalog to electrical quantities with enhanced matching"""
        if not quantities:
            return []
            
        costed_items = []
        
        # Process each quantity
        for quantity_name, quantity_value in quantities.items():
            # Skip non-quantity keys like 'units'
            if quantity_name == 'units' or not quantity_value:
                continue
            
            # Extract unit if provided
            unit = self._extract_quantity_unit(quantities, quantity_name)
            
            # Get construction tier
            tier = self.current_project_data.get('tier', 'Luxury')
            
            # Use cached matching to improve performance
            cache_key = f"electrical:{quantity_name}:{tier}"
            
            matching_items = []
            if cache_key in self._match_cache:
                matching_items = self._match_cache[cache_key]
            else:
                try:
                    # Try specialized electrical matching first if available
                    if self.catalog_mapper and hasattr(self.catalog_mapper, 'get_electrical_catalog_items'):
                        matching_items = self.catalog_mapper.get_electrical_catalog_items(quantity_name, tier)
                    else:
                        # Fallback to standard matching
                        matching_items = self.catalog_mapper.get_catalog_items_for_quantity(
                            "electrical", quantity_name, tier
                        ) if self.catalog_mapper else []
                    
                    # Cache the results
                    self._match_cache[cache_key] = matching_items
                except Exception as e:
                    logger.warning(f"Error matching electrical item {quantity_name}: {str(e)}")
                    matching_items = []
            
            # If no match found, implement fallback strategy
            if not matching_items:
                try:
                    # Fallback 1: Try with generic quality for this tier
                    generic_item = None
                    if self.catalog_mapper and hasattr(self.catalog_mapper, 'get_electrical_generic_item'):
                        generic_item = self.catalog_mapper.get_electrical_generic_item(quantity_name, tier)
                    
                    if generic_item:
                        matching_items = [generic_item]
                    else:
                        # Fallback 2: Use adjacent tier if still no matches
                        adjacent_tiers = {
                            "Premium": ["Luxury"],
                            "Luxury": ["Premium", "Ultra-Luxury"],
                            "Ultra-Luxury": ["Luxury"]
                        }
                        
                        for alt_tier in adjacent_tiers.get(tier, []):
                            alt_cache_key = f"electrical:{quantity_name}:{alt_tier}"
                            
                            alt_matches = []
                            if alt_cache_key in self._match_cache:
                                alt_matches = self._match_cache[alt_cache_key]
                            elif self.catalog_mapper:
                                if hasattr(self.catalog_mapper, 'get_electrical_catalog_items'):
                                    alt_matches = self.catalog_mapper.get_electrical_catalog_items(quantity_name, alt_tier)
                                else:
                                    alt_matches = self.catalog_mapper.get_catalog_items_for_quantity(
                                        "electrical", quantity_name, alt_tier
                                    )
                                self._match_cache[alt_cache_key] = alt_matches
                                
                            if alt_matches:
                                matching_items = alt_matches
                                break
                        
                        # Fallback 3: Use average cost for component category
                        if not matching_items and self.catalog_mapper and hasattr(self.catalog_mapper, 'get_avg_electrical_cost'):
                            avg_item = self.catalog_mapper.get_avg_electrical_cost(quantity_name)
                            if avg_item:
                                matching_items = [avg_item]
                except Exception as e:
                    logger.warning(f"Error in fallback matching for {quantity_name}: {str(e)}")
            
            # Process the matches
            if matching_items:
                try:
                    item = matching_items[0]
                    
                    # Check unit compatibility
                    catalog_unit = item.get('Unit', 'EA')
                    conversion_factor = None
                    
                    if unit and catalog_unit:
                        if self.catalog_mapper and hasattr(self.catalog_mapper, 'get_unit_conversion_factor'):
                            conversion_factor = self.catalog_mapper.get_unit_conversion_factor(unit, catalog_unit)
                        else:
                            conversion_factor = self._get_unit_conversion_factor(unit, catalog_unit)
                    
                    if conversion_factor is None:
                        # Units are incompatible or not specified
                        conversion_factor = 1.0
                        note = f"WARNING: Possible unit mismatch (guessed {unit} to {catalog_unit})"
                    else:
                        # Units are compatible
                        if unit == catalog_unit:
                            note = "Direct match"
                        else:
                            note = f"Converted units ({unit} to {catalog_unit})"
                    
                    # Apply conversion factor
                    adjusted_quantity = quantity_value * conversion_factor
                    
                    # Calculate cost
                    unit_cost = item.get('Cost(Mid)', 0)
                    total_cost = unit_cost * adjusted_quantity
                    
                    # Add to costed items
                    costed_items.append({
                        'item_id': item.get('ID', ''),
                        'item_name': item.get('Item', ''),
                        'category': item.get('Category', ''),
                        'subcategory': item.get('Subcategory', ''),
                        'quantity': adjusted_quantity,
                        'unit': catalog_unit,
                        'unit_cost': unit_cost,
                        'total_cost': total_cost,
                        'markup': item.get('Markup Percentage', 0),
                        'note': note,
                        'quality_tier': item.get('QualityTier', ''),
                        'original_quantity_name': quantity_name,
                        'original_quantity_value': quantity_value,
                        'original_unit': unit
                    })
                except Exception as e:
                    logger.warning(f"Error processing matches for {quantity_name}: {str(e)}")
            else:
                # Record unmatched items for reporting
                self._unmatched_electrical.append(quantity_name)
                
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