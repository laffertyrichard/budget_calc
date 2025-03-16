# tests/core/test_estimation_engine.py

import unittest
import os
import json
from pathlib import Path
from src.core.estimation_engine import EstimationEngine
import logging

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestEstimationEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment before each test method."""
        # Use test configuration files
        test_dir = Path(__file__).parent.parent
        self.config_path = os.path.join(test_dir, 'test_data', 'settings.json')
        
        # Create engine instance
        self.engine = EstimationEngine(self.config_path)

        # Debug: Verify catalog loaded properly
        print(f"Catalog loaded: {self.engine.catalog is not None}")
        if self.engine.catalog is not None:
            print(f"Catalog size: {len(self.engine.catalog)} items")
        if len(self.engine.catalog) > 0:
            print(f"First 3 catalog items:")
            for _, row in self.engine.catalog.head(3).iterrows():
                print(f"  ID: {row.get('ID', 'N/A')}, Item: {row.get('Item', 'N/A')}, Category: {row.get('Category', 'N/A')}")

        # Sample project data
        self.sample_project = {
            "square_footage": 5000,
            "tier": "Luxury",
            "bedroom_count": 4,
            "primary_bath_count": 1,
            "secondary_bath_count": 2,
            "powder_room_count": 1
        }
    
    def test_initialization(self):
        """Test if estimation engine initializes correctly."""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.config)
        self.assertIsNotNone(self.engine.mappings)
        self.assertIsNotNone(self.engine.catalog)
    
    def test_validate_project_data(self):
        """Test project data validation."""
        # Valid data
        result = self.engine.validate_project_data(self.sample_project)
        self.assertTrue(result['is_valid'])
        
        # Invalid data - missing square footage
        invalid_project = self.sample_project.copy()
        invalid_project.pop("square_footage")
        result = self.engine.validate_project_data(invalid_project)
        self.assertFalse(result['is_valid'])
        self.assertIn("square_footage", result['missing_fields'])
        
        # Invalid data - negative square footage
        invalid_project = self.sample_project.copy()
        invalid_project["square_footage"] = -100
        result = self.engine.validate_project_data(invalid_project)
        self.assertFalse(result['is_valid'])
        self.assertTrue(any(item['field'] == 'square_footage' for item in result['invalid_values']))
    
    def test_determine_tier(self):
        """Test tier determination logic."""
        # Test different square footages
        self.assertEqual(self.engine._determine_tier(4500), "Premium")
        self.assertEqual(self.engine._determine_tier(7000), "Luxury")
        self.assertEqual(self.engine._determine_tier(12000), "Ultra-Luxury")
    
    def test_estimate_project(self):
        """Test complete project estimation."""
        result = self.engine.estimate_project(self.sample_project)
        
        # Debug output
        print(f"Categories in result: {list(result.get('categories', {}).keys())}")
        print(f"Total cost: {result.get('total_cost', 0)}")

        # Debug category details
        for category, data in result.get('categories', {}).items():
            status = data.get('status', 'unknown')
        print(f"Category '{category}' status: {status}")
        
        if status == 'success':
            total = data.get('total_cost', 0)
            print(f"  Total cost: ${total}")
            costed_items = data.get('costed_items', [])
            print(f"  Costed items: {len(costed_items)}")
        elif status == 'error':
            print(f"  Error: {data.get('message', 'Unknown error')}")

        # Check structure of results
        self.assertIn('project', result)
        self.assertIn('categories', result)
        self.assertIn('summary', result)
        self.assertIn('total_cost', result)
        
        # Check project data is preserved
        self.assertEqual(result['project']['square_footage'], self.sample_project['square_footage'])
        self.assertEqual(result['project']['tier'], self.sample_project['tier'])
        
        # Check categories have been calculated
        self.assertTrue(len(result['categories']) > 0)
        
        # Check summary contains cost breakdown
        self.assertIn('cost_breakdown', result['summary'])
        
        # Ensure total cost is positive
        self.assertGreater(result['total_cost'], 0)
    
    def test_apply_costs(self):
        """Test catalog matching and cost application."""
        # Get a sample estimator and calculate quantities
        estimator_key = next(iter(self.engine.estimators))
        estimator = self.engine.estimators[estimator_key]
        
        if estimator:
            # MODIFY THIS SECTION
            project_data = self.sample_project.copy()
            # Remove square_footage and tier from kwargs to avoid duplication
            project_data_kwargs = {k: v for k, v in project_data.items() 
                            if k not in ['square_footage', 'tier']}
            quantities = estimator.calculate_quantities(
                project_data['square_footage'],
                project_data['tier'],
                **project_data_kwargs
            )
            
            # Apply costs
            costed_items = self.engine._apply_costs(estimator_key, quantities)
            
            # Check results
            self.assertIsInstance(costed_items, list)
            if quantities:  # Skip if no quantities were calculated
                # At least some items should have been costed
                self.assertTrue(len(costed_items) > 0)
                
                # Check structure of a costed item
                if costed_items:
                    item = costed_items[0]
                    self.assertIn('item_name', item)
                    self.assertIn('quantity', item)
                    self.assertIn('unit_cost', item)
                    self.assertIn('total_cost', item)

    def test_save_and_load_estimation(self):
        """Test saving and loading estimations."""
        # Generate an estimation
        estimation = self.engine.estimate_project(self.sample_project)
        
        # Save the estimation
        test_name = "test_estimation"
        save_result = self.engine.save_estimation(estimation, test_name)
        self.assertTrue(save_result)
        
        # Load the estimation
        loaded_estimation = self.engine.load_estimation(test_name)
        self.assertIsNotNone(loaded_estimation)
        
        # Compare original and loaded
        self.assertEqual(estimation['total_cost'], loaded_estimation['total_cost'])
        self.assertEqual(estimation['project']['square_footage'], 
                         loaded_estimation['project']['square_footage'])
        
        # Cleanup
        estimations_path = self.engine.data_loader.config.get('data', {}).get('estimations_path', 'data/estimations')
        file_path = os.path.join(estimations_path, f"{test_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

# Add additional test classes for other core components
# tests/estimators/test_foundation.py

class TestFoundationEstimator(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment before each test method."""
        from src.estimators.foundation import FoundationEstimator
        self.estimator = FoundationEstimator()
    
    def test_calculate_quantities(self):
        """Test calculation of foundation quantities."""
        # Test with different square footages and tiers
        test_cases = [
            (4000, "Premium"),
            (6000, "Luxury"),
            (12000, "Ultra-Luxury")
        ]
        
        for sf, tier in test_cases:
            quantities = self.estimator.calculate_quantities(sf, tier)
            
            # Print what we're getting to debug
            print(f"Foundation quantities for {sf} sq ft, {tier} tier:")
            for key, value in quantities.items():
                print(f"  {key}: {value}")

            # Check that expected quantities are returned
            self.assertIn('slab_concrete_cy', quantities)
            self.assertIn('footing_concrete_cy', quantities)
            self.assertIn('foundation_wall_cy', quantities)
            self.assertIn('total_concrete_cy', quantities)
            
            # Validate calculations with a tolerance of 1 cubic yard
            sum_of_parts = (
                quantities['slab_concrete_cy'] + 
                quantities['footing_concrete_cy'] + 
                quantities['foundation_wall_cy']
            )
            self.assertAlmostEqual(
                quantities['total_concrete_cy'],
                sum_of_parts,
                delta=1  # Allow difference of 1
            )
            
            # Check that values scale with square footage
            self.assertGreater(quantities['slab_concrete_cy'], 0)
            self.assertGreater(quantities['footing_concrete_cy'], 0)
            
            # Values should increase with tier quality
            if tier == "Ultra-Luxury" and sf == 12000:
                previous = self.estimator.calculate_quantities(sf, "Luxury")
                self.assertGreaterEqual(quantities['total_concrete_cy'], 
                                       previous['total_concrete_cy'])

# tests/core/test_data_loader.py

class TestDataLoader(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment before each test method."""
        from src.core.data_loader import DataLoader
        test_dir = Path(__file__).parent.parent
        self.config_path = os.path.join(test_dir, 'test_data', 'settings.json')
        self.data_loader = DataLoader(self.config_path)
    
    def test_load_catalog(self):
        """Test loading and processing of catalog data."""
        catalog = self.data_loader.load_catalog()
        self.assertFalse(catalog.empty)
        self.assertIn('Item', catalog.columns)
        self.assertIn('Cost(Mid)', catalog.columns)
        self.assertIn('Unit', catalog.columns)
        
    def test_match_quantity_to_catalog_items(self):
        """Test matching quantities to catalog items."""
        # First ensure catalog is loaded
        self.data_loader.load_catalog()
        
        # Test matching for a common category and quantity
        matches = self.data_loader.match_quantity_to_catalog_items('foundation', 'slab_concrete_cy', 100)
        
        # Check if matches were found (assuming catalog has foundation items)
        if not matches.empty:
            self.assertGreater(len(matches), 0)
            
            # Check that matches are from the correct category
            all_foundation = all(
                cat in matches['Category'].values for cat in ['Foundation', 'Concrete']
            )
            self.assertTrue(all_foundation)

# tests/utils/test_catalog_mapper.py

class TestCatalogMapper(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment before each test method."""
        from src.utils.catalog_mapper import CatalogMapper
        test_dir = Path(__file__).parent.parent
        self.catalog_path = os.path.join(test_dir, 'test_data', 'catalog_enhanced.csv')
        self.mapping_config_path = os.path.join(test_dir, 'test_data', 'catalog_mappings.json')
        
        # Ensure test files exist
        if not os.path.exists(self.catalog_path):
            self.skipTest("Test catalog file not found")
            
        self.mapper = CatalogMapper(self.catalog_path, self.mapping_config_path)
    
    def test_get_catalog_items_for_quantity(self):
        """Test retrieving catalog items for a quantity."""
        if self.mapper.catalog.empty:
            self.skipTest("Catalog is empty")
            
        # Test with a few sample quantities
        test_quantities = [
            ('electrical', 'recessed_lights'),
            ('foundation', 'slab_concrete_cy'),
            ('plumbing', 'primary_shower_valves')
        ]
        
        for module, quantity in test_quantities:
            items = self.mapper.get_catalog_items_for_quantity(module, quantity, "Luxury")
            # Don't assert on specific results as they depend on the test catalog,
            # but verify the function returns the expected structure
            self.assertIsInstance(items, list)
            
            # If items were found, check their structure
            if items:
                item = items[0]
                self.assertIsInstance(item, dict)
                self.assertIn('ID', item)
                self.assertIn('Item', item)
    
    def test_get_unit_conversion_factor(self):
        """Test unit conversion factor retrieval."""
        # Test known conversions
        self.assertEqual(self.mapper.get_unit_conversion_factor('SF', 'SF'), 1.0)
        
        # Depending on the config, these may exist - adjust as needed
        factor = self.mapper.get_unit_conversion_factor('SF', 'SY')
        if factor:
            self.assertAlmostEqual(factor, 1/9, places=2)
            
        # Test reverse conversion
        factor_reverse = self.mapper.get_unit_conversion_factor('SY', 'SF')
        if factor_reverse:
            self.assertAlmostEqual(factor_reverse, 9, places=2)
        
        # Test invalid conversion
        self.assertIsNone(self.mapper.get_unit_conversion_factor('SF', 'GAL'))

if __name__ == "__main__":
    unittest.main()