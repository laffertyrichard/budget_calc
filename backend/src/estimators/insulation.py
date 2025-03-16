import logging

logger = logging.getLogger(__name__)

class InsulationEstimator:
    """Handles insulation quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate insulation quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate wall insulation
        results.update(self._calculate_wall_insulation(square_footage, tier))
        
        # Calculate ceiling insulation
        results.update(self._calculate_ceiling_insulation(square_footage, tier))
        
        # Calculate specialty insulation
        results.update(self._calculate_specialty_insulation(square_footage, tier))
        
        # Calculate weatherproofing
        results.update(self._calculate_weatherproofing(square_footage, tier))
        
        return results
        
    def _calculate_wall_insulation(self, square_footage, tier):
        """Calculate wall insulation quantities"""
        # Wall insulation SF per SF of house
        wall_insulation_factor = {
            "Premium": 0.85,
            "Luxury": 0.95,
            "Ultra-Luxury": 1.05
        }
        
        # Wall R-value by tier
        wall_r_value = {
            "Premium": 19,
            "Luxury": 21,
            "Ultra-Luxury": 24
        }
        
        # Calculate wall insulation area
        wall_insulation = square_footage * wall_insulation_factor[tier]
        
        return {
            "wall_insulation_sf": round(wall_insulation),
            "wall_r_value": wall_r_value[tier]
        }
        
    def _calculate_ceiling_insulation(self, square_footage, tier):
        """Calculate ceiling insulation quantities"""
        # Ceiling insulation SF per SF of house (typically 1:1)
        ceiling_insulation_factor = 1.0  # Same for all tiers
        
        # Ceiling R-value by tier
        ceiling_r_value = {
            "Premium": 38,
            "Luxury": 49,
            "Ultra-Luxury": 60
        }
        
        # Calculate ceiling insulation area
        ceiling_insulation = square_footage * ceiling_insulation_factor
        
        return {
            "ceiling_insulation_sf": round(ceiling_insulation),
            "ceiling_r_value": ceiling_r_value[tier]
        }
        
    def _calculate_specialty_insulation(self, square_footage, tier):
        """Calculate specialty insulation quantities"""
        result = {}
        
        # Rigid insulation percentages by tier
        rigid_insulation_pct = {
            "Premium": 0.2,
            "Luxury": 0.4,
            "Ultra-Luxury": 0.6
        }
        
        # Acoustic insulation percentages by tier
        acoustic_insulation_pct = {
            "Premium": 0.05,
            "Luxury": 0.15,
            "Ultra-Luxury": 0.3
        }
        
        # Calculate specialty insulation areas
        result["rigid_insulation_sf"] = round(square_footage * rigid_insulation_pct[tier])
        result["acoustic_insulation_sf"] = round(square_footage * acoustic_insulation_pct[tier])
        
        # Add radiant barrier for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            radiant_barrier_pct = 0.5 if tier == "Luxury" else 1.0
            result["radiant_barrier_sf"] = round(square_footage * radiant_barrier_pct)
        
        # Add thermal break tape for ultra-luxury
        if tier == "Ultra-Luxury":
            result["thermal_break_tape_lf"] = round(square_footage * 0.8)
            
        return result
        
    def _calculate_weatherproofing(self, square_footage, tier):
        """Calculate weatherproofing quantities"""
        # Calculate wall area from wall insulation calculations
        wall_area = self._calculate_wall_insulation(square_footage, tier)["wall_insulation_sf"]
        
        # Weather barrier typically covers wall area with slight overlap (10%)
        weather_barrier = wall_area * 1.1
        
        # Caulk tubes per SF of house
        caulk_factor = {
            "Premium": 0.01,
            "Luxury": 0.015,
            "Ultra-Luxury": 0.02
        }
        
        # Foam sealant cans per SF of house
        foam_factor = {
            "Premium": 0.003,
            "Luxury": 0.005,
            "Ultra-Luxury": 0.007
        }
        
        # Calculate weatherproofing quantities
        caulk_tubes = square_footage * caulk_factor[tier]
        foam_cans = square_footage * foam_factor[tier]
        
        return {
            "weather_barrier_sf": round(weather_barrier),
            "caulk_tubes": round(caulk_tubes),
            "foam_sealant_cans": round(foam_cans)
        }