import logging

logger = logging.getLogger(__name__)

class ThermalFireSuppressionEstimator:
    """Handles thermal insulation and fire suppression quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate thermal insulation and fire suppression quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate thermal insulation quantities (from the original insulation module)
        results.update(self._calculate_thermal_insulation(square_footage, tier))
        
        # Calculate fire suppression quantities
        results.update(self._calculate_fire_suppression(square_footage, tier))
        
        return results
        
    def _calculate_thermal_insulation(self, square_footage, tier):
        """Calculate thermal insulation quantities"""
        # Wall insulation SF per SF of house
        wall_insulation_factor = {
            "Premium": 0.85,
            "Luxury": 0.95,
            "Ultra-Luxury": 1.05
        }
        
        # Ceiling insulation SF per SF of house (typically 1:1)
        ceiling_insulation_factor = 1.0  # Same for all tiers
        
        # Insulation R-values by tier
        wall_r_value = {
            "Premium": 19,
            "Luxury": 21,
            "Ultra-Luxury": 24
        }
        
        ceiling_r_value = {
            "Premium": 38,
            "Luxury": 49,
            "Ultra-Luxury": 60
        }
        
        # Calculate insulation areas
        wall_insulation = square_footage * wall_insulation_factor[tier]
        ceiling_insulation = square_footage * ceiling_insulation_factor
        
        # Calculate specialty insulation
        specialty_results = {}
        
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
        specialty_results["rigid_insulation_sf"] = round(square_footage * rigid_insulation_pct[tier])
        specialty_results["acoustic_insulation_sf"] = round(square_footage * acoustic_insulation_pct[tier])
        
        # Add radiant barrier for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            radiant_barrier_pct = 0.5 if tier == "Luxury" else 1.0
            specialty_results["radiant_barrier_sf"] = round(square_footage * radiant_barrier_pct)
        
        # Add thermal break tape for ultra-luxury
        if tier == "Ultra-Luxury":
            specialty_results["thermal_break_tape_lf"] = round(square_footage * 0.8)
        
        # Calculate weatherproofing quantities
        weatherproofing_results = self._calculate_weatherproofing(square_footage, tier, wall_insulation)
        
        # Combine all thermal insulation results
        results = {
            "wall_insulation_sf": round(wall_insulation),
            "wall_r_value": wall_r_value[tier],
            "ceiling_insulation_sf": round(ceiling_insulation),
            "ceiling_r_value": ceiling_r_value[tier]
        }
        
        results.update(specialty_results)
        results.update(weatherproofing_results)
        
        return results
    
    def _calculate_weatherproofing(self, square_footage, tier, wall_area):
        """Calculate weatherproofing quantities"""
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
    
    def _calculate_fire_suppression(self, square_footage, tier):
        """
        Calculate fire suppression system quantities
        
        Fire suppression requirements vary by tier:
        - Premium: Basic coverage in key areas
        - Luxury: Full coverage with standard components
        - Ultra-Luxury: Full coverage with enhanced components and backup systems
        """
        # Determine if fire suppression is required
        # For this estimator, we'll assume all tiers have some level of fire suppression
        
        # Calculate number of sprinkler heads
        # Industry standard is approximately one head per 100-200 sq ft depending on coverage
        coverage_area_per_head = {
            "Premium": 200,  # 1 head per 200 sq ft (minimum coverage)
            "Luxury": 150,   # 1 head per 150 sq ft (standard coverage)
            "Ultra-Luxury": 100  # 1 head per 100 sq ft (enhanced coverage)
        }
        
        # Percentage of house covered by sprinklers
        coverage_percentage = {
            "Premium": 0.7,   # 70% coverage (key areas only)
            "Luxury": 0.9,    # 90% coverage
            "Ultra-Luxury": 1.0  # 100% coverage
        }
        
        # Calculate covered area
        covered_area = square_footage * coverage_percentage[tier]
        
        # Calculate sprinkler head count
        sprinkler_heads = covered_area / coverage_area_per_head[tier]
        
        # Calculate piping (linear feet)
        # Roughly 0.7-1.0 LF of pipe per 1 SF of covered area
        piping_factor = {
            "Premium": 0.7,
            "Luxury": 0.85,
            "Ultra-Luxury": 1.0
        }
        
        fire_suppression_piping = covered_area * piping_factor[tier]
        
        # Calculate main components
        results = {
            "fire_sprinkler_heads": round(sprinkler_heads),
            "fire_suppression_piping_lf": round(fire_suppression_piping),
            "fire_suppression_covered_area_sf": round(covered_area)
        }
        
        # Control components (one riser assembly per system)
        results["fire_riser_assembly"] = 1
        
        # Flow switches and control valves (one per floor plus one for the system)
        floors = max(1, round(square_footage / 3000))  # Estimate floor count
        results["flow_switches"] = floors + 1
        results["control_valves"] = floors + 1
        
        # Add enhanced components for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            results["fire_suppression_monitor"] = 1  # Electronic monitoring system
            results["inspector_test_connections"] = floors  # One test connection per floor
            
        # Add high-end components for ultra-luxury
        if tier == "Ultra-Luxury":
            results["backup_water_supply"] = 1  # Backup water tank or pump
            results["concealed_sprinkler_heads"] = round(sprinkler_heads * 0.7)  # 70% of heads are concealed type
            results["fire_suppression_accent_finishes"] = round(sprinkler_heads * 0.3)  # 30% of heads get decorative finishes
        
        return results