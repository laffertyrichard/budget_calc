import logging

logger = logging.getLogger(__name__)

class StructuralEstimator:
    """Handles structural quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate structural quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate framing lumber
        results.update(self._calculate_framing(square_footage, tier))
        
        # Calculate structural steel
        results.update(self._calculate_steel(square_footage, tier))
        
        # Calculate sheathing and panels
        results.update(self._calculate_sheathing(square_footage, tier))
        
        return results
        
    def _calculate_framing(self, square_footage, tier):
        """Calculate framing quantities"""
        # Board feet calculations
        board_feet_per_sf = {
            "Premium": 2.8,
            "Luxury": 3.2,
            "Ultra-Luxury": 3.6
        }
        
        engineered_pct = {
            "Premium": 0.15,
            "Luxury": 0.25,
            "Ultra-Luxury": 0.35
        }
        
        steel_pct = {
            "Premium": 0.05,
            "Luxury": 0.15,
            "Ultra-Luxury": 0.25
        }
        
        # Calculate total board feet and breakdown
        total_board_feet = square_footage * board_feet_per_sf[tier]
        conventional_lumber = total_board_feet * (1 - engineered_pct[tier] - steel_pct[tier])
        engineered_lumber = total_board_feet * engineered_pct[tier]
        steel_framing_equiv = total_board_feet * steel_pct[tier]
        
        # Stud calculation
        wall_linear_feet = 4 * (square_footage ** 0.5) + (square_footage * 0.15)  # Perimeter + interior walls
        stud_spacing_inches = 16 if tier != "Ultra-Luxury" else 12
        studs_per_lf = 12 / (stud_spacing_inches / 12)  # studs per linear foot
        stud_quantity = wall_linear_feet * studs_per_lf
        
        return {
            "conventional_lumber_bf": round(conventional_lumber),
            "engineered_lumber_bf": round(engineered_lumber),
            "steel_framing_equivalent_bf": round(steel_framing_equiv),
            "stud_quantity": round(stud_quantity),
            "stud_spacing_inches": stud_spacing_inches,
            "wall_linear_feet": round(wall_linear_feet)
        }
        
    def _calculate_steel(self, square_footage, tier):
        """Calculate structural steel quantities"""
        # Board feet from framing calculations
        board_feet_per_sf = {
            "Premium": 2.8,
            "Luxury": 3.2,
            "Ultra-Luxury": 3.6
        }
        
        steel_pct = {
            "Premium": 0.05,
            "Luxury": 0.15,
            "Ultra-Luxury": 0.25
        }
        
        total_board_feet = square_footage * board_feet_per_sf[tier]
        steel_framing_equiv = total_board_feet * steel_pct[tier]
        
        # Convert to actual steel weights (0.5 lbs per board foot equivalent)
        steel_framing_weight = steel_framing_equiv * 0.5
        
        # Calculate connections
        connections_per_sf = {
            "Premium": 0.004,
            "Luxury": 0.006,
            "Ultra-Luxury": 0.008
        }
        
        connections = square_footage * connections_per_sf[tier]
        
        return {
            "steel_framing_weight_lbs": round(steel_framing_weight),
            "steel_connections": round(connections)
        }
        
    def _calculate_sheathing(self, square_footage, tier):
        """Calculate sheathing quantities"""
        # Sheathing SF per SF of house
        sheathing_factor = {
            "Premium": 2.1,
            "Luxury": 2.3,
            "Ultra-Luxury": 2.6
        }
        
        # Total sheathing
        sheathing_sf = square_footage * sheathing_factor[tier]
        
        # Breakdown by type (approximate percentages)
        roof_sheathing_pct = 0.4
        wall_sheathing_pct = 0.35
        floor_sheathing_pct = 0.25
        
        return {
            "total_sheathing_sf": round(sheathing_sf),
            "roof_sheathing_sf": round(sheathing_sf * roof_sheathing_pct),
            "wall_sheathing_sf": round(sheathing_sf * wall_sheathing_pct),
            "floor_sheathing_sf": round(sheathing_sf * floor_sheathing_pct)
        }