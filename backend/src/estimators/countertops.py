import logging

logger = logging.getLogger(__name__)

class CountertopsEstimator:
    """Handles countertop quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate countertop quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get bathroom counts from kwargs or use defaults
        primary_bath_count = kwargs.get('primary_bath_count', 1)
        secondary_bath_count = kwargs.get('secondary_bath_count', 1)
        powder_room_count = kwargs.get('powder_room_count', 0)
            
        results = {}
        
        # Calculate kitchen countertops
        results.update(self._calculate_kitchen_countertops(square_footage, tier))
        
        # Calculate bathroom countertops
        results.update(self._calculate_bathroom_countertops(tier, primary_bath_count, 
                                                          secondary_bath_count, powder_room_count))
        
        # Calculate material distribution
        results.update(self._calculate_material_distribution(tier, results))
        
        # Calculate totals
        results.update(self._calculate_totals(results))
        
        return results
        
    def _calculate_kitchen_countertops(self, square_footage, tier):
        """Calculate kitchen countertop quantities"""
        # Base amounts by tier (square feet)
        kitchen_base = {
            "Premium": 65,
            "Luxury": 85,
            "Ultra-Luxury": 110
        }
        
        # Base square footage threshold by tier
        base_sq_ft = {
            "Premium": 4000,
            "Luxury": 6000,
            "Ultra-Luxury": 10000
        }
        
        # Additional amount per 1000 SF above threshold
        additional_per_1000 = {
            "Premium": 10,
            "Luxury": 12,
            "Ultra-Luxury": 15
        }
        
        # Calculate countertop area
        kitchen_ct = kitchen_base[tier]
        if square_footage > base_sq_ft[tier]:
            kitchen_ct += ((square_footage - base_sq_ft[tier]) / 1000) * additional_per_1000[tier]
            
        # Butler's pantry countertops for luxury tiers
        butlers_pantry = 0
        if tier == "Luxury":
            butlers_pantry = 30
        elif tier == "Ultra-Luxury":
            butlers_pantry = 50
            
        # Waterfall edges (decorative sides on islands)
        waterfall_edges = 0
        if tier == "Premium":
            waterfall_edges = 3 if square_footage > 5000 else 0
        elif tier == "Luxury":
            waterfall_edges = 8
        elif tier == "Ultra-Luxury":
            waterfall_edges = 15
            
        return {
            "kitchen_countertops_sf": round(kitchen_ct),
            "butlers_pantry_countertops_sf": round(butlers_pantry),
            "waterfall_edges_lf": round(waterfall_edges)
        }
        
    def _calculate_bathroom_countertops(self, tier, primary_bath_count, 
                                      secondary_bath_count, powder_room_count):
        """Calculate bathroom countertop quantities"""
        # Average SF per bathroom by tier
        primary_bath = {
            "Premium": 30,
            "Luxury": 48,
            "Ultra-Luxury": 75
        }
        
        secondary_bath = {
            "Premium": 14,
            "Luxury": 18,
            "Ultra-Luxury": 25
        }
        
        powder_room = {
            "Premium": 9,
            "Luxury": 12,
            "Ultra-Luxury": 18
        }
        
        # Calculate countertop areas
        primary_bath_ct = primary_bath_count * primary_bath[tier]
        secondary_bath_ct = secondary_bath_count * secondary_bath[tier]
        powder_room_ct = powder_room_count * powder_room[tier]
        
        return {
            "primary_bath_countertops_sf": round(primary_bath_ct),
            "secondary_bath_countertops_sf": round(secondary_bath_ct),
            "powder_room_countertops_sf": round(powder_room_ct)
        }
        
    def _calculate_material_distribution(self, tier, countertop_data):
        """Calculate distribution of countertop materials"""
        # Material distribution percentages by tier
        material_dist = {
            "Premium": {
                "quartz": 0.65,
                "granite": 0.25,
                "marble": 0.07,
                "quartzite": 0.03,
                "specialty": 0
            },
            "Luxury": {
                "quartz": 0.45,
                "granite": 0.25,
                "marble": 0.17,
                "quartzite": 0.13,
                "specialty": 0
            },
            "Ultra-Luxury": {
                "quartz": 0.35,
                "granite": 0.17,
                "marble": 0.25,
                "quartzite": 0.18,
                "specialty": 0.05
            }
        }
        
        # Calculate total countertop area
        total_sf = (
            countertop_data.get("kitchen_countertops_sf", 0) +
            countertop_data.get("butlers_pantry_countertops_sf", 0) +
            countertop_data.get("primary_bath_countertops_sf", 0) +
            countertop_data.get("secondary_bath_countertops_sf", 0) +
            countertop_data.get("powder_room_countertops_sf", 0)
        )
        
        # Calculate material breakdown
        result = {}
        for material, percentage in material_dist[tier].items():
            if percentage > 0:
                result[f"{material}_countertops_sf"] = round(total_sf * percentage)
                
        return result
        
    def _calculate_totals(self, countertop_data):
        """Calculate total countertop areas"""
        # Total kitchen countertops
        kitchen_total = (
            countertop_data.get("kitchen_countertops_sf", 0) +
            countertop_data.get("butlers_pantry_countertops_sf", 0)
        )
        
        # Total bathroom countertops
        bathroom_total = (
            countertop_data.get("primary_bath_countertops_sf", 0) +
            countertop_data.get("secondary_bath_countertops_sf", 0) +
            countertop_data.get("powder_room_countertops_sf", 0)
        )
        
        return {
            "total_kitchen_countertops_sf": round(kitchen_total),
            "total_bathroom_countertops_sf": round(bathroom_total),
            "total_countertops_sf": round(kitchen_total + bathroom_total)
        }