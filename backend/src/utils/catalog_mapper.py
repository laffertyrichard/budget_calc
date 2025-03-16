# src/utils/catalog_mapper.py

import pandas as pd
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CatalogMapper:
    """System to map between estimator quantities and catalog items"""
    
    def __init__(self, catalog_path, mapping_config_path=None):
        """
        Initialize with catalog path and optional mapping configuration
        
        Args:
            catalog_path: Path to the enhanced catalog CSV
            mapping_config_path: Path to JSON mapping configuration (created if not exists)
        """
        self.catalog_path = catalog_path
        self.mapping_config_path = mapping_config_path or os.path.join(
            os.path.dirname(catalog_path), 'catalog_mappings.json'
        )
        
        # Load catalog
        try:
            self.catalog = pd.read_csv(catalog_path)
            logger.info(f"Loaded catalog with {len(self.catalog)} items")
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            self.catalog = pd.DataFrame()
        
        # Load or create mapping configuration
        self.mapping_config = self._load_mapping_config()
    
    def _load_mapping_config(self):
        """Load or create mapping configuration"""
        if os.path.exists(self.mapping_config_path):
            try:
                with open(self.mapping_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading mapping config: {str(e)}")
                return self._create_default_mapping_config()
        else:
            return self._create_default_mapping_config()
    
    def _create_default_mapping_config(self):
        """Create default mapping configuration"""
        # Basic structure
        config = {
            "version": "1.0",
            "unit_conversions": {
                "SF": {
                    "SY": 1/9,
                    "SQFT": 1
                },
                "LF": {
                    "FT": 1
                },
                "CY": {
                    "CF": 27
                },
                "EA": {
                    "EACH": 1
                }
            },
            "estimator_modules": {}
        }
        
        # Only create mappings for modules we find in the catalog
        if not self.catalog.empty and 'EstimatorModule' in self.catalog.columns:
            modules = self.catalog['EstimatorModule'].dropna().unique()
            
            for module in modules:
                if not module:
                    continue
                    
                config["estimator_modules"][module] = {
                    "quantity_mappings": {}
                }
        
        # Save the config
        try:
            with open(self.mapping_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created default mapping config at {self.mapping_config_path}")
        except Exception as e:
            logger.error(f"Error creating mapping config: {str(e)}")
        
        return config
    
    def get_catalog_items_for_quantity(self, module_name, quantity_name, construction_tier="Luxury"):
        """
        Get matching catalog items for a specific estimator quantity
        
        Args:
            module_name: Estimator module name (e.g., 'foundation', 'electrical')
            quantity_name: Name of the quantity (e.g., 'slab_concrete_cy', 'recessed_lights')
            construction_tier: Construction tier (Premium, Luxury, Ultra-Luxury)
            
        Returns:
            List of matching catalog items
        """
        if self.catalog.empty:
            return []
            
        # Check if we have explicit mappings
        mappings = self._get_quantity_mappings(module_name, quantity_name)
        
        # If we have explicit item IDs for this quantity and tier, use those
        if mappings and "tier_item_ids" in mappings and construction_tier in mappings["tier_item_ids"]:
            item_ids = mappings["tier_item_ids"][construction_tier]
            matches = self.catalog[self.catalog['ID'].isin(item_ids)]
            if not matches.empty:
                return matches.to_dict('records')
        
        # Try to match by search terms
        if mappings and "search_terms" in mappings:
            search_terms = mappings["search_terms"]
            module_items = self.catalog[self.catalog['EstimatorModule'] == module_name]
            
            # Filter by construction tier if specified
            if construction_tier:
                module_items = module_items[module_items['ConstructionTier'] == construction_tier]
            
            # Create search pattern
            search_pattern = '|'.join(search_terms)
            matches = module_items[module_items['SearchItem'].str.contains(
                search_pattern, case=False, regex=True, na=False
            )]
            
            if not matches.empty:
                return matches.to_dict('records')
        
        # If no explicit mapping or search terms didn't work, try to derive from quantity name
        derived_search_terms = self._derive_search_terms_from_quantity(quantity_name)
        
        # Get items for the module
        module_items = self.catalog[self.catalog['EstimatorModule'] == module_name]
        
        # Filter by construction tier if specified
        if construction_tier:
            module_items = module_items[module_items['ConstructionTier'] == construction_tier]
        
        # Empty result if no module items
        if module_items.empty:
            return []
        
        # Create search pattern
        search_pattern = '|'.join(derived_search_terms)
        matches = module_items[module_items['SearchItem'].str.contains(
            search_pattern, case=False, regex=True, na=False
        )]
        
        # If still no matches, return best guess based on category
        if matches.empty:
            # Try to guess category from quantity name
            category = self._guess_category_from_quantity(quantity_name)
            if category:
                category_items = self.catalog[self.catalog['Category'].str.contains(
                    category, case=False, na=False
                )]
                
                # Filter by construction tier if specified
                if construction_tier:
                    category_items = category_items[category_items['ConstructionTier'] == construction_tier]
                
                if not category_items.empty:
                    return category_items.head(3).to_dict('records')
            
            # Last resort: return any items from the module
            return module_items.head(3).to_dict('records')
        
        return matches.to_dict('records')
    
    def _get_quantity_mappings(self, module_name, quantity_name):
        """Get mapping configuration for a specific quantity"""
        if (module_name in self.mapping_config.get("estimator_modules", {}) and
            quantity_name in self.mapping_config["estimator_modules"][module_name].get("quantity_mappings", {})):
            return self.mapping_config["estimator_modules"][module_name]["quantity_mappings"][quantity_name]
        return None
    
    def _derive_search_terms_from_quantity(self, quantity_name):
        """Derive search terms from quantity name"""
        # Split by underscore and remove unit suffix if present
        parts = quantity_name.split('_')
        
        # Check for common unit suffixes
        unit_suffixes = ['sf', 'lf', 'cy', 'ea', 'count']
        if parts and any(parts[-1] == suffix for suffix in unit_suffixes):
            parts = parts[:-1]  # Remove unit suffix
        
        # Process parts to get search terms
        search_terms = []
        
        for part in parts:
            # Skip common prefixes
            if part in ['total', 'simplified']:
                continue
                
            # Add the part as a search term
            search_terms.append(part)
            
            # Handle common pluralization
            if part.endswith('s') and len(part) > 3:
                search_terms.append(part[:-1])  # Singular form
            else:
                search_terms.append(part + 's')  # Plural form
        
        return search_terms
    
    def _guess_category_from_quantity(self, quantity_name):
        """Guess catalog category from quantity name"""
        # Map common terms to categories
        term_to_category = {
            'concrete': 'Concrete',
            'slab': 'Concrete',
            'footing': 'Foundation',
            'foundation': 'Foundation',
            'framing': 'Framing',
            'lumber': 'Lumber',
            'door': 'Doors',
            'window': 'Windows',
            'outlet': 'Electrical',
            'switch': 'Electrical',
            'light': 'Lighting',
            'fixture': 'Lighting',
            'paint': 'Paint',
            'sink': 'Plumbing',
            'toilet': 'Plumbing',
            'shower': 'Plumbing',
            'hvac': 'HVAC',
            'duct': 'HVAC',
            'cabinet': 'Cabinets',
            'countertop': 'Countertops',
            'tile': 'Tile',
            'flooring': 'Flooring',
            'insulation': 'Insulation',
            'drywall': 'Drywall',
            'roof': 'Roofing'
        }
        
        # Check terms in the quantity name
        for term, category in term_to_category.items():
            if term in quantity_name.lower():
                return category
                
        return None
    
    def add_quantity_mapping(self, module_name, quantity_name, mapping_data):
        """
        Add or update mapping for a quantity
        
        Args:
            module_name: Estimator module name
            quantity_name: Quantity name
            mapping_data: Dictionary with mapping data (search_terms, tier_item_ids, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure module exists in config
        if module_name not in self.mapping_config.get("estimator_modules", {}):
            self.mapping_config.setdefault("estimator_modules", {})[module_name] = {
                "quantity_mappings": {}
            }
            
        # Update mapping
        self.mapping_config["estimator_modules"][module_name].setdefault(
            "quantity_mappings", {}
        )[quantity_name] = mapping_data
        
        # Save updated config
        try:
            with open(self.mapping_config_path, 'w') as f:
                json.dump(self.mapping_config, f, indent=2)
            logger.info(f"Updated mapping for {module_name}.{quantity_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving mapping config: {str(e)}")
            return False
    
    def get_unit_conversion_factor(self, from_unit, to_unit):
        """Get conversion factor between units"""
        # If units are the same, no conversion needed
        if from_unit == to_unit:
            return 1.0
        
        # Check conversions in config
        conversions = self.mapping_config.get("unit_conversions", {})
        
        # Normalize units to uppercase
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        # Check if conversion exists
        if from_unit in conversions and to_unit in conversions[from_unit]:
            return conversions[from_unit][to_unit]
        
        # Check reverse conversion
        if to_unit in conversions and from_unit in conversions[to_unit]:
            return 1 / conversions[to_unit][from_unit]
        
        # No conversion found
        return None
    
    def generate_mapping_suggestions(self, module_name=None):
        """
        Generate mapping suggestions for quantities based on catalog analysis
        
        Args:
            module_name: Optional module name to limit suggestions
            
        Returns:
            Dictionary of suggested mappings by module and quantity
        """
        if self.catalog.empty:
            return {}
            
        # Get all modules if none specified
        modules = [module_name] if module_name else self.catalog['EstimatorModule'].dropna().unique()
        
        suggestions = {}
        
        for module in modules:
            if not module:
                continue
                
            suggestions[module] = {}
            
            # Get sample quantity names for this module (would normally come from estimator)
            sample_quantities = self._get_sample_quantities(module)
            
            for quantity_name in sample_quantities:
                # Get matches for this quantity
                matches = self.get_catalog_items_for_quantity(module, quantity_name)
                
                # Create suggestion if we found matches
                if matches:
                    suggestions[module][quantity_name] = {
                        "search_terms": self._derive_search_terms_from_quantity(quantity_name),
                        "suggested_items": [
                            {"id": item["ID"], "name": item["Item"]} 
                            for item in matches[:3]
                        ],
                        "tier_item_ids": {
                            "Premium": [item["ID"] for item in matches if item.get("ConstructionTier") == "Premium"][:1],
                            "Luxury": [item["ID"] for item in matches if item.get("ConstructionTier") == "Luxury"][:1],
                            "Ultra-Luxury": [item["ID"] for item in matches if item.get("ConstructionTier") == "Ultra-Luxury"][:1]
                        }
                    }
        
        return suggestions
    
    def _get_sample_quantities(self, module_name):
        """Get sample quantity names for a module (in a real system, these would come from the estimator)"""
        # These are just examples - in real use, we'd get these from the estimator modules
        sample_quantities_by_module = {
            "foundation": ["slab_concrete_cy", "footing_concrete_cy", "foundation_wall_cy", "foundation_waterproofing_sf"],
            "electrical": ["standard_outlets", "gfci_outlets", "recessed_lights", "chandeliers", "switches_dimmer"],
            "plumbing": ["primary_shower_valves", "primary_sinks", "primary_toilets", "tankless_water_heaters"],
            "hvac": ["tonnage", "systems", "registers", "returns"],
            "finishes": ["wall_paint_gallons", "ceiling_paint_gallons", "trim_paint_gallons"],
            "cabinetry": ["kitchen_base_cabinets_lf", "kitchen_wall_cabinets_lf", "vanity_cabinets_lf"],
            "countertops": ["kitchen_countertops_sf", "bathroom_countertops_sf"],
            "tile": ["shower_wall_tile_sf", "bathroom_floor_tile_sf", "kitchen_backsplash_sf"]
        }
        
        return sample_quantities_by_module.get(module_name, [])
    # Add these methods to the CatalogMapper class in src/utils/catalog_mapper.py

def get_electrical_catalog_items(self, quantity_name, tier):
    """Specialized method for matching electrical quantities to catalog items"""
    # Start with standard mapping approach
    matches = self.get_catalog_items_for_quantity("electrical", quantity_name, tier)
    
    # If no matches found, apply electrical-specific strategies
    if not matches:
        # Strategy 1: Try alias mapping for common electrical terms
        electrical_aliases = {
            "recessed_lights": ["can lights", "pot lights", "downlights"],
            "dimmer_switches": ["dimmers", "light controls"],
            "gfci_outlets": ["gfi outlets", "ground fault", "bathroom outlets"],
            "standard_outlets": ["receptacles", "plugs", "wall outlets"],
            "three_way_switches": ["3-way", "multiple location"],
            "chandeliers": ["hanging fixtures", "pendant lights", "ceiling fixtures"],
            "under_cabinet_lights": ["cabinet lighting", "task lighting"],
            "audio_visual_drops": ["av connections", "media outlets"],
            "security_system_components": ["security devices", "alarm components"]
        }
        
        if quantity_name in electrical_aliases:
            for alias in electrical_aliases[quantity_name]:
                # Filter catalog by electrical estimator module and alias
                alias_matches = [
                    item for item in self.catalog.to_dict('records')
                    if item.get('EstimatorModule') == "electrical" and
                    alias in str(item.get('SearchItem', '')).lower()
                ]
                
                if alias_matches:
                    return alias_matches
        
        # Strategy 2: Component type matching
        component_types = {
            "lights": ["lights", "lighting", "fixtures", "lamps"],
            "switches": ["switches", "controls", "dimmers"],
            "outlets": ["outlets", "receptacles", "plugs"],
            "panels": ["panels", "electrical boxes", "service"]
        }
        
        for component, terms in component_types.items():
            if any(comp in quantity_name for comp in terms):
                # Try to find matches based on component type
                type_matches = []
                for term in terms:
                    term_matches = [
                        item for item in self.catalog.to_dict('records')
                        if item.get('EstimatorModule') == "electrical" and
                        term in str(item.get('SearchItem', '')).lower()
                    ]
                    type_matches.extend(term_matches)
                
                if type_matches:
                    # Filter by construction tier if possible
                    tier_matches = [
                        item for item in type_matches
                        if item.get('ConstructionTier') == tier
                    ]
                    
                    if tier_matches:
                        return tier_matches
                    return type_matches
    
    return matches

def get_electrical_generic_item(self, quantity_name, tier):
    """Get a generic electrical item for a given quantity name and tier"""
    # Map quantity categories to generic catalog items
    generic_mapping = {
        "outlets": "standard electrical outlet",
        "switches": "standard wall switch",
        "lights": "standard light fixture",
        "panels": "electrical panel"
    }
    
    # Determine which category this quantity belongs to
    category = None
    for cat, terms in {
        "outlets": ["outlet", "receptacle", "plug"],
        "switches": ["switch", "dimmer", "control"],
        "lights": ["light", "fixture", "lamp", "chandelier", "pendant"],
        "panels": ["panel", "circuit", "breaker"]
    }.items():
        if any(term in quantity_name for term in terms):
            category = cat
            break
    
    if not category:
        return None
        
    # Search for generic items matching this category
    search_term = generic_mapping.get(category)
    if not search_term:
        return None
        
    # Filter catalog to find generic items
    generic_items = [
        item for item in self.catalog.to_dict('records')
        if item.get('EstimatorModule') == "electrical" and
        search_term in str(item.get('SearchItem', '')).lower() and
        item.get('ConstructionTier') == tier
    ]
    
    if generic_items:
        return generic_items[0]
    return None

def get_avg_electrical_cost(self, quantity_name):
    """Calculate average cost for a type of electrical component"""
    # Determine component category
    component_categories = {
        "outlets": ["outlet", "receptacle", "plug", "gfci", "usb"],
        "switches": ["switch", "dimmer", "control"],
        "lights": ["light", "recessed", "pendant", "chandelier"],
        "panels": ["panel", "circuit", "breaker"]
    }
    
    category = None
    for cat, terms in component_categories.items():
        if any(term in quantity_name for term in terms):
            category = cat
            break
    
    if not category:
        return None
    
    # Filter electrical items in this category
    category_items = [
        item for item in self.catalog.to_dict('records')
        if item.get('EstimatorModule') == "electrical" and
        any(term in str(item.get('SearchItem', '')).lower() for term in component_categories[category])
    ]
    
    if not category_items:
        return None
    
    # Calculate average cost
    costs = [item.get('Cost(Mid)', 0) for item in category_items]
    if not costs:
        return None
        
    avg_cost = sum(costs) / len(costs)
    
    # Create a generic item with average cost
    return {
        "ID": f"AVG-{category.upper()}",
        "Item": f"Average {category} component",
        "Category": "Electrical",
        "Unit": "EA",
        "Cost(Mid)": avg_cost,
        "EstimatorModule": "electrical",
        "QualityTier": "Standard",
        "ConstructionTier": "Luxury"
    }
    
def main():
    """Main function when run as a script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage catalog-estimator mappings')
    parser.add_argument('catalog', help='Path to enhanced catalog CSV')
    parser.add_argument('--config', help='Path to mapping configuration JSON')
    parser.add_argument('--suggest', action='store_true', help='Generate mapping suggestions')
    parser.add_argument('--module', help='Limit suggestions to specific module')
    
    args = parser.parse_args()
    
    mapper = CatalogMapper(args.catalog, args.config)
    
    if args.suggest:
        suggestions = mapper.generate_mapping_suggestions(args.module)
        print(json.dumps(suggestions, indent=2))
    else:
        print(f"Loaded catalog with {len(mapper.catalog)} items")
        print(f"Mapping configuration: {mapper.mapping_config_path}")
        
        # Example usage
        if args.module:
            sample_quantities = mapper._get_sample_quantities(args.module)
            if sample_quantities:
                print(f"\nExample mappings for {args.module}:")
                for quantity in sample_quantities[:3]:  # Show first 3 examples
                    items = mapper.get_catalog_items_for_quantity(args.module, quantity)
                    if items:
                        print(f"\n  {quantity}:")
                        for item in items[:2]:  # Show first 2 matching items
                            print(f"    - {item['ID']}: {item['Item']} (${item.get('Cost(Mid)', 0):.2f} {item.get('Unit', '')})")
                    else:
                        print(f"\n  {quantity}: No matches found")

if __name__ == "__main__":
    main()