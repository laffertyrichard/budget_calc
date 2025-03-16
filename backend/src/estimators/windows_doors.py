import math
import logging

logger = logging.getLogger(__name__)

class WindowsDoorsEstimator:
    """Handles windows and doors quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate window and door quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate window quantities
        results.update(self._calculate_windows(square_footage, tier))
        
        # Calculate exterior door quantities
        results.update(self._calculate_exterior_doors(square_footage, tier))
        
        # Calculate garage door quantities
        results.update(self._calculate_garage_doors(square_footage, tier))
        
        return results
        
    def _calculate_windows(self, square_footage, tier):
        """Calculate window quantities"""
        # Windows per square foot of house
        windows_per_sf = {
            "Premium": 0.006,
            "Luxury": 0.008,
            "Ultra-Luxury": 0.01
        }
        
        # Average window size by tier
        avg_window_sf = {
            "Premium": 12,
            "Luxury": 15,
            "Ultra-Luxury": 18
        }
        
        # Window efficiency level by tier
        window_efficiency = {
            "Premium": "Low-E Double Pane",
            "Luxury": "Low-E Triple Pane",
            "Ultra-Luxury": "Dynamic Glass/Smart Glass"
        }
        
        # Calculate window count and area
        window_count = round(square_footage * windows_per_sf[tier])
        window_area = window_count * avg_window_sf[tier]
        
        # Calculate window trim (perimeter of all windows)
        trim_per_window = 4 * math.sqrt(avg_window_sf[tier])
        window_trim = window_count * trim_per_window
        
        return {
            "window_count": window_count,
            "window_area_sf": round(window_area),
            "window_efficiency": window_efficiency[tier],
            "window_trim_lf": round(window_trim)
        }
        
    def _calculate_exterior_doors(self, square_footage, tier):
        """Calculate exterior door quantities"""
        # Base number of exterior doors by tier
        base_doors = {
            "Premium": 2,
            "Luxury": 3,
            "Ultra-Luxury": 4
        }
        
        # Additional doors for larger homes
        additional_doors_per_3000 = {
            "Premium": 0,
            "Luxury": 1,
            "Ultra-Luxury": 2
        }
        
        # Base patio/sliding door sets
        base_patio_doors = {
            "Premium": 1,
            "Luxury": 2,
            "Ultra-Luxury": 3
        }
        
        # Additional patio doors for larger homes
        additional_patio_per_4000 = {
            "Premium": 0.5,
            "Luxury": 1,
            "Ultra-Luxury": 1.5
        }
        
        # Door type by tier
        door_type = {
            "Premium": "Fiberglass/Wood",
            "Luxury": "Premium Wood/Steel",
            "Ultra-Luxury": "Custom Wood/Steel"
        }
        
        # Calculate additional doors based on square footage
        additional_doors = 0
        if square_footage > 6000:
            additional_doors = math.floor((square_footage - 6000) / 3000) * additional_doors_per_3000[tier]
            
        # Calculate additional patio doors based on square footage
        additional_patio = 0
        if square_footage > 4000:
            additional_patio = math.floor((square_footage - 4000) / 4000) * additional_patio_per_4000[tier]
            
        # Calculate total doors
        exterior_doors = base_doors[tier] + additional_doors
        patio_doors = base_patio_doors[tier] + additional_patio
        
        # Calculate hardware sets (typically one per door)
        door_hardware = exterior_doors + (patio_doors * 0.5)  # less hardware for sliding doors
        
        return {
            "exterior_door_count": round(exterior_doors),
            "patio_door_sets": round(patio_doors),
            "door_hardware_sets": round(door_hardware),
            "exterior_door_type": door_type[tier]
        }
        
    def _calculate_garage_doors(self, square_footage, tier):
        """Calculate garage door quantities"""
        # Garage doors by tier
        garage_doors = {
            "Premium": 2,
            "Luxury": 3,
            "Ultra-Luxury": 4
        }
        
        # Auto-openers (typically one per door)
        auto_openers = garage_doors[tier]
        
        # Calculate quantity
        return {
            "garage_door_count": garage_doors[tier],
            "garage_door_openers": auto_openers
        }