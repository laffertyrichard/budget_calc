import os
import json
import pandas as pd
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

class DataLoader:
    """Class to handle loading and processing catalog and configuration data"""
    
    def __init__(self, config_path: str = 'config/settings.json'):
        """Initialize with path to configuration file"""
        self.config = self._load_json(config_path)
        self.mappings = self._load_json(os.path.join('config', 'enhanced_catalog_mappings.json'))
        self.catalog = None
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load and parse a JSON file"""
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in: {path}")
            return {}
    
    def load_catalog(self, path: str = None) -> pd.DataFrame:
        """Load the cost catalog CSV file with proper data typing and validation"""
        catalog_path = path or self.config.get('data', {}).get('catalog_path', 'data/catalog_enhanced.csv')
        
        try:
            # Define column types for better data handling
            dtype_map = {
                'Item': str,
                'Cost (Low)': str,  # Will convert these to float after handling currency symbols
                'Cost (High)': str,
                'Cost(Mid)': str,
                'Unit': str,
                'Qty': float,
                'Markup Percentage': float,
                'Cost Code': float,
                'Category': str,
                'ID': str
            }
            
            # Load catalog with specified dtypes
            self.catalog = pd.read_csv(catalog_path, dtype=dtype_map)
            
            # Clean and convert cost columns
            for col in ['Cost (Low)', 'Cost (High)', 'Cost(Mid)']:
                if col in self.catalog.columns:
                    # Remove currency symbols and convert to float
                    self.catalog[col] = self.catalog[col].str.replace('[\$,]', '', regex=True).astype(float)
            
            # Fill missing values
            self.catalog['Unit'] = self.catalog['Unit'].fillna('EA')
            self.catalog['Markup Percentage'] = self.catalog['Markup Percentage'].fillna(0)
            
            # Create a standardized 'SearchItem' column for better matching
            self.catalog['SearchItem'] = self.catalog['Item'].str.lower().str.replace('[^a-z0-9]', ' ', regex=True)
            
            logger.info(f"Loaded catalog with {len(self.catalog)} items")
            return self.catalog
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {catalog_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            return pd.DataFrame()
    
    def match_quantity_to_catalog_items(self, category: str, quantity_name: str, quantity_value: Union[int, float]) -> pd.DataFrame:
        """Match a specific quantity to catalog items using enhanced matching logic"""
        if self.catalog is None:
            self.load_catalog()
                
        if self.catalog.empty:
            return pd.DataFrame()
        
        # Get category items
        category_items = self.get_category_items(category)
        
        if category_items.empty:
            return pd.DataFrame()
        
        # Get mapping information for this category
        category_mapping = self.mappings.get('category_mappings', {}).get(category, {})
        
        # Get specific item mappings for quantities in this category
        item_mappings = category_mapping.get('item_mappings', {})
        
        # Check if we have a direct mapping for this quantity
        if quantity_name in item_mappings:
            # Use direct mapping if available
            mapped_item_ids = item_mappings[quantity_name].get('item_ids', [])
            if mapped_item_ids:
                return category_items[category_items['ID'].isin(mapped_item_ids)]
            
            # If we have search terms, use those
            search_terms = item_mappings[quantity_name].get('search_terms', [])
            if search_terms:
                # Create a regex pattern from all search terms
                pattern = '|'.join(search_terms)
                return category_items[category_items['SearchItem'].str.contains(pattern, regex=True, na=False)]
        
        # No direct mapping, try fuzzy matching with the quantity name
        # First, standardize the quantity name for searching
        search_quantity = quantity_name.lower().replace('_', ' ')
        
        # Look for items containing the search term
        matching_items = category_items[
            category_items['SearchItem'].str.contains(search_quantity, na=False)
        ]
        
        return matching_items

    def get_category_items(self, category: str) -> pd.DataFrame:
        """Get catalog items for a specific estimation category"""
        if self.catalog is None:
            self.load_catalog()
                
        if self.catalog.empty:
            return pd.DataFrame()
                
        # Get catalog categories for this estimation category
        catalog_categories = self.mappings.get('category_mappings', {}).get(category, {}).get('catalog_categories', [])
        
        # Filter catalog for these categories
        return self.catalog[self.catalog['Category'].isin(catalog_categories)]
    
    def save_estimation(self, estimation_results: Dict[str, Any], filename: str) -> bool:
        """Save estimation results to a JSON file"""
        estimations_path = self.config.get('data', {}).get('estimations_path', 'data/estimations')
        os.makedirs(estimations_path, exist_ok=True)
        
        file_path = os.path.join(estimations_path, f"{filename}.json")
        
        try:
            with open(file_path, 'w') as file:
                json.dump(estimation_results, file, indent=2)
            logger.info(f"Saved estimation to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving estimation: {str(e)}")
            return False
    
    def load_estimation(self, filename: str) -> Dict[str, Any]:
        """Load a saved estimation from JSON file"""
        estimations_path = self.config.get('data', {}).get('estimations_path', 'data/estimations')
        file_path = os.path.join(estimations_path, f"{filename}.json")
        
        try:
            return self._load_json(file_path)
        except Exception as e:
            logger.error(f"Error loading estimation file: {str(e)}")
            return {}