import math
import logging

logger = logging.getLogger(__name__)

class FinishCarpentryEstimator:
    """Handles finish carpentry quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate finish carpentry quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get room counts from kwargs or use defaults
        bedroom_count = kwargs.get('bedroom_count', 3)
        bathroom_count = kwargs.get('bathroom_count', 2)
        if 'bathroom_count' not in kwargs:
            # If no bathroom count is provided, try to calculate from primary and secondary
            primary_bath_count = kwargs.get('primary_bath_count', 1)
            secondary_bath_count = kwargs.get('secondary_bath_count', 1)
            bathroom_count = primary_bath_count + secondary_bath_count
            
        powder_room_count = kwargs.get('powder_room_count', 0)
            
        results = {}
        
        # Calculate interior doors
        results.update(self._calculate_doors(square_footage, tier, bedroom_count, bathroom_count, powder_room_count))
        
        # Calculate trim
        results.update(self._calculate_trim(square_footage, tier, bathroom_count))
        
        # Calculate simplified formula
        results.update(self._calculate_simplified(square_footage, bedroom_count, bathroom_count, powder_room_count, tier))
        
        return results
        
    def _calculate_doors(self, square_footage, tier, bedroom_count, bathroom_count, powder_room_count):
        """Calculate interior door quantities"""
        # Single doors
        bedroom_doors = bedroom_count  # One door per bedroom
        
        # Bedroom closet doors vary by tier
        bedroom_closet_doors = {
            "Premium": bedroom_count,  # One per bedroom
            "Luxury": round(bedroom_count * 1.5),  # Average of 1-2 per bedroom
            "Ultra-Luxury": bedroom_count * 2  # Two per bedroom
        }[tier]
        
        # Bathroom doors
        bathroom_doors = bathroom_count  # One per bathroom
        
        # Powder room doors
        powder_room_doors = powder_room_count  # One per powder room
        
        # Utility room doors (assuming 2 utility rooms - laundry, mechanical)
        utility_room_doors = 2
        
        # Additional doors beyond base square footage
        additional_doors_per_1000 = {
            "Premium": 1,
            "Luxury": 1.5,
            "Ultra-Luxury": 2
        }
        
        base_sq_ft = 4000
        additional_single_doors = 0
        if square_footage > base_sq_ft:
            additional_single_doors = ((square_footage - base_sq_ft) / 1000) * additional_doors_per_1000[tier]
        
        # Calculate total single doors
        single_doors = bedroom_doors + bedroom_closet_doors + bathroom_doors + powder_room_doors + utility_room_doors + additional_single_doors
        
        # Double doors
        if tier == "Premium":
            office_double_doors = 0.5  # Average of 0-1
            dining_double_doors = 0.5  # Average of 0-1
            primary_bedroom_double_doors = 0
            additional_double_doors_per_2000 = 0
        elif tier == "Luxury":
            office_double_doors = 1
            dining_double_doors = 1
            primary_bedroom_double_doors = 0.5  # Average of 0-1
            additional_double_doors_per_2000 = 1
        else:  # Ultra-Luxury
            office_double_doors = 1
            dining_double_doors = 1
            primary_bedroom_double_doors = 1
            additional_double_doors_per_2000 = 2
        
        # Additional double doors for larger homes
        additional_double_doors = 0
        if square_footage > base_sq_ft:
            additional_double_doors = ((square_footage - base_sq_ft) / 2000) * additional_double_doors_per_2000
        
        # Calculate total double doors
        double_doors = office_double_doors + dining_double_doors + primary_bedroom_double_doors + additional_double_doors
        
        # Special doors (pocket, barn, etc.)
        if tier == "Premium":
            pocket_doors = 1.5  # Average of 1-2
            barn_doors = 0.5    # Average of 0-1
            garage_man_doors = 1
            exterior_utility_doors = 1.5  # Average of 1-2
        elif tier == "Luxury":
            pocket_doors = 4     # Average of 3-5
            barn_doors = 2       # Average of 1-3
            garage_man_doors = 1.5  # Average of 1-2
            exterior_utility_doors = 2.5  # Average of 2-3
        else:  # Ultra-Luxury
            pocket_doors = 8     # Average of 6-10
            barn_doors = 4       # Average of 3-5
            garage_man_doors = 2.5  # Average of 2-3
            exterior_utility_doors = 4  # Average of 3-5
        
        return {
            "single_doors": round(single_doors),
            "double_doors": round(double_doors),
            "pocket_doors": round(pocket_doors),
            "barn_doors": round(barn_doors),
            "garage_man_doors": round(garage_man_doors),
            "exterior_utility_doors": round(exterior_utility_doors)
        }
        
    def _calculate_trim(self, square_footage, tier, bathroom_count):
        """Calculate trim quantities"""
        # Baseboard linear feet per sq ft of house
        baseboard_lf_per_sq_ft = {
            "Premium": 0.8,
            "Luxury": 0.9,
            "Ultra-Luxury": 1.0
        }
        
        # Bathroom deduction (LF per bathroom)
        bathroom_deduction_lf = {
            "Premium": 20,
            "Luxury": 25,
            "Ultra-Luxury": 30
        }
        
        # Open concept adjustment (percentage)
        open_concept_adjustment = {
            "Premium": 0.05,
            "Luxury": 0.10,
            "Ultra-Luxury": 0.15
        }
        
        # Calculate baseboard linear feet
        baseboard_lf = square_footage * baseboard_lf_per_sq_ft[tier]
        bathroom_deduction = bathroom_count * bathroom_deduction_lf[tier]
        open_concept_deduction = baseboard_lf * open_concept_adjustment[tier]
        
        # Calculate final baseboard length
        final_baseboard_lf = baseboard_lf - bathroom_deduction - open_concept_deduction
        
        # Calculate crown molding (typically in main living areas)
        crown_molding_factor = {
            "Premium": 0.3,    # 30% of house gets crown molding
            "Luxury": 0.6,     # 60% of house gets crown molding
            "Ultra-Luxury": 0.8  # 80% of house gets crown molding
        }
        
        crown_molding_lf = final_baseboard_lf * crown_molding_factor[tier]
        
        # Calculate casing (around doors and windows)
        # Assume 20 LF per door and 16 LF per window
        doors_count = self._calculate_doors(square_footage, tier, 3, 2, 1)["single_doors"]
        window_count = round(square_footage * 0.008)  # Approx. 0.008 windows per sq ft
        
        door_casing_lf = doors_count * 20
        window_casing_lf = window_count * 16
        
        return {
            "baseboard_lf": round(final_baseboard_lf),
            "crown_molding_lf": round(crown_molding_lf),
            "door_casing_lf": round(door_casing_lf),
            "window_casing_lf": round(window_casing_lf),
            "total_trim_lf": round(final_baseboard_lf + crown_molding_lf + door_casing_lf + window_casing_lf)
        }
        
    def _calculate_simplified(self, square_footage, bedroom_count, bathroom_count, powder_room_count, tier):
        """Calculate using simplified formula"""
        # Door formula factors
        single_door_factor = {
            "Premium": 2,
            "Luxury": 3,
            "Ultra-Luxury": 4
        }
        
        double_door_factor = {
            "Premium": 0.5,
            "Luxury": 1,
            "Ultra-Luxury": 1.5
        }
        
        # Baseboard formula factor
        baseboard_factor = {
            "Premium": 0.75,
            "Luxury": 0.85,
            "Ultra-Luxury": 0.95
        }
        
        # Calculate using simplified formula
        simplified_single_doors = (bedroom_count * 2) + (bathroom_count * 1.2) + (square_footage / 1000 * single_door_factor[tier])
        simplified_double_doors = (square_footage / 3000 * double_door_factor[tier])
        simplified_baseboard = square_footage * baseboard_factor[tier]
        
        return {
            "simplified_single_doors": round(simplified_single_doors),
            "simplified_double_doors": round(simplified_double_doors),
            "simplified_baseboard_lf": round(simplified_baseboard)
        }