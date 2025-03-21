# src/core/material_constants.py

# Categories with material-only items
MATERIAL_CATEGORIES = [
    'plumbing', 
    'tile', 
    'flooring', 
    'countertops',
    'exterior_finishes',
    'roofing'
]

# Fixed markup percentage for all materials
MATERIAL_MARKUP_PERCENTAGE = 30

# Material tier definitions for catalog items
MATERIAL_TIERS = {
    'Premium': {
        'description': 'Builder-grade/standard quality materials',
        'relative_cost': 'low'
    },
    'Luxury': {
        'description': 'Mid to high-grade quality materials',
        'relative_cost': 'medium'
    },
    'Ultra-Luxury': {
        'description': 'Designer/custom quality materials',
        'relative_cost': 'high'
    }
}