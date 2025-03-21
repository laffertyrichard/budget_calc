import logging

logger = logging.getLogger(__name__)

class DrywallInteriorEstimator:
    """Handles drywall and interior finish quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate drywall and interior finish quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate drywall quantities
        results.update(self._calculate_drywall(square_footage, tier))
        
        # Calculate ceiling finishes
        results.update(self._calculate_ceiling_finishes(square_footage, tier))
        
        # Calculate accessories
        results.update(self._calculate_accessories(square_footage, tier))
        
        return results
        
    def _calculate_drywall(self, square_footage, tier):
        """Calculate drywall quantities"""
        # Drywall SF per SF of house
        drywall_factor = {
            "Premium": 2.8,
            "Luxury": 3.1,
            "Ultra-Luxury": 3.5
        }
        
        
        # Ceiling height by tier
        ceiling_height = {
            "Premium": 9,
            "Luxury": 10,
            "Ultra-Luxury": 12
        }
        
        # Calculate drywall area and breakdown
        drywall_area = square_footage * drywall_factor[tier]
        smooth_area = drywall_area - textured_area
        
        # Calculate specialty drywall (moisture resistant, etc.)
        specialty_drywall_pct = {
            "Premium": 0.05,
            "Luxury": 0.1,
            "Ultra-Luxury": 0.2
        }
        
        specialty_drywall = drywall_area * specialty_drywall_pct[tier]
        
        return {
            "drywall_area_sf": round(drywall_area),
            "ceiling_height_ft": ceiling_height[tier],
            "textured_area_sf": round(textured_area),
            "smooth_area_sf": round(smooth_area),
            "specialty_drywall_sf": round(specialty_drywall)
        }
        
    def _calculate_ceiling_finishes(self, square_footage, tier):
        """Calculate ceiling finish quantities"""
        # Specialty ceiling percentages by tier
        specialty_ceiling_pct = {
            "Premium": {
                "coffered": 0,
                "tray": 0.05
            },
            "Luxury": {
                "coffered": 0.07,
                "tray": 0.15
            },
            "Ultra-Luxury": {
                "coffered": 0.15,
                "tray": 0.25,
                "specialty": 0.1
            }
        }
        
        result = {}
        
        # Calculate specialty ceiling areas
        for ceiling_type, pct in specialty_ceiling_pct[tier].items():
            result[f"{ceiling_type}_ceiling_sf"] = round(square_footage * pct)
            
        return result
        
    def _calculate_accessories(self, square_footage, tier):
        """Calculate drywall accessory quantities"""
        # Corner bead linear feet per SF of house
        corner_bead_factor = {
            "Premium": 0.08,
            "Luxury": 0.12,
            "Ultra-Luxury": 0.16
        }
        
        # Control joint linear feet per SF of house
        control_joint_factor = {
            "Premium": 0.02,
            "Luxury": 0.04,
            "Ultra-Luxury": 0.06
        }
        
        # Calculate accessories
        corner_bead = square_footage * corner_bead_factor[tier]
        control_joint = square_footage * control_joint_factor[tier]
        
        # Calculate mud and tape
        mud_coverage = 300  # SF per gallon
        drywall_factor = {
            "Premium": 2.8,
            "Luxury": 3.1,
            "Ultra-Luxury": 3.5
        }
        mud_gallons = (square_footage * drywall_factor[tier]) / mud_coverage
        
        tape_lf_per_sf = 0.15
        tape_length = square_footage * drywall_factor[tier] * tape_lf_per_sf
        
        return {
            "corner_bead_lf": round(corner_bead),
            "control_joint_lf": round(control_joint),
            "drywall_mud_gallons": round(mud_gallons),
            "drywall_tape_lf": round(tape_length)
        }