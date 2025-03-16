# src/utils/catalog_enhancer.py

import pandas as pd
import re
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CatalogEnhancer:
    """Utility to enhance and standardize the construction catalog"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        
    def enhance_catalog(self, input_path, output_path=None):
        """
        Process the catalog to add standardized names, search attributes, and improved categorization
        
        Args:
            input_path: Path to the original catalog CSV
            output_path: Path to save the enhanced catalog (defaults to adding '_enhanced' to filename)
        
        Returns:
            Path to the enhanced catalog
        """
        # Default output path if not provided
        if not output_path:
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}_enhanced{input_file.suffix}")
        
        # Load catalog
        try:
            catalog = pd.read_csv(input_path)
            logger.info(f"Loaded catalog with {len(catalog)} items from {input_path}")
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            return None
            
        # Process catalog
        enhanced_catalog = self._process_catalog(catalog)
        
        # Save enhanced catalog
        try:
            enhanced_catalog.to_csv(output_path, index=False)
            logger.info(f"Enhanced catalog saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving enhanced catalog: {str(e)}")
            return None
    
    def _process_catalog(self, catalog):
        """Apply all enhancements to the catalog"""
        # Make a copy to avoid modifying the original
        enhanced = catalog.copy()
        
        # Drop rows with missing categories first (before further processing)
        if 'Category' in enhanced.columns:
            pre_drop_count = len(enhanced)
            enhanced = enhanced.dropna(subset=['Category'])
            dropped_count = pre_drop_count - len(enhanced)
            if dropped_count > 0:
                logger.info(f"Dropped {dropped_count} rows with missing categories")
                
        # 1. Clean and standardize cost columns
        enhanced = self._standardize_costs(enhanced)
        
        # 2. Standardize units
        enhanced = self._standardize_units(enhanced)
        
        # 3. Add normalized search field
        enhanced = self._add_search_fields(enhanced)
        
        # 4. Standardize and enhance categories
        enhanced = self._enhance_categories(enhanced)
        
        # 5. Add mapping attributes
        enhanced = self._add_mapping_attributes(enhanced)
        
        return enhanced
    
    def _standardize_costs(self, df):
        """Standardize cost columns to numeric values"""
        # Identify cost columns
        cost_columns = [col for col in df.columns if 'cost' in col.lower()]
        
        for col in cost_columns:
            if pd.api.types.is_string_dtype(df[col].dtype):
                # Remove currency symbols and commas
                df[col] = df[col].str.replace(r'[$,]', '', regex=True)
                
                # Convert to float
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # If 'Cost(Mid)' doesn't exist but 'Cost (Low)' and 'Cost (High)' do, create it
        if 'Cost(Mid)' not in df.columns and 'Cost (Low)' in df.columns and 'Cost (High)' in df.columns:
            df['Cost(Mid)'] = (df['Cost (Low)'] + df['Cost (High)']) / 2
            
        return df
    
    def _standardize_units(self, df):
        """Standardize unit values"""
        # Fill missing units with 'EA'
        if 'Unit' in df.columns:
            df['Unit'] = df['Unit'].fillna('EA')
            
            # Standardize common units
            unit_mapping = {
                'EACH': 'EA', 
                'SQ FT': 'SF',
                'SQUARE FOOT': 'SF', 
                'SQ. FT.': 'SF',
                'SQUARE FEET': 'SF',
                'LIN FT': 'LF',
                'LINEAR FOOT': 'LF',
                'LIN. FT.': 'LF',
                'LINEAR FEET': 'LF',
                'CU YD': 'CY',
                'CUBIC YARD': 'CY',
                'CU. YD.': 'CY',
                'CUBIC YARDS': 'CY',
                'GALLON': 'GAL',
                'GAL.': 'GAL'
            }
            
            # Apply case-insensitive mapping
            df['OriginalUnit'] = df['Unit']  # Keep original for reference
            df['Unit'] = df['Unit'].str.upper().replace(unit_mapping)
        
        return df
    
    def _add_search_fields(self, df):
        """Add normalized fields for better searching"""
        if 'Item' in df.columns:
            # Create normalized search version of item name
            df['SearchItem'] = df['Item'].str.lower()
            
            # Replace special characters with spaces
            df['SearchItem'] = df['SearchItem'].str.replace(r'[^a-z0-9]', ' ', regex=True)
            
            # Remove extra spaces
            df['SearchItem'] = df['SearchItem'].str.replace(r'\s+', ' ', regex=True).str.strip()
            
            # Create keyword list from item description
            df['Keywords'] = df['SearchItem'].apply(self._extract_keywords)
        
        return df
    
    def _extract_keywords(self, text):
        """Extract relevant keywords from text"""
        if not isinstance(text, str):
            return ''
            
        # Split into words
        words = text.split()
        
        # Filter out common stopwords
        stopwords = {'a', 'an', 'the', 'and', 'or', 'of', 'to', 'for', 'with', 'in', 'on', 'by', 'at'}
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Join unique keywords
        return ' '.join(sorted(set(keywords)))
    
    def _enhance_categories(self, df):
        """Standardize and enhance categories"""
        if 'Category' in df.columns:
            # Standardize category names
            df['Category'] = df['Category'].str.strip().str.title()
            
            # Add subcategory based on item description and category
            df['Subcategory'] = self._derive_subcategory(df)
            
            # Add construction phase
            construction_phases = {
                'Foundation': 'Structure',
                'Concrete': 'Structure',
                'Framing': 'Structure',
                'Roofing': 'Envelope',
                'Siding': 'Envelope',
                'Windows': 'Envelope',
                'Doors': 'Envelope',
                'Insulation': 'Envelope',
                'Drywall': 'Interior',
                'Painting': 'Interior',
                'Flooring': 'Interior',
                'Cabinets': 'Interior',
                'Countertops': 'Interior',
                'Plumbing': 'MEP',
                'Electrical': 'MEP',
                'HVAC': 'MEP',
                'Appliances': 'Finish',
                'Landscaping': 'Exterior',
                'Hardscape': 'Exterior'
            }
            
            df['Phase'] = df['Category'].map(lambda x: next(
                (phase for cat, phase in construction_phases.items() if cat in x), 'Other'
            ))
        
        return df
    
    def _derive_subcategory(self, df):
        """Derive subcategory based on item description and category"""
        subcategories = []
        
        for _, row in df.iterrows():
            if not isinstance(row.get('Category', ''), str) or not isinstance(row.get('Item', ''), str):
                subcategories.append('')
                continue
                
            category = row['Category'].lower()
            item = row['Item'].lower()
            
            # Derive subcategory based on category and item description
            if 'concrete' in category:
                if 'slab' in item:
                    subcategories.append('Slab')
                elif 'footing' in item or 'footer' in item:
                    subcategories.append('Footings')
                elif 'wall' in item:
                    subcategories.append('Walls')
                else:
                    subcategories.append('General')
            elif 'electrical' in category:
                if 'outlet' in item or 'receptacle' in item:
                    subcategories.append('Outlets')
                elif 'switch' in item:
                    subcategories.append('Switches')
                elif 'panel' in item or 'breaker' in item:
                    subcategories.append('Panels')
                elif 'wire' in item or 'wiring' in item or 'cable' in item:
                    subcategories.append('Wiring')
                else:
                    subcategories.append('General')
            elif 'lighting' in category:
                if 'recessed' in item or 'can' in item:
                    subcategories.append('Recessed')
                elif 'pendant' in item:
                    subcategories.append('Pendants')
                elif 'chandelier' in item:
                    subcategories.append('Chandeliers')
                elif 'sconce' in item:
                    subcategories.append('Sconces')
                elif 'under cabinet' in item or 'undercabinet' in item:
                    subcategories.append('Under Cabinet')
                else:
                    subcategories.append('General')
            # Add more category-specific logic here
            else:
                subcategories.append('General')
        
        return subcategories
    
    def _add_mapping_attributes(self, df):
        """Add attributes to help with mapping estimator quantities to catalog items"""
        # Add a column for preferred estimator module
        df['EstimatorModule'] = ''
        
        # Map categories to estimator modules
        category_to_module = {
            'Concrete': 'foundation',
            'Foundation': 'foundation',
            'Framing': 'structural',
            'Lumber': 'structural',
            'Steel': 'structural',
            'Electrical': 'electrical',
            'Lighting': 'electrical',
            'Plumbing': 'plumbing',
            'Fixtures': 'plumbing',
            'HVAC': 'hvac',
            'Insulation': 'insulation',
            'Drywall': 'drywall_interior',
            'Paint': 'painting_coatings',
            'Flooring': 'flooring',
            'Tile': 'tile',
            'Cabinets': 'cabinetry',
            'Countertops': 'countertops',
            'Doors': 'windows_doors',
            'Windows': 'windows_doors',
            'Roofing': 'roofing',
            'Landscaping': 'landscape_hardscape',
            'Cleaning': 'cleaning'
        }
        
        # Apply mapping based on category
        for category, module in category_to_module.items():
            mask = df['Category'].str.contains(category, case=False, na=False)
            df.loc[mask, 'EstimatorModule'] = module
        
        # Add a column for quality tier
        df['QualityTier'] = 'Standard'  # Default tier
        
        # Add logic to derive quality tier based on price relative to category average
        for category in df['Category'].unique():
            if pd.isna(category):
                continue
                
            category_items = df[df['Category'] == category]
            
            if len(category_items) < 2 or 'Cost(Mid)' not in category_items.columns:
                continue
                
            # Calculate percentiles for this category
            low_threshold = category_items['Cost(Mid)'].quantile(0.33)
            high_threshold = category_items['Cost(Mid)'].quantile(0.67)
            
            # Assign tiers based on cost
            df.loc[(df['Category'] == category) & (df['Cost(Mid)'] <= low_threshold), 'QualityTier'] = 'Economy'
            df.loc[(df['Category'] == category) & (df['Cost(Mid)'] > low_threshold) & 
                   (df['Cost(Mid)'] <= high_threshold), 'QualityTier'] = 'Standard'
            df.loc[(df['Category'] == category) & (df['Cost(Mid)'] > high_threshold), 'QualityTier'] = 'Premium'
        
        # Map quality tiers to construction tiers
        tier_mapping = {
            'Economy': 'Premium',
            'Standard': 'Luxury',
            'Premium': 'Ultra-Luxury'
        }
        
        # Add construction tier column
        df['ConstructionTier'] = df['QualityTier'].map(tier_mapping)
        
        return df

def main():
    """Main function when run as a script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance construction catalog with improved naming and mapping')
    parser.add_argument('input', help='Input catalog CSV file')
    parser.add_argument('--output', help='Output enhanced catalog CSV file')
    
    args = parser.parse_args()
    
    enhancer = CatalogEnhancer()
    result = enhancer.enhance_catalog(args.input, args.output)
    
    if result:
        print(f"Enhanced catalog saved to: {result}")
    else:
        print("Error enhancing catalog")

if __name__ == "__main__":
    main()