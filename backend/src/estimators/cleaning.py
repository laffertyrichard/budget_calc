import logging

logger = logging.getLogger(__name__)

class CleaningEstimator:
    """Handles cleaning quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate cleaning quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get project duration from kwargs or estimate based on square footage
        project_duration_months = kwargs.get('project_duration_months')
        if not project_duration_months:
            # Estimate project duration based on square footage and tier
            project_duration_months = self._estimate_project_duration(square_footage, tier)
            
        results = {}
        
        # Calculate rough cleaning
        results.update(self._calculate_rough_cleaning(square_footage, tier, project_duration_months))
        
        # Calculate final cleaning
        results.update(self._calculate_final_cleaning(square_footage, tier))
        
        # Calculate specialty cleaning
        results.update(self._calculate_specialty_cleaning(square_footage, tier))
        
        return results
        
    def _estimate_project_duration(self, square_footage, tier):
        """Estimate project duration in months based on square footage and tier"""
        # Base months for minimum square footage
        base_months = {
            "Premium": 8,
            "Luxury": 10,
            "Ultra-Luxury": 12
        }
        
        # Additional months per 1000 square feet above baseline
        additional_months_per_1000sf = {
            "Premium": 0.5,
            "Luxury": 0.6,
            "Ultra-Luxury": 0.8
        }
        
        # Baseline square footage
        baseline_sf = {
            "Premium": 4000,
            "Luxury": 6000,
            "Ultra-Luxury": 10000
        }
        
        # Calculate estimated duration
        duration = base_months[tier]
        if square_footage > baseline_sf[tier]:
            additional_sf = square_footage - baseline_sf[tier]
            duration += (additional_sf / 1000) * additional_months_per_1000sf[tier]
            
        return round(duration)
        
    def _calculate_rough_cleaning(self, square_footage, tier, project_duration_months):
        """Calculate rough cleaning quantities"""
        # Rough cleaning frequency per month based on tier
        rough_cleaning_frequency = {
            "Premium": 2,    # Twice a month
            "Luxury": 4,     # Weekly
            "Ultra-Luxury": 8  # Twice a week
        }
        
        # Calculate labor hours per cleaning
        labor_hours_per_cleaning = square_footage / 2000  # Approx 1 hour per 2000 sq ft
        
        # Calculate dumpsters needed for construction waste
        construction_waste_factor = {
            "Premium": 0.15,   # CY per 100 sq ft
            "Luxury": 0.2,
            "Ultra-Luxury": 0.25
        }
        
        construction_waste_cy = (square_footage / 100) * construction_waste_factor[tier]
        dumpster_capacity_cy = 20  # Standard 20 CY dumpster
        dumpsters_needed = construction_waste_cy / dumpster_capacity_cy
        
        return {
            "rough_cleaning_occurrences": round(rough_cleaning_frequency[tier] * project_duration_months),
            "rough_cleaning_labor_hours": round(labor_hours_per_cleaning * rough_cleaning_frequency[tier] * project_duration_months),
            "construction_waste_cy": round(construction_waste_cy),
            "construction_dumpsters": round(dumpsters_needed)
        }
        
    def _calculate_final_cleaning(self, square_footage, tier):
        """Calculate final cleaning quantities"""
        # Final cleaning labor hours based on square footage and tier
        final_cleaning_factor = {
            "Premium": 0.025,  # Hours per sq ft
            "Luxury": 0.03,
            "Ultra-Luxury": 0.04
        }
        
        # Calculate final cleaning labor hours
        final_cleaning_hours = square_footage * final_cleaning_factor[tier]
        
        # Window cleaning based on window count
        # Assume 0.008 windows per sq ft as in other estimators
        window_count = round(square_footage * 0.008)
        
        # Window cleaning factor based on tier
        window_cleaning_factor = {
            "Premium": 0.5,  # Hours per window
            "Luxury": 0.75,
            "Ultra-Luxury": 1.0
        }
        
        window_cleaning_hours = window_count * window_cleaning_factor[tier]
        
        return {
            "final_cleaning_sf": square_footage,
            "final_cleaning_labor_hours": round(final_cleaning_hours),
            "window_cleaning_count": window_count,
            "window_cleaning_labor_hours": round(window_cleaning_hours)
        }
        
    def _calculate_specialty_cleaning(self, square_footage, tier):
        """Calculate specialty cleaning quantities"""
        result = {}
        
        # Floor cleaning (hardwood, tile, etc.)
        floor_cleaning_sf = square_footage * 0.7  # Assume 70% of space has flooring needing special cleaning
        result["floor_cleaning_sf"] = round(floor_cleaning_sf)
        
        # Power washing exterior
        power_washing_sf = square_footage * 0.3  # Approx 30% of square footage for exterior surface area
        result["power_washing_sf"] = round(power_washing_sf)
        
        # Add specialty cleaning for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            # Chandelier/fixture cleaning
            fixture_count = round(square_footage * 0.002)  # 1 fixture per 500 sq ft
            result["fixture_cleaning_count"] = fixture_count
            
            # Countertop/stone sealing
            countertop_area = round(square_footage * 0.04)  # Approx 4% of sq ft for countertops
            result["countertop_sealing_sf"] = countertop_area
            
            # Cabinet cleaning and detailing
            cabinet_linear_feet = round(square_footage * 0.02)  # Approx 0.02 LF per sq ft
            result["cabinet_cleaning_lf"] = cabinet_linear_feet
            
        # Add even more specialty cleaning for ultra-luxury
        if tier == "Ultra-Luxury":
            # Specialized surface treatments
            result["specialty_surface_sf"] = round(square_footage * 0.1)
            
            # Glass balustrade cleaning
            result["glass_balustrade_cleaning_sf"] = round(square_footage * 0.02)
            
            # Post-construction air quality management
            result["air_scrubber_days"] = 5
            
        return result