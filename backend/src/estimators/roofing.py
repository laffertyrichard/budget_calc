import math
import logging

logger = logging.getLogger(__name__)

class RoofingEstimator:
    """Handles roofing quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate roofing quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate roof area and underlayment
        results.update(self._calculate_roof_area(square_footage, tier))
        
        # Calculate roof components
        results.update(self._calculate_components(square_footage, tier))
        
        # Calculate drainage system
        results.update(self._calculate_drainage(square_footage, tier))
        
        return results
        
    def _calculate_roof_area(self, square_footage, tier):
        """Calculate roof area and underlayment"""
        # Roof area ratio (roof area to house footprint)
        roof_ratio = {
            "Premium": 1.2,
            "Luxury": 1.35,
            "Ultra-Luxury": 1.5
        }
        
        # Underlayment layers
        underlayment_layers = {
            "Premium": 1,
            "Luxury": 2,
            "Ultra-Luxury": 2
        }
        
        # Calculate roof area
        roof_area = square_footage * roof_ratio[tier]
        
        # Calculate underlayment (includes 15% for overlaps)
        underlayment_area = roof_area * 1.15 * underlayment_layers[tier]
        
        # Roof insulation area (typically just the footprint)
        ceiling_insulation_area = square_footage
        
        # Insulation R-value by tier
        insulation_r_value = {
            "Premium": 38,
            "Luxury": 49,
            "Ultra-Luxury": 60
        }
        
        return {
            "roof_area_sf": round(roof_area),
            "underlayment_area_sf": round(underlayment_area),
            "ceiling_insulation_sf": round(ceiling_insulation_area),
            "insulation_r_value": insulation_r_value[tier]
        }
        
    def _calculate_components(self, square_footage, tier):
        """Calculate roof component quantities"""
        # Get roof area
        roof_area = self._calculate_roof_area(square_footage, tier)["roof_area_sf"]
        
        # Component factors (per roof square foot)
        ridge_vent_factor = {
            "Premium": 0.03,
            "Luxury": 0.05,
            "Ultra-Luxury": 0.07
        }
        
        drip_edge_factor = {
            "Premium": 0.12,
            "Luxury": 0.16,
            "Ultra-Luxury": 0.2
        }
        
        fascia_factor = {
            "Premium": 0.12,
            "Luxury": 0.16,
            "Ultra-Luxury": 0.2
        }
        
        soffit_factor = {
            "Premium": 0.15,
            "Luxury": 0.22,
            "Ultra-Luxury": 0.3
        }
        
        # Calculate components
        ridge_vent = roof_area * ridge_vent_factor[tier]
        drip_edge = roof_area * drip_edge_factor[tier]
        fascia = square_footage * fascia_factor[tier]  # Based on house footprint
        soffit = square_footage * soffit_factor[tier]  # Based on house footprint
        
        return {
            "ridge_vent_lf": round(ridge_vent),
            "drip_edge_lf": round(drip_edge),
            "fascia_lf": round(fascia),
            "soffit_sf": round(soffit)
        }
        
    def _calculate_drainage(self, square_footage, tier):
        """Calculate roof drainage system quantities"""
        # Approximate perimeter of house
        perimeter = 4 * math.sqrt(square_footage)
        
        # Gutters typically cover about 85% of perimeter
        gutters = perimeter * 0.85
        
        # One downspout roughly every 40 feet of gutter
        downspouts = gutters / 40
        
        # Additional drainage components for luxury tiers
        result = {
            "gutters_lf": round(gutters),
            "downspouts_count": round(downspouts)
        }
        
        # Add specialty drainage items for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            result["rain_chains"] = 1 if tier == "Luxury" else 2
            result["decorative_scuppers"] = 0 if tier == "Luxury" else math.ceil(downspouts / 3)
            
        return result