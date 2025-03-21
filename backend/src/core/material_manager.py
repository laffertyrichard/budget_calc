# src/core/material_manager.py
from src.core.material_constants import MATERIAL_CATEGORIES, MATERIAL_MARKUP_PERCENTAGE, MATERIAL_TIERS

class MaterialManager:
    """Manages material identification and markup application"""
    
    def __init__(self):
        self.markup_percentage = MATERIAL_MARKUP_PERCENTAGE
        self.material_categories = MATERIAL_CATEGORIES
        self.material_tiers = MATERIAL_TIERS
        
    def is_material_category(self, category):
        """Check if category is eligible for material markup"""
        return category in self.material_categories
        
    def get_markup_percentage(self):
        """Get the fixed markup percentage for materials"""
        return self.markup_percentage
        
    def apply_markup(self, material_cost):
        """Apply markup to material cost"""
        return material_cost * (1 + (self.markup_percentage / 100))
    
    def get_tier_info(self, tier='Luxury'):
        """Get information about a specific material tier"""
        return self.material_tiers.get(tier, self.material_tiers['Luxury'])