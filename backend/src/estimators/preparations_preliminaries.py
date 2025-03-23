import math
import logging

logger = logging.getLogger(__name__)

class PreparationsPreliminariesEstimator:
    """Handles preparations and preliminaries quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate preparations and preliminaries quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get project duration from kwargs or estimate based on square footage
        project_duration_months = kwargs.get('project_duration_months')
        if not project_duration_months:
            # Estimate project duration based on square footage and tier
            project_duration_months = self._estimate_project_duration(square_footage, tier)
            
        results = {}
        
        # Calculate site preparation
        results.update(self._calculate_site_preparation(square_footage, tier))
        
        # Calculate temporary facilities
        results.update(self._calculate_temporary_facilities(square_footage, tier, project_duration_months))
        
        # Calculate project management
        results.update(self._calculate_project_management(square_footage, tier, project_duration_months))
        
        # Calculate additional labor roles
        results.update(self._calculate_additional_labor(square_footage, tier, project_duration_months))
        
        # Calculate permits and fees
        results.update(self._calculate_permits_fees(square_footage, tier))
        
        # Calculate safety and protection
        results.update(self._calculate_safety_protection(square_footage, tier, project_duration_months))
        
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
        
    def _calculate_site_preparation(self, square_footage, tier):
        """Calculate site preparation quantities"""
        # Calculate lot size (rough approximation)
        lot_size_multiplier = {
            "Premium": 3.0,
            "Luxury": 4.0,
            "Ultra-Luxury": 5.0
        }
        
        house_footprint = square_footage / 1.5  # Assuming 1.5 stories average
        lot_size = house_footprint * lot_size_multiplier[tier]
        
        # Calculate construction fencing (perimeter of lot plus 20%)
        lot_perimeter = 4 * math.sqrt(lot_size)
        construction_fencing = lot_perimeter * 1.2
        
        # Calculate site clearing area
        site_clearing_factor = {
            "Premium": 1.2,  # 120% of house footprint
            "Luxury": 1.5,   # 150% of house footprint
            "Ultra-Luxury": 2.0  # 200% of house footprint
        }
        
        site_clearing_area = house_footprint * site_clearing_factor[tier]
        
        # Calculate erosion control linear feet (typically around perimeter)
        erosion_control_lf = lot_perimeter
        
        # Other site preparation items
        result = {
            "construction_fencing_lf": round(construction_fencing),
            "site_clearing_sf": round(site_clearing_area),
            "erosion_control_lf": round(erosion_control_lf),
            "construction_entrance": 1,
            "tree_protection": round(lot_size / 10000)  # 1 per 10,000 sq ft of lot
        }
        
        # Add additional items for larger/luxury projects
        if tier in ["Luxury", "Ultra-Luxury"]:
            result["construction_signage"] = 1
            result["temporary_roads_sf"] = round(lot_size * 0.05)  # 5% of lot for temp roads
            
        return result
        
    def _calculate_temporary_facilities(self, square_footage, tier, project_duration_months):
        """Calculate temporary facilities quantities"""
        # Number of portable toilets based on project size
        if square_footage < 5000:
            portable_toilets = 1
        elif square_footage < 10000:
            portable_toilets = 2
        else:
            portable_toilets = 3
            
        # Dumpster calculation
        # Roughly 1 dumpster per 2000 sq ft of construction
        dumpster_pulls = math.ceil(square_footage / 2000) * project_duration_months
        
        # Field office based on tier
        field_office_sf = 0
        if tier == "Premium":
            field_office_sf = 0 if square_footage < 5000 else 150
        elif tier == "Luxury":
            field_office_sf = 200
        else:  # Ultra-Luxury
            field_office_sf = 400
            
        # Calculate temporary utilities
        temp_utilities_months = project_duration_months
        
        return {
            "portable_toilets": portable_toilets,
            "portable_toilet_months": portable_toilets * project_duration_months,
            "dumpster_pulls": dumpster_pulls,
            "field_office_sf": field_office_sf,
            "field_office_months": 0 if field_office_sf == 0 else project_duration_months,
            "temp_electrical_months": temp_utilities_months,
            "temp_water_months": temp_utilities_months
        }
        
    def _calculate_project_management(self, square_footage, tier, project_duration_months):
        """Calculate project management quantities"""
        # Project management level varies by tier
        if tier == "Premium":
            superintendent_hours_per_week = 15
            project_manager_hours_per_week = 5
        elif tier == "Luxury":
            superintendent_hours_per_week = 25
            project_manager_hours_per_week = 10
        else:  # Ultra-Luxury
            superintendent_hours_per_week = 40
            project_manager_hours_per_week = 15
            
        # Calculate total hours for project duration
        weeks = project_duration_months * 4.33  # Approximate weeks per month
        superintendent_hours = superintendent_hours_per_week * weeks
        project_manager_hours = project_manager_hours_per_week * weeks
        
        # Calculate meeting quantities
        client_meetings = project_duration_months * 2  # Two client meetings per month
        subcontractor_meetings = project_duration_months * 4  # Weekly subcontractor meetings
        
        return {
            "superintendent_hours": round(superintendent_hours),
            "project_manager_hours": round(project_manager_hours),
            "client_meetings": round(client_meetings),
            "subcontractor_meetings": round(subcontractor_meetings)
        }
        
    def _calculate_additional_labor(self, square_footage, tier, project_duration_months):
        """Calculate additional labor roles quantities"""
        # Labor hours per week based on tier
        labor_hours_per_week = {
            "Project Administrator": {"Premium": 5, "Luxury": 10, "Ultra-Luxury": 15},
            "Construction Manager": {"Premium": 10, "Luxury": 20, "Ultra-Luxury": 30},
            "Carpenter / Tool Person": {"Premium": 20, "Luxury": 30, "Ultra-Luxury": 40},
            "Construction Site Tech": {"Premium": 10, "Luxury": 15, "Ultra-Luxury": 20}
        }
        
        # Calculate total hours for project duration
        weeks = project_duration_months * 4.33  # Approximate weeks per month
        
        additional_labor = {}
        for role, hours in labor_hours_per_week.items():
            total_hours = hours[tier] * weeks
            additional_labor[f"{role.lower().replace(' ', '_')}_hours"] = round(total_hours)
            additional_labor[f"{role.lower().replace(' ', '_')}_months"] = project_duration_months
        
        return additional_labor
        
    def _calculate_permits_fees(self, square_footage, tier):
        """Calculate permit and fee quantities (not actual costs)"""
        # These are permit/inspection quantities, not costs
        
        # Core permits (these are counts, not dollar values)
        permits = {
            "building_permit": 1,
            "mechanical_permit": 1,
            "electrical_permit": 1,
            "plumbing_permit": 1
        }
        
        # Calculate inspection quantities
        foundation_inspections = 2
        framing_inspections = 2
        mechanical_inspections = 3
        electrical_inspections = 3
        plumbing_inspections = 3
        final_inspections = 2
        
        # Additional inspections for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            # More complex projects require more inspections
            foundation_inspections += 1
            framing_inspections += 1
            mechanical_inspections += 1
            electrical_inspections += 1
            plumbing_inspections += 1
            
        # Even more inspections for ultra-luxury
        if tier == "Ultra-Luxury":
            foundation_inspections += 1
            framing_inspections += 1
            
        inspections = {
            "foundation_inspections": foundation_inspections,
            "framing_inspections": framing_inspections,
            "mechanical_inspections": mechanical_inspections,
            "electrical_inspections": electrical_inspections,
            "plumbing_inspections": plumbing_inspections,
            "final_inspections": final_inspections
        }
        
        # Combine all permit data
        permits.update(inspections)
        
        # Add specialty permits for luxury tiers
        if tier in ["Luxury", "Ultra-Luxury"]:
            permits["pool_permit"] = 1
            permits["landscape_permit"] = 1
            
        return permits
        
    def _calculate_safety_protection(self, square_footage, tier, project_duration_months):
        """Calculate safety and protection quantities"""
        # Safety equipment calculation based on project size
        safety_equipment_factor = {
            "Premium": 0.5,  # Units per 1000 sq ft
            "Luxury": 0.7,
            "Ultra-Luxury": 1.0
        }
        
        # Calculate safety equipment units
        safety_equipment = (square_footage / 1000) * safety_equipment_factor[tier]
        
        # Dust control based on project duration
        dust_barriers_sf = square_footage * 0.15  # About 15% of project area
        
        # Floor protection based on project area
        floor_protection_sf = square_footage * 0.5  # Protect 50% of floors during construction
        
        # Window protection based on window quantity
        # Assume 0.008 windows per sq ft as in other estimators
        window_count = round(square_footage * 0.008)
        window_protection = window_count
        
        return {
            "safety_equipment_units": round(safety_equipment),
            "dust_barriers_sf": round(dust_barriers_sf),
            "floor_protection_sf": round(floor_protection_sf),
            "window_protection_units": window_protection,
            "first_aid_kits": math.ceil(project_duration_months / 3)  # Replace every 3 months
        }