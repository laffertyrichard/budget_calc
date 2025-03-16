import logging

logger = logging.getLogger(__name__)

class CabinetryEstimator:
    """Handles cabinetry quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate cabinetry quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get bathroom counts from kwargs or use defaults
        primary_bath_count = kwargs.get('primary_bath_count', 1)
        secondary_bath_count = kwargs.get('secondary_bath_count', 1)
        powder_room_count = kwargs.get('powder_room_count', 0)
            
        results = {}
        
        # Calculate kitchen cabinetry
        results.update(self._calculate_kitchen_cabinetry(square_footage, tier))
        
        # Calculate bathroom cabinetry
        results.update(self._calculate_bathroom_cabinetry(square_footage, tier, 
                                                         primary_bath_count, 
                                                         secondary_bath_count, 
                                                         powder_room_count))
        
        # Calculate specialty cabinetry
        results.update(self._calculate_specialty_cabinetry(square_footage, tier))
        
        # Calculate summary totals
        results.update(self._calculate_totals(results))
        
        return results
        
    def _calculate_kitchen_cabinetry(self, square_footage, tier):
        """Calculate kitchen cabinetry quantities"""
        # Base amounts by tier (linear feet)
        base_cabinet_base = {
            "Premium": 22,
            "Luxury": 28,
            "Ultra-Luxury": 34
        }
        
        wall_cabinet_base = {
            "Premium": 18,
            "Luxury": 24,
            "Ultra-Luxury": 30
        }
        
        island_base = {
            "Premium": 8,
            "Luxury": 10,
            "Ultra-Luxury": 14
        }
        
        full_height_base = {
            "Premium": 6,
            "Luxury": 8,
            "Ultra-Luxury": 12
        }
        
        # Additional amount per 1000 SF above 4000 SF
        additional_per_1000_sf = 0  # Initialize
        if square_footage > 4000:
            additional_per_1000_sf = (square_footage - 4000) / 1000
        
        # Calculate cabinetry quantities
        base_cabinets = base_cabinet_base[tier] + (6 * additional_per_1000_sf)
        wall_cabinets = wall_cabinet_base[tier] + (5 * additional_per_1000_sf)
        island_cabinets = island_base[tier] + (3 * additional_per_1000_sf)
        full_height_cabinets = full_height_base[tier] + (2 * additional_per_1000_sf)
        
        return {
            "kitchen_base_cabinets_lf": round(base_cabinets, 1),
            "kitchen_wall_cabinets_lf": round(wall_cabinets, 1),
            "kitchen_island_lf": round(island_cabinets, 1),
            "kitchen_full_height_cabinets_lf": round(full_height_cabinets, 1)
        }
        
    def _calculate_bathroom_cabinetry(self, square_footage, tier, 
                                     primary_bath_count, secondary_bath_count, powder_room_count):
        """Calculate bathroom cabinetry quantities"""
        # Base amounts by tier (linear feet per bathroom)
        primary_bath_base = {
            "Premium": 8,
            "Luxury": 10,
            "Ultra-Luxury": 14
        }
        
        secondary_bath_base = {
            "Premium": 3,
            "Luxury": 4,
            "Ultra-Luxury": 5
        }
        
        powder_room = {
            "Premium": 2,
            "Luxury": 2.5,
            "Ultra-Luxury": 3
        }
        
        # Additional amount per 1000 SF above 4000 SF
        additional_per_1000_sf = 0  # Initialize
        if square_footage > 4000:
            additional_per_1000_sf = (square_footage - 4000) / 1000
        
        # Calculate cabinetry quantities
        primary_bath_vanity = primary_bath_count * (primary_bath_base[tier] + (2 * additional_per_1000_sf))
        secondary_bath_vanity = secondary_bath_count * (secondary_bath_base[tier] + (0.5 * additional_per_1000_sf))
        powder_room_vanity = powder_room_count * powder_room[tier]
        
        return {
            "primary_bath_vanity_lf": round(primary_bath_vanity, 1),
            "secondary_bath_vanity_lf": round(secondary_bath_vanity, 1),
            "powder_room_vanity_lf": round(powder_room_vanity, 1)
        }
        
    def _calculate_specialty_cabinetry(self, square_footage, tier):
        """Calculate specialty cabinetry quantities"""
        result = {}
        
        # Only calculate specialty cabinetry for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            # Home office cabinetry
            result["office_cabinetry_lf"] = round(tier == "Luxury" and 6 or 10, 1)
            
            # Butler's pantry/bar cabinetry
            butlers_pantry = tier == "Luxury" and 8 or 15
            result["butlers_pantry_lf"] = round(butlers_pantry, 1)
            
            # Media room cabinetry
            if tier == "Ultra-Luxury":
                result["media_room_cabinetry_lf"] = round(8, 1)
                
        return result
        
    def _calculate_totals(self, cabinet_data):
        """Calculate total cabinetry linear feet"""
        # Sum kitchen cabinetry
        kitchen_total = sum(
            cabinet_data.get(k, 0) for k in [
                "kitchen_base_cabinets_lf", 
                "kitchen_wall_cabinets_lf", 
                "kitchen_island_lf", 
                "kitchen_full_height_cabinets_lf"
            ]
        )
        
        # Sum bathroom cabinetry
        bathroom_total = sum(
            cabinet_data.get(k, 0) for k in [
                "primary_bath_vanity_lf", 
                "secondary_bath_vanity_lf", 
                "powder_room_vanity_lf"
            ]
        )
        
        # Sum specialty cabinetry
        specialty_total = sum(
            cabinet_data.get(k, 0) for k in [
                "office_cabinetry_lf", 
                "butlers_pantry_lf", 
                "media_room_cabinetry_lf"
            ]
        )
        
        return {
            "total_kitchen_cabinets_lf": round(kitchen_total, 1),
            "total_bathroom_cabinets_lf": round(bathroom_total, 1),
            "total_specialty_cabinets_lf": round(specialty_total, 1),
            "total_cabinetry_lf": round(kitchen_total + bathroom_total + specialty_total, 1)
        }