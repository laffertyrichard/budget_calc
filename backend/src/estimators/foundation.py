import math
import logging

logger = logging.getLogger(__name__)

class FoundationEstimator:
    """Handles foundation quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate foundation quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate concrete volumes
        results.update(self._calculate_concrete(square_footage, tier))
        
        # Calculate waterproofing
        results.update(self._calculate_waterproofing(square_footage, tier))
        
        return results
        
    def _calculate_concrete(self, square_footage, tier):
        """Calculate concrete quantities"""
        foundationFootprint = square_footage * 1.1  # Foundation is typically 10% larger than house footprint
        perimeter = 4 * math.sqrt(foundationFootprint)
        
        # Tier-specific parameters
        slab_thickness_inches = {'Premium': 4, 'Luxury': 5, 'Ultra-Luxury': 6}
        footing_width_inches = {'Premium': 12, 'Luxury': 16, 'Ultra-Luxury': 24}
        footing_depth_inches = {'Premium': 18, 'Luxury': 24, 'Ultra-Luxury': 30}
        wall_thickness_inches = {'Premium': 8, 'Luxury': 10, 'Ultra-Luxury': 12}
        wall_height = 9  # feet - same for all tiers for this example
        
        # Calculate volumes in cubic yards
        slab_volume = (foundationFootprint * slab_thickness_inches[tier] / 12) / 27
        footing_volume = (perimeter * (footing_width_inches[tier] / 12) * (footing_depth_inches[tier] / 12)) / 27
        wall_volume = (perimeter * wall_height * (wall_thickness_inches[tier] / 12)) / 27
        
        return {
            'slab_concrete_cy': round(slab_volume),
            'footing_concrete_cy': round(footing_volume),
            'foundation_wall_cy': round(wall_volume),
            'total_concrete_cy': round(slab_volume + footing_volume + wall_volume)
        }
        
    def _calculate_waterproofing(self, square_footage, tier):
        """Calculate waterproofing quantities"""
        # Waterproofing factors by tier
        waterproofing_factor = {'Premium': 0.4, 'Luxury': 0.5, 'Ultra-Luxury': 0.6}
        drainage_factor = {'Premium': 0.1, 'Luxury': 0.15, 'Ultra-Luxury': 0.2}
        roof_drainage_factor = {'Premium': 0.05, 'Luxury': 0.08, 'Ultra-Luxury': 0.1}
        sump_pumps = {'Premium': 1, 'Luxury': 2, 'Ultra-Luxury': 3}
        
        return {
            'foundation_waterproofing_sf': round(square_footage * waterproofing_factor[tier]),
            'below_grade_drainage_lf': round(square_footage * drainage_factor[tier]),
            'roof_drainage_lf': round(square_footage * roof_drainage_factor[tier]),
            'sump_pumps': sump_pumps[tier]
        }