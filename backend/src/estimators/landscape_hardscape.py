import math
import logging

logger = logging.getLogger(__name__)

class LandscapeHardscapeEstimator:
    """Handles landscape and hardscape quantity calculations"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate landscape and hardscape quantities based on inputs"""
        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate lot size and areas
        results.update(self._calculate_lot_areas(square_footage, tier))
        
        # Calculate plants
        results.update(self._calculate_plants(results["non_house_area_sf"], tier))
        
        # Calculate hardscape breakdown
        results.update(self._calculate_hardscape_breakdown(results["hardscape_area_sf"], tier))
        
        # Calculate irrigation
        results.update(self._calculate_irrigation(results, tier))
        
        # Calculate specialty features
        results.update(self._calculate_specialty_features(results["lot_size_sf"], tier))
        
        return results
        
    def _calculate_lot_areas(self, square_footage, tier):
        """Calculate lot size and area breakdown"""
        # Lot size multiplier (lot size to house footprint ratio)
        lot_size_multiplier = {
            "Premium": 3.0,
            "Luxury": 4.0,
            "Ultra-Luxury": 5.0
        }
        
        # Calculate house footprint (assuming 1.5 stories average)
        house_footprint = square_footage / 1.5
        
        # Calculate lot size
        lot_size = house_footprint * lot_size_multiplier[tier]
        
        # Calculate non-house area
        non_house_area = lot_size - house_footprint
        
        # Area breakdown percentages by tier
        hardscape_pct = {
            "Premium": 0.25,
            "Luxury": 0.3,
            "Ultra-Luxury": 0.35
        }
        
        lawn_pct = {
            "Premium": 0.50,
            "Luxury": 0.40,
            "Ultra-Luxury": 0.30
        }
        
        planting_bed_pct = {
            "Premium": 0.20,
            "Luxury": 0.25,
            "Ultra-Luxury": 0.30
        }
        
        # Calculate area breakdown
        hardscape_area = non_house_area * hardscape_pct[tier]
        lawn_area = non_house_area * lawn_pct[tier]
        planting_bed_area = non_house_area * planting_bed_pct[tier]
        
        # Calculate remaining area (drives, utility areas, etc.)
        remaining_area = non_house_area - hardscape_area - lawn_area - planting_bed_area
        
        return {
            "lot_size_sf": round(lot_size),
            "house_footprint_sf": round(house_footprint),
            "non_house_area_sf": round(non_house_area),
            "hardscape_area_sf": round(hardscape_area),
            "lawn_area_sf": round(lawn_area),
            "planting_bed_area_sf": round(planting_bed_area),
            "other_area_sf": round(remaining_area)
        }
        
    def _calculate_plants(self, non_house_area, tier):
        """Calculate plant quantities"""
        # Plants per 1000 SF of non-house area
        trees_per_1000 = {
            "Premium": 0.4,
            "Luxury": 0.6,
            "Ultra-Luxury": 0.8
        }
        
        shrubs_per_1000 = {
            "Premium": 8,
            "Luxury": 12,
            "Ultra-Luxury": 16
        }
        
        # Calculate plant quantities
        tree_count = (non_house_area / 1000) * trees_per_1000[tier]
        shrub_count = (non_house_area / 1000) * shrubs_per_1000[tier]
        
        # Additional plant types for luxury tiers
        result = {
            "tree_count": round(tree_count),
            "shrub_count": round(shrub_count)
        }
        
        if tier in ["Luxury", "Ultra-Luxury"]:
            # Ornamental trees (about 20% of total trees)
            result["ornamental_tree_count"] = round(tree_count * 0.2)
            
            # Specialty shrubs (about 15% of total shrubs)
            result["specialty_shrub_count"] = round(shrub_count * 0.15)
            
            # Perennials and ground cover
            perennials_per_shrub = 3 if tier == "Luxury" else 5
            result["perennial_count"] = round(shrub_count * perennials_per_shrub)
            
        return result
        
    def _calculate_hardscape_breakdown(self, hardscape_area, tier):
        """Calculate hardscape area breakdown"""
        # Hardscape breakdown percentages by tier
        if tier == "Premium":
            patio_pct = 0.5
            walkway_pct = 0.3
            driveway_pct = 0.2
            outdoor_kitchen_pct = 0
            pool_deck_pct = 0
            specialty_pct = 0
        elif tier == "Luxury":
            patio_pct = 0.4
            walkway_pct = 0.25
            driveway_pct = 0.25
            outdoor_kitchen_pct = 0.05
            pool_deck_pct = 0.05
            specialty_pct = 0
        else:  # Ultra-Luxury
            patio_pct = 0.35
            walkway_pct = 0.2
            driveway_pct = 0.2
            outdoor_kitchen_pct = 0.08
            pool_deck_pct = 0.1
            specialty_pct = 0.07
            
        # Calculate hardscape areas
        result = {
            "patio_area_sf": round(hardscape_area * patio_pct),
            "walkway_area_sf": round(hardscape_area * walkway_pct),
            "driveway_area_sf": round(hardscape_area * driveway_pct)
        }
        
        # Add luxury hardscape elements
        if tier in ["Luxury", "Ultra-Luxury"]:
            result["outdoor_kitchen_area_sf"] = round(hardscape_area * outdoor_kitchen_pct)
            result["pool_deck_area_sf"] = round(hardscape_area * pool_deck_pct)
            
        if tier == "Ultra-Luxury":
            result["specialty_hardscape_area_sf"] = round(hardscape_area * specialty_pct)
            
        return result
        
    def _calculate_irrigation(self, areas, tier):
        """Calculate irrigation system quantities"""
        # Irrigation coverage percentage by tier
        irrigation_pct = {
            "Premium": 0.7,
            "Luxury": 0.9,
            "Ultra-Luxury": 1.0
        }
        
        # Calculate irrigated area (lawn + planting beds)
        landscape_area = areas["lawn_area_sf"] + areas["planting_bed_area_sf"]
        irrigation_area = landscape_area * irrigation_pct[tier]
        
        # Calculate sprinkler counts (rough approximation)
        # Lawn sprinklers: approximately 1 per 150 sq ft
        # Drip irrigation: approximately 1 emitter per 4 sq ft in planting beds
        lawn_sprinklers = areas["lawn_area_sf"] / 150
        drip_emitters = areas["planting_bed_area_sf"] / 4
        
        # Valve count: approximately 1 per 1500 sq ft for lawn, 1 per 1000 sq ft for beds
        irrigation_valves = (areas["lawn_area_sf"] / 1500) + (areas["planting_bed_area_sf"] / 1000)
        
        return {
            "irrigation_area_sf": round(irrigation_area),
            "lawn_sprinklers": round(lawn_sprinklers),
            "drip_emitters": round(drip_emitters),
            "irrigation_valves": round(irrigation_valves)
        }
        
    def _calculate_specialty_features(self, lot_size, tier):
        """Calculate specialty landscape features"""
        # Convert lot size to acres
        lot_size_acres = lot_size / 43560
        
        # Specialty features per acre by tier
        specialty_features_per_acre = {
            "Premium": 1,
            "Luxury": 2,
            "Ultra-Luxury": 4
        }
        
        # Calculate base specialty features
        specialty_features = lot_size_acres * specialty_features_per_acre[tier]
        
        # Allocate specialty features based on tier
        result = {}
        
        if tier == "Premium":
            result["fire_pit_count"] = 1 if specialty_features >= 1 else 0
        elif tier == "Luxury":
            result["fire_pit_count"] = 1
            result["water_feature_count"] = 1 if specialty_features >= 2 else 0
            result["outdoor_lighting_count"] = round(result.get("hardscape_area_sf", 5000) / 250)  # one light per 250 sf
        else:  # Ultra-Luxury
            result["fire_pit_count"] = 1
            result["water_feature_count"] = round(specialty_features / 2)
            result["outdoor_lighting_count"] = round(result.get("hardscape_area_sf", 7000) / 200)  # one light per 200 sf
            result["outdoor_structure_count"] = 1 if specialty_features >= 3 else 0
            result["specialty_landscape_features"] = round(specialty_features - 2)
            
        return result