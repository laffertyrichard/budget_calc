import logging

logger = logging.getLogger(__name__)

class PaintingCoatingsEstimator:
    """Handles paint and coatings quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate paint and coating quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate wall and ceiling paint
        results.update(self._calculate_wall_ceiling_paint(square_footage, tier))
        
        # Calculate trim and door paint
        results.update(self._calculate_trim_door_paint(square_footage, tier))
        
        # Calculate specialty finishes
        results.update(self._calculate_specialty_finishes(square_footage, tier))
        
        # Calculate exterior paint
        results.update(self._calculate_exterior_paint(square_footage, tier))
        
        return results
        
    def _calculate_wall_ceiling_paint(self, square_footage, tier):
        """Calculate wall and ceiling paint quantities"""
        # SF of paintable wall per SF of house
        wall_area_factor = {
            "Premium": 2.2,
            "Luxury": 2.4,
            "Ultra-Luxury": 2.7
        }
        
        # SF of paintable ceiling per SF of house
        ceiling_area_factor = {
            "Premium": 0.9,
            "Luxury": 1.0,
            "Ultra-Luxury": 1.1
        }
        
        # Primer and paint coats
        primer_coats = 1  # Same for all tiers
        paint_coats = 2 if tier != "Ultra-Luxury" else 3  # Extra coat for Ultra-Luxury
        
        # Paint coverage (SF per gallon)
        coverage = 350  # Same for all tiers
        
        # Calculate paintable areas
        wall_area = square_footage * wall_area_factor[tier]
        ceiling_area = square_footage * ceiling_area_factor[tier]
        total_paintable_area = wall_area + ceiling_area
        
        # Calculate paint gallons
        wall_ceiling_paint = (
            (total_paintable_area * primer_coats) / coverage +
            (total_paintable_area * paint_coats) / coverage
        )
        
        return {
            "wall_area_sf": round(wall_area),
            "ceiling_area_sf": round(ceiling_area),
            "total_paintable_area_sf": round(total_paintable_area),
            "wall_ceiling_primer_gallons": round((total_paintable_area * primer_coats) / coverage),
            "wall_ceiling_paint_gallons": round((total_paintable_area * paint_coats) / coverage),
            "total_wall_ceiling_gallons": round(wall_ceiling_paint)
        }
        
    def _calculate_trim_door_paint(self, square_footage, tier):
        """Calculate trim and door paint quantities"""
        # LF of trim per SF of house
        trim_factor = {
            "Premium": 0.8,
            "Luxury": 0.9,
            "Ultra-Luxury": 1.0
        }
        
        # Estimate interior door count (based on room count)
        rooms_per_sf = 1/300  # Approx. one room per 300 SF
        doors_per_room = 1.2  # Approx. 1.2 doors per room
        interior_door_count = square_footage * rooms_per_sf * doors_per_room
        
        # Trim and doors that can be painted with one gallon
        trim_doors_per_gallon = {
            "Premium": 15,
            "Luxury": 12,
            "Ultra-Luxury": 10
        }
        
        # Primer and paint coats
        primer_coats = 1  # Same for all tiers
        paint_coats = 2 if tier != "Ultra-Luxury" else 3  # Extra coat for Ultra-Luxury
        
        # Calculate trim linear feet
        trim_lf = square_footage * trim_factor[tier]
        
        # Calculate paint gallons
        # Approximate 30 LF of trim equals 1 door for paint coverage
        trim_door_equivalent = (trim_lf / 30) + interior_door_count
        trim_door_paint = (
            trim_door_equivalent / trim_doors_per_gallon[tier] *
            (primer_coats + paint_coats)
        )
        
        return {
            "interior_door_count": round(interior_door_count),
            "trim_lf": round(trim_lf),
            "trim_door_primer_gallons": round(trim_door_equivalent / trim_doors_per_gallon[tier] * primer_coats),
            "trim_door_paint_gallons": round(trim_door_equivalent / trim_doors_per_gallon[tier] * paint_coats),
            "total_trim_door_gallons": round(trim_door_paint)
        }
        
    def _calculate_specialty_finishes(self, square_footage, tier):
        """Calculate specialty finish quantities"""
        result = {}
        
        # Calculate total paintable area from wall/ceiling function
        total_paintable_area = self._calculate_wall_ceiling_paint(square_footage, tier)["total_paintable_area_sf"]
        
        # Specialty finish percentage by tier
        specialty_finish_pct = {
            "Premium": 0.05,
            "Luxury": 0.15,
            "Ultra-Luxury": 0.25
        }
        
        # Calculate specialty finish area
        specialty_finish_area = total_paintable_area * specialty_finish_pct[tier]
        result["specialty_finish_area_sf"] = round(specialty_finish_area)
        
        # Add specific specialty finishes by tier
        if tier == "Luxury":
            result["decorative_glaze_gallons"] = round(specialty_finish_area / 300)
        elif tier == "Ultra-Luxury":
            result["decorative_glaze_gallons"] = round(specialty_finish_area / 250)
            result["venetian_plaster_area_sf"] = round(total_paintable_area * 0.1)
            result["metallic_finish_area_sf"] = round(total_paintable_area * 0.05)
            
        return result
        
    def _calculate_exterior_paint(self, square_footage, tier):
        """Calculate exterior paint quantities"""
        # Exterior paint gallons per SF of house
        exterior_paint_factor = {
            "Premium": 0.005,  # 1 gallon per 200 SF
            "Luxury": 0.006,   # 1 gallon per 167 SF
            "Ultra-Luxury": 0.0075  # 1 gallon per 133 SF
        }
        
        # Exterior wall area is typically 2-3x the square footage for 2-story homes
        exterior_wall_factor = {
            "Premium": 2.0,
            "Luxury": 2.5,
            "Ultra-Luxury": 3.0
        }
        
        # Calculate exterior paintable area
        exterior_wall_area = square_footage * exterior_wall_factor[tier]
        
        # Calculate exterior paint gallons (primer + paint coats)
        # Premium: 1 primer coat, 2 paint coats
        # Luxury: 1 primer coat, 2 paint coats
        # Ultra-Luxury: 1 primer coat, 3 paint coats
        primer_coats = 1
        paint_coats = 2 if tier != "Ultra-Luxury" else 3
        
        # Paint coverage (SF per gallon)
        coverage = 350  # Same for all tiers
        
        exterior_primer_gallons = (exterior_wall_area * primer_coats) / coverage
        exterior_paint_gallons = (exterior_wall_area * paint_coats) / coverage
        
        # Add specialty exterior coatings for luxury tiers
        result = {
            "exterior_wall_area_sf": round(exterior_wall_area),
            "exterior_primer_gallons": round(exterior_primer_gallons),
            "exterior_paint_gallons": round(exterior_paint_gallons),
            "total_exterior_gallons": round(exterior_primer_gallons + exterior_paint_gallons)
        }
        
        # Add specialty exterior coatings for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            # Special trim coatings
            trim_area = exterior_wall_area * 0.15  # About 15% of wall area is trim
            result["exterior_trim_area_sf"] = round(trim_area)
            result["exterior_trim_paint_gallons"] = round(trim_area / 300)  # Lower coverage for trim paint
            
            # Specialty coatings for ultra-luxury
            if tier == "Ultra-Luxury":
                result["exterior_stain_gallons"] = round(exterior_wall_area * 0.3 / 300)  # 30% might be stained
                result["exterior_sealer_gallons"] = round(exterior_wall_area * 0.4 / 400)  # 40% needs sealer
                
        return result