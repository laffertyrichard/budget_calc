# tests/integration/test_electrical_integration.py

import unittest
import os
import json
from pathlib import Path
import logging

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestElectricalIntegration(unittest.TestCase):
    """Test the integration between the electrical estimator and catalog"""
    
    def setUp(self):
        # Get project root
        project_root = Path(__file__).parent.parent.parent
        
        # Import modules
        from src.core.estimation_engine import EstimationEngine
        from src.estimators.electrical import ElectricalEstimator
        from src.utils.catalog_mapper import CatalogMapper
        from src.utils.electrical_validator import ElectricalCatalogValidator
        
        # Set paths
        config_path = os.path.join(project_root, 'config', 'settings.json')
        catalog_path = os.path.join(project_root, 'data', 'catalog_enhanced.csv')
        mappings_path = os.path.join(project_root, 'config', 'catalog_mappings.json')
        
        # Initialize components
        self.engine = EstimationEngine(config_path)
        self.electrical_estimator = ElectricalEstimator()
        
        # Only initialize catalog mapper if catalog exists
        if os.path.exists(catalog_path):
            self.catalog_mapper = CatalogMapper(catalog_path, mappings_path)
            self.validator = ElectricalCatalogValidator(self.catalog_mapper, self.electrical_estimator)
        else:
            self.catalog_mapper = None
            self.validator = None
        
        # Test data
        self.sample_project = {
            "square_footage": 5000,
            "tier": "Luxury",
            "bedroom_count": 4,
            "primary_bath_count": 1,
            "secondary_bath_count": 2,
            "powder_room_count": 1
        }
    
    def test_electrical_estimator_units(self):
        """Test that electrical estimator produces standardized units"""
        quantities = self.electrical_estimator.calculate_quantities(
            self.sample_project["square_footage"],
            self.sample_project["tier"]
        )
        
        self.assertIn("units", quantities)
        units = quantities["units"]
        
        # Check some key quantities have expected units
        self.assertEqual(units.get("standard_outlets"), "EA")
        self.assertEqual(units.get("recessed_lights"), "EA")
        self.assertEqual(units.get("romex_lf"), "LF")
    
    def test_full_electrical_estimation(self):
        """Test complete electrical estimation with catalog integration"""
        # Skip if no catalog mapper
        if not self.catalog_mapper:
            self.skipTest("Catalog not available for integration test")
        
        # Run estimation
        result = self.engine.estimate_project(self.sample_project)
        
        # Check electrical category is present
        self.assertIn("electrical", result["categories"])
        electrical_result = result["categories"]["electrical"]
        
        print(electrical_result) # Debugging
        # Check status
        self.assertEqual(electrical_result["status"], "success")
        
        # Check costed items
        self.assertIn("costed_items", electrical_result)
        costed_items = electrical_result["costed_items"]
        
        # There should be costed items
        self.assertGreater(len(costed_items), 0)
        
        # Check a costed item structure
        item = costed_items[0]
        self.assertIn("item_name", item)
        self.assertIn("quantity", item)
        self.assertIn("unit_cost", item)
        self.assertIn("total_cost", item)
        self.assertIn("original_quantity_name", item)
        self.assertIn("original_unit", item)
    
    def test_catalog_validation(self):
        """Test electrical catalog validation"""
        # Skip if no validator
        if not self.validator:
            self.skipTest("Catalog not available for validation test")
        
        # Run validation
        validation = self.validator.validate_catalog_coverage()
        
        # Check basic structure
        self.assertIn("total_quantities", validation)
        self.assertIn("matched_quantities", validation)
        self.assertIn("overall_coverage_pct", validation)
        
        # Generate mappings
        mappings = self.validator.generate_missing_mappings()
        
        # Check mappings for missing quantities
        for quantity in validation["missing_matches"]:
            self.assertIn(quantity, mappings)
            self.assertIn("search_terms", mappings[quantity])
            self.assertIn("suggested_mapping", mappings[quantity])

if __name__ == "__main__":
    unittest.main()