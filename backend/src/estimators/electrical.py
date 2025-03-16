# src/estimators/electrical.py
import logging

logger = logging.getLogger(__name__)

class ElectricalEstimator:
    """Handles electrical quantity calculations with standardized units"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config or {}
        # Define standard units for all electrical quantities
        self.standard_units = {
            "standard_outlets": "EA",
            "gfci_outlets": "EA",
            "usb_outlets": "EA",
            "floor_outlets": "EA", 
            "single_pole_switches": "EA",
            "three_way_switches": "EA",
            "dimmer_switches": "EA",
            "smart_switches": "EA",
            "recessed_lights": "EA",
            "pendants": "EA",
            "chandeliers": "EA",
            "under_cabinet_lights": "LF",
            "toe_kick_lights": "LF",
            "closet_lights": "EA",
            "lighting_control_panels": "EA",
            "audio_visual_drops": "EA",
            "security_system_components": "EA",
            "main_panel_size": "AMP",
            "sub_panels": "EA",
            "total_circuits": "EA",
            "romex_lf": "LF",
            "total_outlets_switches": "EA",
            "total_light_fixtures": "EA",
            "total_specialty_systems": "EA"
        }
    
    def set_config(self, config):
        """Set configuration (for estimation engine integration)"""
        self.config = config
    
    def calculate_quantities(self, square_footage, tier, **kwargs):
        """Calculate electrical quantities with standardized units"""
        logger.info(f"Calculating electrical quantities for {square_footage} sq ft, tier: {tier}")
        print(f"Calculating electrical quantities for {square_footage} sq ft, tier: {tier}")

        if not square_footage:
            return {}
            
        results = {}
        
        # Calculate outlets and switches
        results.update(self._calculate_outlets_switches(square_footage, tier))
        
        # Calculate lighting
        results.update(self._calculate_lighting(square_footage, tier))
        
        # Calculate specialty systems
        results.update(self._calculate_specialty_systems(square_footage, tier))
        
        # Calculate distribution (panels, wiring)
        results.update(self._calculate_distribution(square_footage, tier))
        
        # Add units dictionary to results
        results["units"] = {key: self.standard_units.get(key, "EA") for key in results.keys() 
                            if key != "units"}
        
        logger.info(f"Calculated quantities: {results}")
        print(f"Calculated quantities: {results}")

        return results
        
    def _calculate_outlets_switches(self, square_footage, tier):
        """Calculate outlet and switch quantities"""
        # Define coefficients for each tier
        coefficients = {
            "Premium": {
                "standard_outlets": 0.020,
                "gfci_outlets": 0.004,
                "usb_outlets": 0.001,
                "floor_outlets": 0.001,
                "single_pole_switches": 0.014,
                "three_way_switches": 0.005,
                "dimmer_switches": 0.005,
                "smart_switches": 0.001
            },
            "Luxury": {
                "standard_outlets": 0.022,
                "gfci_outlets": 0.005,
                "usb_outlets": 0.003,
                "floor_outlets": 0.002,
                "single_pole_switches": 0.015,
                "three_way_switches": 0.006,
                "dimmer_switches": 0.007,
                "smart_switches": 0.003
            },
            "Ultra-Luxury": {
                "standard_outlets": 0.025,
                "gfci_outlets": 0.006,
                "usb_outlets": 0.005,
                "floor_outlets": 0.004,
                "single_pole_switches": 0.016,
                "three_way_switches": 0.008,
                "dimmer_switches": 0.01,
                "smart_switches": 0.007
            }
        }
        
        result = {}
        for item, coefficient in coefficients[tier].items():
            result[item] = round(square_footage * coefficient)
            
        # Calculate total outlets and switches for summary
        result["total_outlets_switches"] = round(square_footage * {
            "Premium": 0.06, 
            "Luxury": 0.07, 
            "Ultra-Luxury": 0.08
        }[tier])
        
        return result
        
    def _calculate_lighting(self, square_footage, tier):
        """Calculate lighting quantities"""
        # Define coefficients for each tier
        coefficients = {
            "Premium": {
                "recessed_lights": 0.014,
                "pendants": 0.001,
                "chandeliers": 0.0005,
                "under_cabinet_lights": 0.008,
                "toe_kick_lights": 0,
                "closet_lights": 0.002
            },
            "Luxury": {
                "recessed_lights": 0.015,
                "pendants": 0.0013,
                "chandeliers": 0.001,
                "under_cabinet_lights": 0.01,
                "toe_kick_lights": 0.005,
                "closet_lights": 0.003
            },
            "Ultra-Luxury": {
                "recessed_lights": 0.018,
                "pendants": 0.002,
                "chandeliers": 0.0015,
                "under_cabinet_lights": 0.012,
                "toe_kick_lights": 0.01,
                "closet_lights": 0.005
            }
        }
        
        result = {}
        for item, coefficient in coefficients[tier].items():
            result[item] = round(square_footage * coefficient)
            
        # Calculate total light fixtures for summary
        result["total_light_fixtures"] = round(square_footage * {
            "Premium": 0.03, 
            "Luxury": 0.035, 
            "Ultra-Luxury": 0.045
        }[tier])
        
        return result
        
    def _calculate_specialty_systems(self, square_footage, tier):
        """Calculate specialty electrical systems"""
        # Simplified specialty systems calculation
        specialty_systems = round(square_footage * {
            "Premium": 0.005, 
            "Luxury": 0.008, 
            "Ultra-Luxury": 0.012
        }[tier])
        
        # Detailed breakdown for luxury tiers
        result = {"total_specialty_systems": specialty_systems}
        
        if tier in ["Luxury", "Ultra-Luxury"]:
            result["lighting_control_panels"] = round(square_footage * {
                "Luxury": 0.0002, 
                "Ultra-Luxury": 0.0005
            }[tier])
            
            result["audio_visual_drops"] = round(square_footage * {
                "Luxury": 0.002, 
                "Ultra-Luxury": 0.003
            }[tier])
            
            result["security_system_components"] = round(square_footage * {
                "Luxury": 0.001, 
                "Ultra-Luxury": 0.002
            }[tier])
        
        return result
        
    def _calculate_distribution(self, square_footage, tier):
        """Calculate electrical distribution system quantities"""
        result = {}
        
        # Main panel and sub-panels
        if square_footage <= 5000:
            result["main_panel_size"] = 200
            result["sub_panels"] = 0 if tier == "Premium" else 1
        elif square_footage <= 8000:
            result["main_panel_size"] = 400
            result["sub_panels"] = 1 if tier == "Premium" else 2
        else:
            result["main_panel_size"] = 400
            result["sub_panels"] = 2 if tier == "Premium" else (3 if tier == "Luxury" else 4)
        
        # Circuit counts
        circuits_per_device = {"Premium": 8, "Luxury": 7, "Ultra-Luxury": 6}
        result["total_circuits"] = round((square_footage * 0.06) / circuits_per_device[tier])
        
        # Wiring (simplified calculation)
        result["romex_lf"] = round(square_footage * {
            "Premium": 2.5, 
            "Luxury": 3.0, 
            "Ultra-Luxury": 3.5
        }[tier])
        
        return result