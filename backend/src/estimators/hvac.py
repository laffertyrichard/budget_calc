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
        system_sizing = self._calculate_system_sizing(square_footage, tier)
        results.update(system_sizing)
        
        # Calculate distribution components
        distribution = self._calculate_distribution(square_footage, tier)
        results.update(distribution)
        
        # Calculate optimal HVAC unit combination for efficient cooling
        hvac_system = self.calculate_hvac_system(square_footage, tier)
        results.update(hvac_system)
        
        return results
        
    def _calculate_system_sizing(self, square_footage, tier):
        """Calculate HVAC system sizing"""
        # Tonnage calculation based on square footage and tier
        tonnage_factors = {
            "Premium": 500,    # 1 ton per 500 sq ft
            "Luxury": 450,     # 1 ton per 450 sq ft
            "Ultra-Luxury": 400  # 1 ton per 400 sq ft
        }
        
        # System count calculation
        system_factors = {
            "Premium": 2000,   # New system every 2000 sq ft
            "Luxury": 1800,    # New system every 1800 sq ft
            "Ultra-Luxury": 1600  # New system every 1600 sq ft
        }
        
        # Zones per system vary by tier
        zones_per_system = {
            "Premium": 1.5,    # Average 1-2 zone
            "Luxury": 2.5,     # Average of 2-3 zones
            "Ultra-Luxury": 3.5  # Average of 3-4 zones
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
    
    @staticmethod
    def _calculate_unit_combination(required_tons, available_units=[2, 3, 4, 5]):
        """
        Finds the combination of HVAC unit sizes that meets or exceeds the required tonnage
        with the smallest oversize and fewest units.
        """
        # Set an upper bound for capacity calculation
        max_capacity = required_tons + max(available_units)
        # dp[cap] holds a tuple: (number_of_units, combination_list) for capacity "cap"
        dp = [None] * (max_capacity + 1)
        dp[0] = (0, [])
        
        for cap in range(1, max_capacity + 1):
            for unit in available_units:
                if cap - unit >= 0 and dp[cap - unit] is not None:
                    candidate_units = dp[cap - unit][0] + 1
                    candidate_combo = dp[cap - unit][1] + [unit]
                    if dp[cap] is None:
                        dp[cap] = (candidate_units, candidate_combo)
                    else:
                        current_units, current_combo = dp[cap]
                        # Prefer fewer units and lower total capacity to minimize oversize
                        if candidate_units < current_units or (candidate_units == current_units and sum(candidate_combo) < sum(current_combo)):
                            dp[cap] = (candidate_units, candidate_combo)
                            
        best_combo = None
        best_units = None
        best_oversize = None
        best_total = None
        
        # Evaluate combinations for any capacity >= required_tons
        for cap in range(required_tons, max_capacity + 1):
            if dp[cap] is not None:
                oversize = cap - required_tons
                units = dp[cap][0]
                if best_combo is None or (oversize < best_oversize) or (oversize == best_oversize and units < best_units):
                    best_combo = dp[cap][1]
                    best_units = units
                    best_oversize = oversize
                    best_total = cap
                    
        return {
            "units": best_combo,
            "unit_count": best_units,
            "total_capacity": best_total,
            "oversize": best_oversize
        }
    
    def calculate_hvac_system(self, square_footage, tier):
        """
        Calculate the required HVAC tonnage and determine the optimal combination of 
        2, 3, 4, and 5-ton units for efficient cooling.
        """
        # Tonnage factors based on tier
        tonnage_factors = {
            "Premium": 500,
            "Luxury": 450,
            "Ultra-Luxury": 400
        }
        
        # Calculate required tonnage (in tons)
        required_tonnage = square_footage / tonnage_factors[tier]
        # Round up to ensure capacity meets requirements
        required_tonnage_int = math.ceil(required_tonnage)
        
        # Determine the optimal HVAC unit combination
        hvac_units = self._calculate_unit_combination(required_tonnage_int)
        
        return {
            "required_tonnage": round(required_tonnage, 1),
            "hvac_units": hvac_units
        }
