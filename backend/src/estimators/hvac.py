import math
import logging

logger = logging.getLogger(__name__)

class HvacEstimator:
    """Handles HVAC quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate HVAC quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate system sizing
        results.update(self._calculate_system_sizing(square_footage, tier))
        
        # Calculate distribution components
        results.update(self._calculate_distribution(square_footage, tier))
        
        return results
        
    def _calculate_system_sizing(self, square_footage, tier):
        """Calculate HVAC system sizing"""
        # Tonnage calculation based on square footage and tier
        tonnage_factors = {
            "Premium": 550,    # 1 ton per 550 sq ft
            "Luxury": 500,     # 1 ton per 500 sq ft
            "Ultra-Luxury": 450  # 1 ton per 450 sq ft
        }
        
        # System count calculation
        system_factors = {
            "Premium": 2000,   # New system every 2000 sq ft
            "Luxury": 1800,    # New system every 1800 sq ft
            "Ultra-Luxury": 1600  # New system every 1600 sq ft
        }
        
        # Zones per system vary by tier
        zones_per_system = {
            "Premium": 2.5,    # Average of 2-3 zones
            "Luxury": 3.5,     # Average of 3-4 zones
            "Ultra-Luxury": 5  # Average of 4-6 zones
        }
        
        # Calculate tonnage, systems and zones
        tonnage = square_footage / tonnage_factors[tier]
        systems = math.ceil(square_footage / system_factors[tier])
        zones = systems * zones_per_system[tier]
        
        return {
            "tonnage": round(tonnage, 1),  # Round to 1 decimal place
            "systems": systems,
            "zones": round(zones)
        }
        
    def _calculate_distribution(self, square_footage, tier):
        """Calculate HVAC distribution components"""
        # Distribution factors by tier
        flex_duct_factors = {
            "Premium": 2.5,    # LF per 100 sq ft
            "Luxury": 2.8,
            "Ultra-Luxury": 3.0
        }
        
        hard_duct_factors = {
            "Premium": 1.0,    # LF per 100 sq ft
            "Luxury": 1.2,
            "Ultra-Luxury": 1.5
        }
        
        register_factors = {
            "Premium": 125,    # 1 register per X sq ft
            "Luxury": 110,
            "Ultra-Luxury": 100
        }
        
        return_factors = {
            "Premium": 1000,   # 1 additional return per X sq ft
            "Luxury": 850,
            "Ultra-Luxury": 700
        }
        
        # Calculate distribution components
        flex_duct = (square_footage * flex_duct_factors[tier]) / 100
        hard_duct = (square_footage * hard_duct_factors[tier]) / 100
        registers = square_footage / register_factors[tier]
        
        # Returns are based on zones plus additional returns based on sq ft
        zones = self._calculate_system_sizing(square_footage, tier)["zones"]
        returns = zones + (square_footage / return_factors[tier])
        
        return {
            "flex_duct_linear_feet": round(flex_duct),
            "hard_duct_linear_feet": round(hard_duct),
            "registers": round(registers),
            "returns": round(returns)
        }