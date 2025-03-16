import logging

logger = logging.getLogger(__name__)

class PlumbingEstimator:
    """Handles plumbing quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate plumbing quantities based on inputs"""
        if not square_footage:
            return {}
            
        # Get bathroom counts from kwargs or use defaults
        primary_bath_count = kwargs.get('primary_bath_count', 1)
        secondary_bath_count = kwargs.get('secondary_bath_count', 1)
        powder_room_count = kwargs.get('powder_room_count', 0)
        
        results = {}
        
        # Calculate primary bathroom fixtures
        results.update(self._calculate_primary_bath(square_footage, tier, primary_bath_count))
        
        # Calculate secondary bathroom fixtures
        results.update(self._calculate_secondary_bath(square_footage, tier, secondary_bath_count))
        
        # Calculate powder room fixtures
        results.update(self._calculate_powder_room(tier, powder_room_count))
        
        # Calculate water heating system
        results.update(self._calculate_water_heating(square_footage, tier))
        
        # Calculate total fixtures (summary)
        results.update(self._calculate_total_fixtures(primary_bath_count, secondary_bath_count, powder_room_count, tier))
        
        return results
        
    def _calculate_primary_bath(self, square_footage, tier, count):
        """Calculate primary bathroom fixture quantities"""
        if count <= 0:
            return {'primary_bath_count': 0}
            
        # Base quantities per bathroom
        base_shower_valves = {"Premium": 1, "Luxury": 2, "Ultra-Luxury": 3}
        base_sinks = {"Premium": 2, "Luxury": 2, "Ultra-Luxury": 3}
        base_bathtubs = {"Premium": 1, "Luxury": 1, "Ultra-Luxury": 1.5}
        base_toilets = {"Premium": 1, "Luxury": 1, "Ultra-Luxury": 2}
        
        # Additional per 1000 sq ft
        shower_per_1000 = 0.4  # same for all tiers
        sinks_per_1000 = 0.5   # same for all tiers
        bathtubs_per_1000 = 0.1  # same for all tiers
        toilets_per_1000 = 0.2   # same for all tiers
        
        # Calculate quantities for all primary bathrooms
        shower_valves = count * (base_shower_valves[tier] + (square_footage * shower_per_1000 / 1000))
        sinks = count * (base_sinks[tier] + (square_footage * sinks_per_1000 / 1000))
        bathtubs = count * (base_bathtubs[tier] + (square_footage * bathtubs_per_1000 / 1000))
        toilets = count * (base_toilets[tier] + (square_footage * toilets_per_1000 / 1000))
        
        return {
            "primary_bath_count": count,
            "primary_shower_valves": round(shower_valves),
            "primary_sinks": round(sinks),
            "primary_bathtubs": round(bathtubs),
            "primary_toilets": round(toilets)
        }
        
    def _calculate_secondary_bath(self, square_footage, tier, count):
        """Calculate secondary bathroom fixture quantities"""
        if count <= 0:
            return {'secondary_bath_count': 0}
            
        # Base quantities per bathroom
        secondary_shower_valves = 1  # One per bathroom for all tiers
        
        # Base sink count varies by tier
        base_secondary_sinks = {"Premium": 1, "Luxury": 1.5, "Ultra-Luxury": 2}
        
        # Additional per 1000 sq ft
        sinks_per_1000 = 0.3  # same for all tiers
        
        # Calculate quantities for all secondary bathrooms
        shower_valves = count * secondary_shower_valves
        sinks = count * (base_secondary_sinks[tier] + (square_footage * sinks_per_1000 / 1000))
        
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
        """Calculate total fixture counts (simplified formula)"""
        fixtures_per_primary_bath = {"Premium": 5, "Luxury": 6, "Ultra-Luxury": 8}
        fixtures_per_secondary_bath = {"Premium": 3.7, "Luxury": 4.7, "Ultra-Luxury": 5.7}
        fixtures_per_powder_room = 2  # Same for all tiers
        
        total_fixtures = (
            (primary_bath_count * fixtures_per_primary_bath[tier]) +
            (secondary_bath_count * fixtures_per_secondary_bath[tier]) +
            (powder_room_count * fixtures_per_powder_room)
        )
        
        return {
            "total_plumbing_fixtures": round(total_fixtures)
        }