#!/usr/bin/env python3
"""
Test script for verifying mapping integration
"""

import os
import sys
import json
import logging

# Add the parent directory to the path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.estimation_engine import EstimationEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mappings():
    """Test that the updated mappings are correctly integrated with the estimation engine"""
    # Initialize the estimation engine
    estimator = EstimationEngine()
    
    # Define test project data
    project_data = {
        "square_footage": 6500,
        "tier": "Luxury",
        "bedroom_count": 4,
        "primary_bath_count": 2,
        "secondary_bath_count": 2,
        "powder_room_count": 1
    }
    
    # Run the estimation
    logger.info("Starting estimation with test project data")
    results = estimator.estimate_project(project_data)
    
    # Check for direct ID matches
    direct_matches = []
    for category, data in results.get('categories', {}).items():
        if data.get('status') == 'success':
            for item in data.get('costed_items', []):
                # Look for items that were matched by ID
                if item.get('note') and "Direct match" in item.get('note'):
                    direct_matches.append({
                        'category': category,
                        'quantity_name': item.get('original_quantity_name'),
                        'item_id': item.get('item_id'),
                        'item_name': item.get('item_name')
                    })
    
    # Print results
    if direct_matches:
        logger.info(f"Found {len(direct_matches)} direct ID matches:")
        for i, match in enumerate(direct_matches, 1):
            logger.info(f"{i}. Category: {match['category']}, Quantity: {match['quantity_name']}, " 
                       f"Matched to: {match['item_id']} - {match['item_name']}")
    else:
        logger.warning("No direct ID matches found. Check your mapping integration.")
    
    # Check for issues
    unmatched_counts = {}
    for category, data in results.get('categories', {}).items():
        if data.get('status') == 'success':
            unmatched = data.get('unmatched_quantities', [])
            if unmatched:
                unmatched_counts[category] = len(unmatched)
    
    if unmatched_counts:
        logger.info("Categories with unmatched quantities:")
        for category, count in unmatched_counts.items():
            logger.info(f"- {category}: {count} unmatched quantities")
    
    return results

def save_results(results, filename="mapping_test_results.json"):
    """Save test results to a file for inspection"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {filename}")

if __name__ == "__main__":
    logger.info("=== Running Mapping Integration Test ===")
    results = test_mappings()
    save_results(results)
    logger.info("=== Test Complete ===")