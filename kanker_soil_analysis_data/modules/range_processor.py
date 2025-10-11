"""
🚀 Range Processor Module
========================

This module handles intelligent processing of range-based nutrient values
from ICAR 2024-25 data for integration with satellite-based NPK estimation.

Features:
- AI-powered range processing with context awareness
- Multi-method validation for range conversion
- Intelligent fallback mechanisms
- Confidence scoring for processed values

Author: AI Assistant
Date: 2024
Version: 1.0
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NutrientType(Enum):
    """Nutrient types supported by the system"""
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"
    BORON = "boron"
    IRON = "iron"
    ZINC = "zinc"
    SOIL_PH = "soil_ph"

@dataclass
class RangeValue:
    """Data class for range values"""
    min_value: float
    max_value: float
    unit: str
    confidence: float = 0.0
    
    @property
    def center_value(self) -> float:
        """Calculate center value of the range"""
        return (self.min_value + self.max_value) / 2
    
    @property
    def range_width(self) -> float:
        """Calculate width of the range"""
        return self.max_value - self.min_value
    
    @property
    def range_percentage(self) -> float:
        """Calculate range as percentage of center value"""
        if self.center_value == 0:
            return 0
        return (self.range_width / self.center_value) * 100

@dataclass
class VillageContext:
    """Context information for a village"""
    village_name: str
    coordinates: Tuple[float, float]
    soil_type: str = "clay"
    crop_type: str = "rice"
    season: str = "kharif"
    rainfall: str = "normal"
    zone: str = "yellow"
    tehsil: str = "kanker"

class RangeProcessor:
    """
    Intelligent range processor for ICAR nutrient data
    
    This class provides multiple methods for processing range-based
    nutrient values and converting them to single values for API integration.
    """
    
    def __init__(self):
        """Initialize the range processor"""
        self.context_factors = {
            'soil_type': {
                'clay': 1.1,      # Clay soil retains more nutrients
                'sandy': 0.9,     # Sandy soil loses nutrients faster
                'loamy': 1.0,     # Loamy soil is balanced
                'silty': 1.05     # Silty soil retains nutrients well
            },
            'crop_type': {
                'rice': 1.05,     # Rice needs more nitrogen
                'wheat': 1.0,     # Wheat is balanced
                'maize': 1.1,     # Maize needs more nutrients
                'sugarcane': 1.15, # Sugarcane needs high nutrients
                'cotton': 1.08    # Cotton needs moderate-high nutrients
            },
            'season': {
                'kharif': 1.0,    # Normal season
                'rabi': 0.95,     # Slightly lower nutrient needs
                'zaid': 1.05      # Higher nutrient needs
            },
            'rainfall': {
                'high': 0.9,      # High rainfall leaches nutrients
                'normal': 1.0,    # Normal rainfall
                'low': 1.1        # Low rainfall concentrates nutrients
            }
        }
        
        self.nutrient_units = {
            NutrientType.NITROGEN: "kg/ha",
            NutrientType.PHOSPHORUS: "kg/ha",
            NutrientType.POTASSIUM: "kg/ha",
            NutrientType.BORON: "ppm",
            NutrientType.IRON: "ppm",
            NutrientType.ZINC: "ppm",
            NutrientType.SOIL_PH: "pH"
        }
    
    def extract_range_values(self, range_str: str) -> Optional[RangeValue]:
        """
        Extract min and max values from range string
        
        Args:
            range_str: String like "380-440 kg/ha" or "6.5-7.2 pH"
            
        Returns:
            RangeValue object or None if parsing fails
        """
        try:
            # Remove extra whitespace
            range_str = range_str.strip()
            
            # Pattern for range: "min-max unit" or "min-max"
            range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*([a-zA-Z/]+)?'
            match = re.search(range_pattern, range_str)
            
            if match:
                min_val = float(match.group(1))
                max_val = float(match.group(2))
                unit = match.group(3) if match.group(3) else "kg/ha"
                
                return RangeValue(
                    min_value=min_val,
                    max_value=max_val,
                    unit=unit,
                    confidence=0.8  # Default confidence for parsed ranges
                )
            
            # Pattern for single value: "420 kg/ha"
            single_pattern = r'(\d+\.?\d*)\s*([a-zA-Z/]+)?'
            match = re.search(single_pattern, range_str)
            
            if match:
                value = float(match.group(1))
                unit = match.group(2) if match.group(2) else "kg/ha"
                
                return RangeValue(
                    min_value=value,
                    max_value=value,
                    unit=unit,
                    confidence=0.9  # Higher confidence for single values
                )
            
            logger.warning(f"Could not parse range string: {range_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing range string '{range_str}': {e}")
            return None
    
    def ai_powered_range_processing(
        self, 
        range_str: str, 
        satellite_value: float, 
        village_context: VillageContext,
        nutrient_type: NutrientType
    ) -> Dict[str, Union[float, str, float]]:
        """
        AI-powered range processing with context awareness
        
        Args:
            range_str: Range string from ICAR data
            satellite_value: Satellite-derived value
            village_context: Village context information
            nutrient_type: Type of nutrient being processed
            
        Returns:
            Dictionary with processed value, method used, and confidence
        """
        try:
            # Extract range values
            range_value = self.extract_range_values(range_str)
            if not range_value:
                return self._fallback_processing(range_str, satellite_value, village_context)
            
            # Calculate context adjustment factor
            context_factor = self._calculate_context_factor(village_context, nutrient_type)
            
            # AI-powered processing based on satellite agreement
            satellite_agreement = self._calculate_satellite_agreement(
                satellite_value, range_value
            )
            
            if satellite_agreement > 0.7:
                # High agreement - use satellite-adjusted center
                processed_value = range_value.center_value * context_factor
                method = "satellite_adjusted_center"
                confidence = 0.95
                
            elif satellite_value > range_value.max_value:
                # Satellite higher than range - use max with adjustment
                processed_value = range_value.max_value * context_factor
                method = "satellite_higher_max"
                confidence = 0.85
                
            elif satellite_value < range_value.min_value:
                # Satellite lower than range - use min with adjustment
                processed_value = range_value.min_value * context_factor
                method = "satellite_lower_min"
                confidence = 0.85
                
            else:
                # Satellite within range - use weighted average
                weight = 0.6  # 60% ICAR, 40% satellite
                processed_value = (
                    range_value.center_value * weight + 
                    satellite_value * (1 - weight)
                ) * context_factor
                method = "weighted_average"
                confidence = 0.9
            
            return {
                'value': round(processed_value, 2),
                'method': method,
                'confidence': confidence,
                'original_range': range_str,
                'context_factor': context_factor,
                'satellite_agreement': satellite_agreement
            }
            
        except Exception as e:
            logger.error(f"Error in AI-powered processing: {e}")
            return self._fallback_processing(range_str, satellite_value, village_context)
    
    def multi_method_range_validation(
        self, 
        range_str: str, 
        satellite_data: Dict, 
        historical_data: Dict,
        village_context: VillageContext
    ) -> Dict[str, Union[float, str, float]]:
        """
        Multi-method validation for range processing
        
        Args:
            range_str: Range string from ICAR data
            satellite_data: Satellite-derived data
            historical_data: Historical data for validation
            village_context: Village context information
            
        Returns:
            Dictionary with validated value and confidence
        """
        try:
            range_value = self.extract_range_values(range_str)
            if not range_value:
                return self._fallback_processing(range_str, 0, village_context)
            
            # Method 1: Simple average
            method1_value = range_value.center_value
            method1_confidence = 0.7
            
            # Method 2: Weighted average (60% min, 40% max)
            method2_value = range_value.min_value * 0.6 + range_value.max_value * 0.4
            method2_confidence = 0.75
            
            # Method 3: Satellite-adjusted
            satellite_value = satellite_data.get('value', range_value.center_value)
            method3_value = self._adjust_to_satellite(satellite_value, range_value)
            method3_confidence = 0.8
            
            # Method 4: Historical pattern
            method4_value = self._get_historical_average(historical_data, range_value)
            method4_confidence = 0.65
            
            # Method 5: Zone-based typical value
            method5_value = self._get_zone_typical_value(village_context, range_value)
            method5_confidence = 0.7
            
            # Calculate consensus
            methods = [
                (method1_value, method1_confidence),
                (method2_value, method2_confidence),
                (method3_value, method3_confidence),
                (method4_value, method4_confidence),
                (method5_value, method5_confidence)
            ]
            
            # Weighted consensus
            total_weight = sum(conf for _, conf in methods)
            consensus_value = sum(val * conf for val, conf in methods) / total_weight
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(methods)
            
            return {
                'value': round(consensus_value, 2),
                'method': 'multi_method_consensus',
                'confidence': overall_confidence,
                'methods_used': len(methods),
                'consensus_details': {
                    'method1': method1_value,
                    'method2': method2_value,
                    'method3': method3_value,
                    'method4': method4_value,
                    'method5': method5_value
                }
            }
            
        except Exception as e:
            logger.error(f"Error in multi-method validation: {e}")
            return self._fallback_processing(range_str, 0, village_context)
    
    def _calculate_context_factor(self, village_context: VillageContext, nutrient_type: NutrientType) -> float:
        """Calculate context adjustment factor"""
        try:
            soil_factor = self.context_factors['soil_type'].get(village_context.soil_type, 1.0)
            crop_factor = self.context_factors['crop_type'].get(village_context.crop_type, 1.0)
            season_factor = self.context_factors['season'].get(village_context.season, 1.0)
            rainfall_factor = self.context_factors['rainfall'].get(village_context.rainfall, 1.0)
            
            # Combine factors with nutrient-specific adjustments
            base_factor = soil_factor * crop_factor * season_factor * rainfall_factor
            
            # Nutrient-specific adjustments
            if nutrient_type == NutrientType.NITROGEN:
                # Nitrogen is more affected by rainfall and soil type
                return base_factor * 1.05
            elif nutrient_type == NutrientType.PHOSPHORUS:
                # Phosphorus is more stable
                return base_factor * 0.98
            elif nutrient_type == NutrientType.POTASSIUM:
                # Potassium is moderately affected
                return base_factor * 1.02
            else:
                # Micronutrients are more stable
                return base_factor * 0.95
                
        except Exception as e:
            logger.error(f"Error calculating context factor: {e}")
            return 1.0
    
    def _calculate_satellite_agreement(self, satellite_value: float, range_value: RangeValue) -> float:
        """Calculate agreement between satellite and ICAR range"""
        try:
            if range_value.range_width == 0:
                # Single value - calculate percentage difference
                diff = abs(satellite_value - range_value.center_value)
                return max(0, 1 - (diff / range_value.center_value))
            
            # Range value - calculate how well satellite fits
            if range_value.min_value <= satellite_value <= range_value.max_value:
                # Satellite is within range
                center_distance = abs(satellite_value - range_value.center_value)
                max_distance = range_value.range_width / 2
                return max(0, 1 - (center_distance / max_distance))
            else:
                # Satellite is outside range
                if satellite_value > range_value.max_value:
                    distance = satellite_value - range_value.max_value
                else:
                    distance = range_value.min_value - satellite_value
                
                # Calculate agreement based on distance
                range_center = range_value.center_value
                return max(0, 1 - (distance / range_center))
                
        except Exception as e:
            logger.error(f"Error calculating satellite agreement: {e}")
            return 0.5
    
    def _adjust_to_satellite(self, satellite_value: float, range_value: RangeValue) -> float:
        """Adjust ICAR value based on satellite data"""
        try:
            if range_value.range_width == 0:
                return range_value.center_value
            
            # If satellite is within range, use weighted average
            if range_value.min_value <= satellite_value <= range_value.max_value:
                return range_value.center_value * 0.7 + satellite_value * 0.3
            
            # If satellite is outside range, adjust towards it
            if satellite_value > range_value.max_value:
                return range_value.max_value * 0.8 + satellite_value * 0.2
            else:
                return range_value.min_value * 0.8 + satellite_value * 0.2
                
        except Exception as e:
            logger.error(f"Error adjusting to satellite: {e}")
            return range_value.center_value
    
    def _get_historical_average(self, historical_data: Dict, range_value: RangeValue) -> float:
        """Get historical average for validation"""
        try:
            if not historical_data or 'values' not in historical_data:
                return range_value.center_value
            
            values = historical_data['values']
            if not values:
                return range_value.center_value
            
            # Calculate average of historical values
            avg_value = sum(values) / len(values)
            
            # Ensure it's within reasonable bounds
            min_bound = range_value.min_value * 0.8
            max_bound = range_value.max_value * 1.2
            
            return max(min_bound, min(max_bound, avg_value))
            
        except Exception as e:
            logger.error(f"Error getting historical average: {e}")
            return range_value.center_value
    
    def _get_zone_typical_value(self, village_context: VillageContext, range_value: RangeValue) -> float:
        """Get zone-typical value based on village context"""
        try:
            # Zone-based adjustments
            zone_adjustments = {
                'yellow': 1.0,      # Normal zone
                'red': 1.1,         # High nutrient zone
                'green': 0.9,       # Low nutrient zone
                'orange': 1.05,     # Medium-high zone
                'grey': 0.95        # Medium-low zone
            }
            
            zone_factor = zone_adjustments.get(village_context.zone, 1.0)
            return range_value.center_value * zone_factor
            
        except Exception as e:
            logger.error(f"Error getting zone typical value: {e}")
            return range_value.center_value
    
    def _calculate_overall_confidence(self, methods: List[Tuple[float, float]]) -> float:
        """Calculate overall confidence from multiple methods"""
        try:
            if not methods:
                return 0.5
            
            # Calculate variance between methods
            values = [val for val, _ in methods]
            mean_value = sum(values) / len(values)
            variance = sum((val - mean_value) ** 2 for val in values) / len(values)
            
            # Lower variance = higher confidence
            variance_factor = max(0, 1 - (variance / mean_value) if mean_value > 0 else 0)
            
            # Average confidence of methods
            avg_confidence = sum(conf for _, conf in methods) / len(methods)
            
            # Combine variance factor with average confidence
            overall_confidence = (avg_confidence * 0.7) + (variance_factor * 0.3)
            
            return min(1.0, max(0.0, overall_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {e}")
            return 0.5
    
    def _fallback_processing(
        self, 
        range_str: str, 
        satellite_value: float, 
        village_context: VillageContext
    ) -> Dict[str, Union[float, str, float]]:
        """Fallback processing when main methods fail"""
        try:
            # Try to extract any numeric value
            numeric_pattern = r'(\d+\.?\d*)'
            match = re.search(numeric_pattern, range_str)
            
            if match:
                value = float(match.group(1))
                return {
                    'value': value,
                    'method': 'fallback_numeric',
                    'confidence': 0.3,
                    'original_range': range_str,
                    'warning': 'Fallback processing used'
                }
            
            # Ultimate fallback
            return {
                'value': satellite_value if satellite_value > 0 else 100.0,
                'method': 'fallback_default',
                'confidence': 0.1,
                'original_range': range_str,
                'warning': 'Default fallback used'
            }
            
        except Exception as e:
            logger.error(f"Error in fallback processing: {e}")
            return {
                'value': 100.0,
                'method': 'fallback_error',
                'confidence': 0.0,
                'original_range': range_str,
                'error': str(e)
            }

# Example usage and testing
if __name__ == "__main__":
    # Test the range processor
    processor = RangeProcessor()
    
    # Test data
    test_range = "380-440 kg/ha"
    test_satellite_value = 410.0
    test_context = VillageContext(
        village_name="Test Village",
        coordinates=(20.25, 81.35),
        soil_type="clay",
        crop_type="rice",
        season="kharif",
        rainfall="normal",
        zone="yellow",
        tehsil="kanker"
    )
    
    # Test AI-powered processing
    result = processor.ai_powered_range_processing(
        test_range, 
        test_satellite_value, 
        test_context,
        NutrientType.NITROGEN
    )
    
    print("🚀 Range Processor Test Results:")
    print(f"Input Range: {test_range}")
    print(f"Satellite Value: {test_satellite_value}")
    print(f"Processed Value: {result['value']}")
    print(f"Method Used: {result['method']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Context Factor: {result.get('context_factor', 'N/A')}")
    print(f"Satellite Agreement: {result.get('satellite_agreement', 'N/A'):.2f}")