import logging

logger = logging.getLogger(__name__)

class PlumbingEstimator:
    """Handles plumbing quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def set_config(self, config):
        """Set configuration after initialization"""
        self.config = config
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate plumbing quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get bathroom counts from kwargs or use defaults
        primary_bath_count = kwargs.get('primary_bath_count', 2)
        secondary_bath_count = kwargs.get('secondary_bath_count', 3)
        powder_room_count = kwargs.get('powder_room_count', 2)
        
        results = {}
        
        # Calculate primary bathroom fixtures
        results.update(self._calculate_primary_bath(tier, primary_bath_count))
        
        # Calculate secondary bathroom fixtures
        results.update(self._calculate_secondary_bath(tier, secondary_bath_count))
        
        # Calculate powder room fixtures
        results.update(self._calculate_powder_room(tier, powder_room_count))
        
        # Calculate water heating system
        results.update(self._calculate_water_heating(square_footage, tier))
        
        # Calculate total fixtures (summary)
        results.update(self._calculate_total_fixtures(primary_bath_count, secondary_bath_count, powder_room_count, tier))
        
        return results
        
    def _calculate_primary_bath(self, tier, count):
        """Calculate primary bathroom fixture quantities with FIXED counts per bathroom"""
        if count <= 0:
            return {'primary_bath_count': 0}
            
        # Base quantities per bathroom - fixed values
        base_shower_valves = {"Premium": 1, "Luxury": 2, "Ultra-Luxury": 3}
        base_sinks = {"Premium": 2, "Luxury": 2, "Ultra-Luxury": 2}
        base_bathtubs = {"Premium": 1, "Luxury": 1, "Ultra-Luxury": 1}
        base_toilets = {"Premium": 1, "Luxury": 2, "Ultra-Luxury": 2}
        
        # Calculate quantities for all primary bathrooms
        shower_valves = count * base_shower_valves[tier]
        sinks = count * base_sinks[tier]
        bathtubs = count * base_bathtubs[tier]
        toilets = count * base_toilets[tier]
        
        return {
            "primary_bath_count": count,
            "primary_shower_valves": round(shower_valves),
            "primary_sinks": round(sinks),
            "primary_bathtubs": round(bathtubs),
            "primary_toilets": round(toilets)
        }
        
    def _calculate_secondary_bath(self, tier, count):
        """Calculate secondary bathroom fixture quantities with FIXED counts per bathroom"""
        if count <= 0:
            return {'secondary_bath_count': 0}
            
        # Base quantities per bathroom - fixed values
        base_shower_valves = 1  # One per bathroom for all tiers
        base_sinks = {"Premium": 1, "Luxury": 1, "Ultra-Luxury": 2}
        
        # Calculate quantities for all secondary bathrooms
        shower_valves = count * base_shower_valves
        sinks = count * base_sinks[tier]
        
        # 70% of secondary bathrooms have tubs
        bathtubs = count * 0.7
        
        # One toilet per secondary bathroom
        toilets = count
        
        return {
            "secondary_bath_count": count,
            "secondary_shower_valves": round(shower_valves),
            "secondary_sinks": round(sinks),
            "secondary_bathtubs": round(bathtubs),
            "secondary_toilets": round(toilets)
        }
        
    def _calculate_powder_room(self, tier, count):
        """Calculate powder room fixture quantities"""
        if count <= 0:
            return {'powder_room_count': 0}
            
        # Each powder room has one sink and one toilet
        return {
            "powder_room_count": count,
            "powder_room_sinks": count,
            "powder_room_toilets": count
        }
        
    def _calculate_water_heating(self, square_footage, tier):
        """Calculate water heating system quantities"""
        # Water heater count based on square footage
        if square_footage <= 3500:
            tankless_count = 1
        elif square_footage <= 7000:
            tankless_count = 2
        elif square_footage <= 10000:
            tankless_count = 3
        else:
            tankless_count = 4
            
        return {
            "tankless_water_heaters": tankless_count
        }
        
    def _calculate_total_fixtures(self, primary_bath_count, secondary_bath_count, powder_room_count, tier):
        """Calculate total fixture counts"""
        # Count exact fixtures rather than using multipliers
        primary_fixtures = {
            "Premium": 5,  # 1 shower + 2 sinks + 1 tub + 1 toilet = 5
            "Luxury": 6,   # 2 showers + 2 sinks + 1 tub + 1 toilet = 6
            "Ultra-Luxury": 8  # 3 showers + 2 sinks + 1 tub + 2 toilets = 8
        }
        
        secondary_fixtures = {
            "Premium": 3,  # 1 shower + 1 sink + 0.7 tub + 1 toilet ≈ 3
            "Luxury": 3,   # 1 shower + 1 sink + 0.7 tub + 1 toilet ≈ 3
            "Ultra-Luxury": 5  # 1 shower + 2 sinks + 0.7 tub + 1 toilet ≈ 5
        }
        
        powder_fixtures = 2  # 1 sink + 1 toilet = 2
        
        total_fixtures = (
            (primary_bath_count * primary_fixtures[tier]) +
            (secondary_bath_count * secondary_fixtures[tier]) +
            (powder_room_count * powder_fixtures)
        )
        
        return {
            "total_plumbing_fixtures": round(total_fixtures)
        }