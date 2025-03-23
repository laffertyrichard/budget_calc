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
            "main_panel_size": "EA",
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
        """Calculate electrical distribution system quantities with dynamic service selection"""
        result = {}
        
        # Define electrical service levels based on square footage
        service_levels = {
            "Premium": [
                {"min_sf": 0, "max_sf": 4000, "main_panel_size": 200, "electrical_service_name": "Electrical New 200 Amp Service"},
                {"min_sf": 4001, "max_sf": 6500, "main_panel_size": 400, "electrical_service_name": "Electrical New 400 Amp Service"},
                {"min_sf": 6501, "max_sf": float('inf'), "main_panel_size": 600, "electrical_service_name": "Electrical New 600 Amp Service"}
            ],
            "Luxury": [
                {"min_sf": 0, "max_sf": 5000, "main_panel_size": 200, "electrical_service_name": "Electrical New 200 Amp Service"},
                {"min_sf": 5001, "max_sf": 8000, "main_panel_size": 400, "electrical_service_name": "Electrical New 400 Amp Service"},
                {"min_sf": 8001, "max_sf": float('inf'), "main_panel_size": 600, "electrical_service_name": "Electrical New 600 Amp Service"}
            ],
            "Ultra-Luxury": [
                {"min_sf": 0, "max_sf": 6000, "main_panel_size": 400, "electrical_service_name": "Electrical New 400 Amp Service"},
                {"min_sf": 6001, "max_sf": float('inf'), "main_panel_size": 600, "electrical_service_name": "Electrical New 600 Amp Service"}
            ]
        }
        
        # Select the appropriate service level
        selected_service = next(
            (service for service in service_levels[tier] 
             if service['min_sf'] <= square_footage < service['max_sf']), 
            service_levels[tier][-1]  # Default to the last (largest) service
        )
        
        # Set main panel size and electrical service name
        result["main_panel_size"] = selected_service["main_panel_size"]
        result["main_panel_quantity"] = 1
        result["electrical_service_name"] = selected_service["electrical_service_name"]
        
        # Determine number of sub-panels based on service size and tier
        if square_footage <= 5000:
            result["sub_panels"] = 0 if tier == "Premium" else 1
        elif square_footage <= 8000:
            result["sub_panels"] = 1 if tier == "Premium" else 2
        else:
            result["sub_panels"] = 2 if tier == "Premium" else (3 if tier == "Luxury" else 4)
        
        # Kitchen circuits calculation
        kitchen_circuits = round(square_footage * 0.005)  # ~5 per 1,000 SF
        lighting_circuits = round(square_footage * 0.004)  # ~4 per 1,000 SF
        outlet_circuits = round(square_footage * 0.005)  # ~5 per 1,000 SF
        mechanical_circuits = round(square_footage * 0.002)  # ~2 per 1,000 SF
        
        # Tier-based adjustments
        tier_multiplier = {
            "Premium": 1.0,
            "Luxury": 1.2,
            "Ultra-Luxury": 1.5
        }
        
        # Apply tier multipliers to base calculations
        kitchen_circuits = round(kitchen_circuits * tier_multiplier[tier])
        lighting_circuits = round(lighting_circuits * tier_multiplier[tier])
        outlet_circuits = round(outlet_circuits * tier_multiplier[tier])
        mechanical_circuits = round(mechanical_circuits * tier_multiplier[tier])
        
        # Add baseline circuits to results
        result["kitchen_circuits"] = kitchen_circuits
        result["lighting_circuits"] = lighting_circuits
        result["outlet_circuits"] = outlet_circuits
        result["mechanical_circuits"] = mechanical_circuits
        
        # Calculate baseline total
        baseline_total = kitchen_circuits + lighting_circuits + outlet_circuits + mechanical_circuits
        
        # Optional additional circuits based on tier
        additional_circuits = {}
        
        if tier == "Premium":
            # Basic additional circuits for Premium tier
            additional_circuits = {
                "exterior_lighting_circuits": 1,
                "garage_circuits": 1,
                "emergency_circuits": 1
            }
        elif tier == "Luxury":
            # More additional circuits for Luxury tier
            additional_circuits = {
                "exterior_lighting_circuits": 2,
                "garage_circuits": 2,
                "emergency_circuits": 1,
                "audio_visual_circuits": 2,
                "home_office_circuits": 1,
                "security_system_circuits": 1
            }
        else:  # Ultra-Luxury
            # Maximum additional circuits for Ultra-Luxury tier
            additional_circuits = {
                "exterior_lighting_circuits": 3,
                "garage_circuits": 3,
                "emergency_circuits": 2,
                "audio_visual_circuits": 4,
                "home_office_circuits": 2,
                "security_system_circuits": 2,
                "pool_spa_circuits": 3,
                "outdoor_kitchen_circuits": 2,
                "smart_home_circuits": 2,
                "wine_room_circuits": 1,
                "heated_flooring_circuits": 2
            }
        
        # Add additional circuits to results
        result.update(additional_circuits)
        
        # Calculate total additional circuits
        additional_total = sum(additional_circuits.values())
        
        # Calculate overall total circuits
        result["total_baseline_circuits"] = baseline_total
        result["total_additional_circuits"] = additional_total
        result["total_circuits"] = baseline_total + additional_total
        
        # Calculate wiring (simplified calculation)
        result["romex_lf"] = round(square_footage * {
            "Premium": 2.5, 
            "Luxury": 3.0, 
            "Ultra-Luxury": 3.5
        }[tier])
        
        return result