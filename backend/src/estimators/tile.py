import logging

logger = logging.getLogger(__name__)

class TileEstimator:
    """Handles tile quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate tile quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get bathroom counts from kwargs or use defaults
        primary_bath_count = kwargs.get('primary_bath_count', 1)
        secondary_bath_count = kwargs.get('secondary_bath_count', 1)
        powder_room_count = kwargs.get('powder_room_count', 0)
            
        results = {}
        
        # Calculate primary bathroom tile
        results.update(self._calculate_primary_bath_tile(tier, primary_bath_count))
        
        # Calculate secondary bathroom tile
        results.update(self._calculate_secondary_bath_tile(tier, secondary_bath_count))
        
        # Calculate powder room tile
        results.update(self._calculate_powder_room_tile(tier, powder_room_count))
        
        # Calculate kitchen tile
        results.update(self._calculate_kitchen_tile(square_footage, tier))
        
        # Calculate other tile areas
        results.update(self._calculate_other_tile(square_footage, tier))
        
        # Calculate totals
        results.update(self._calculate_totals(results))
        
        # Calculate simplified formula result
        results.update(self._calculate_simplified(square_footage, tier, primary_bath_count, 
                                                secondary_bath_count, powder_room_count))
        
        return results
        
    def _calculate_primary_bath_tile(self, tier, count):
        """Calculate primary bathroom tile quantities"""
        if count <= 0:
            return {'primary_bath_count': 0}
            
        # Tile SF per primary bathroom by component and tier
        shower_floor = {
            "Premium": 15,
            "Luxury": 25,
            "Ultra-Luxury": 45
        }
        
        shower_walls = {
            "Premium": 110,
            "Luxury": 160,
            "Ultra-Luxury": 250
        }
        
        bathroom_floor = {
            "Premium": 70,
            "Luxury": 120,
            "Ultra-Luxury": 200
        }
        
        shampoo_niches = {
            "Premium": 2.5,
            "Luxury": 5,
            "Ultra-Luxury": 10
        }
        
        edge_treatment = {
            "Premium": 45,
            "Luxury": 80,
            "Ultra-Luxury": 150
        }
        
        # Calculate total tile quantities for all primary bathrooms
        result = {
            "primary_bath_count": count,
            "primary_bath_shower_floor_sf": round(count * shower_floor[tier]),
            "primary_bath_shower_walls_sf": round(count * shower_walls[tier]),
            "primary_bath_floor_sf": round(count * bathroom_floor[tier]),
            "primary_bath_niches_sf": round(count * shampoo_niches[tier]),
            "primary_bath_schluter_lf": round(count * edge_treatment[tier])
        }
        
        # Calculate total primary bath tile
        result["primary_bath_tile_sf"] = (
            result["primary_bath_shower_floor_sf"] +
            result["primary_bath_shower_walls_sf"] +
            result["primary_bath_floor_sf"] +
            result["primary_bath_niches_sf"]
        )
        
        return result
        
    def _calculate_secondary_bath_tile(self, tier, count):
        """Calculate secondary bathroom tile quantities"""
        if count <= 0:
            return {'secondary_bath_count': 0}
            
        # Tile SF per secondary bathroom by component and tier
        shower_floor = {
            "Premium": 9,
            "Luxury": 16,
            "Ultra-Luxury": 25
        }
        
        shower_walls = {
            "Premium": 70,
            "Luxury": 100,
            "Ultra-Luxury": 150
        }
        
        bathroom_floor = {
            "Premium": 45,
            "Luxury": 60,
            "Ultra-Luxury": 95
        }
        
        shampoo_niches = {
            "Premium": 2,
            "Luxury": 3,
            "Ultra-Luxury": 5
        }
        
        edge_treatment = {
            "Premium": 30,
            "Luxury": 50,
            "Ultra-Luxury": 80
        }
        
        # Calculate total tile quantities for all secondary bathrooms
        result = {
            "secondary_bath_count": count,
            "secondary_bath_shower_floor_sf": round(count * shower_floor[tier]),
            "secondary_bath_shower_walls_sf": round(count * shower_walls[tier]),
            "secondary_bath_floor_sf": round(count * bathroom_floor[tier]),
            "secondary_bath_niches_sf": round(count * shampoo_niches[tier]),
            "secondary_bath_schluter_lf": round(count * edge_treatment[tier])
        }
        
        # Calculate total secondary bath tile
        result["secondary_bath_tile_sf"] = (
            result["secondary_bath_shower_floor_sf"] +
            result["secondary_bath_shower_walls_sf"] +
            result["secondary_bath_floor_sf"] +
            result["secondary_bath_niches_sf"]
        )
        
        return result
        
    def _calculate_powder_room_tile(self, tier, count):
        """Calculate powder room tile quantities"""
        if count <= 0:
            return {'powder_room_count': 0}
            
        # Tile SF per powder room by component and tier
        floor_tile = {
            "Premium": 25,
            "Luxury": 35,
            "Ultra-Luxury": 50
        }
        
        accent_wall = {
            "Premium": 0,
            "Luxury": 15,
            "Ultra-Luxury": 30
        }
        
        edge_treatment = {
            "Premium": 0,
            "Luxury": 10,
            "Ultra-Luxury": 20
        }
        
        # Calculate total tile quantities for all powder rooms
        result = {
            "powder_room_count": count,
            "powder_room_floor_sf": round(count * floor_tile[tier]),
            "powder_room_accent_wall_sf": round(count * accent_wall[tier]),
            "powder_room_schluter_lf": round(count * edge_treatment[tier])
        }
        
        # Calculate total powder room tile
        result["powder_room_tile_sf"] = (
            result["powder_room_floor_sf"] +
            result["powder_room_accent_wall_sf"]
        )
        
        return result
        
    def _calculate_kitchen_tile(self, square_footage, tier):
        """Calculate kitchen backsplash and other tile quantities"""
        # Kitchen backsplash base SF by tier
        base_amount = {
            "Premium": 40,
            "Luxury": 60,
            "Ultra-Luxury": 100
        }
        
        # Additional per 1000 SF by tier
        additional_per_1000 = {
            "Premium": 5,
            "Luxury": 7,
            "Ultra-Luxury": 10
        }
        
        # Butler's/prep kitchen by tier (SF)
        butlers_kitchen = {
            "Premium": 0,
            "Luxury": 25,
            "Ultra-Luxury": 40
        }
        
        # Calculate backsplash area
        backsplash = base_amount[tier] + ((square_footage / 1000) * additional_per_1000[tier])
        
        return {
            "kitchen_backsplash_tile_sf": round(backsplash),
            "butlers_kitchen_tile_sf": round(butlers_kitchen[tier])
        }
        
    def _calculate_other_tile(self, square_footage, tier):
        """Calculate other tile areas"""
        # Other tile areas by tier (SF)
        laundry_room = {
            "Premium": 50,
            "Luxury": 75,
            "Ultra-Luxury": 120
        }
        
        mudroom = {
            "Premium": 40,
            "Luxury": 60,
            "Ultra-Luxury": 100
        }
        
        entry_foyer = {
            "Premium": 80,
            "Luxury": 150,
            "Ultra-Luxury": 300
        }
        
        return {
            "laundry_room_tile_sf": round(laundry_room[tier]),
            "mudroom_tile_sf": round(mudroom[tier]),
            "entry_foyer_tile_sf": round(entry_foyer[tier])
        }
        
    def _calculate_totals(self, tile_data):
        """Calculate total tile quantities"""
        # Calculate total bathroom tile
        bathroom_tile = (
            tile_data.get("primary_bath_tile_sf", 0) +
            tile_data.get("secondary_bath_tile_sf", 0) +
            tile_data.get("powder_room_tile_sf", 0)
        )
        
        # Calculate total kitchen tile
        kitchen_tile = (
            tile_data.get("kitchen_backsplash_tile_sf", 0) +
            tile_data.get("butlers_kitchen_tile_sf", 0)
        )
        
        # Calculate total other tile
        other_tile = (
            tile_data.get("laundry_room_tile_sf", 0) +
            tile_data.get("mudroom_tile_sf", 0) +
            tile_data.get("entry_foyer_tile_sf", 0)
        )
        
        # Calculate total schluter/edge treatment
        total_schluter = (
            tile_data.get("primary_bath_schluter_lf", 0) +
            tile_data.get("secondary_bath_schluter_lf", 0) +
            tile_data.get("powder_room_schluter_lf", 0)
        )
        
        return {
            "total_bathroom_tile_sf": round(bathroom_tile),
            "total_kitchen_tile_sf": round(kitchen_tile),
            "total_other_tile_sf": round(other_tile),
            "total_tile_sf": round(bathroom_tile + kitchen_tile + other_tile),
            "total_schluter_lf": round(total_schluter)
        }
        
    def _calculate_simplified(self, square_footage, tier, primary_bath_count, 
                            secondary_bath_count, powder_room_count):
        """Calculate total tile using simplified formula"""
        # Simplified formula factors by tier
        house_factor = {
            "Premium": 0.05,
            "Luxury": 0.07,
            "Ultra-Luxury": 0.09
        }
        
        primary_bath = {
            "Premium": 200,
            "Luxury": 315,
            "Ultra-Luxury": 510
        }
        
        secondary_bath = {
            "Premium": 125,
            "Luxury": 180,
            "Ultra-Luxury": 280
        }
        
        powder_room = {
            "Premium": 25,
            "Luxury": 50,
            "Ultra-Luxury": 80
        }
        
        # Schluter factors
        schluter_primary = {
            "Premium": 45,
            "Luxury": 80,
            "Ultra-Luxury": 150
        }
        
        schluter_secondary = {
            "Premium": 30,
            "Luxury": 50,
            "Ultra-Luxury": 80
        }
        
        schluter_powder = {
            "Premium": 0,
            "Luxury": 10,
            "Ultra-Luxury": 20
        }
        
        # Calculate simplified totals
        simplified_tile = (
            (square_footage * house_factor[tier]) +
            (primary_bath_count * primary_bath[tier]) +
            (secondary_bath_count * secondary_bath[tier]) +
            (powder_room_count * powder_room[tier])
        )
        
        simplified_schluter = (
            (primary_bath_count * schluter_primary[tier]) +
            (secondary_bath_count * schluter_secondary[tier]) +
            (powder_room_count * schluter_powder[tier])
        )
        
        return {
            "simplified_total_tile_sf": round(simplified_tile),
            "simplified_total_schluter_lf": round(simplified_schluter)
        }