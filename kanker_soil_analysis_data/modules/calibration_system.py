"""
⚙️ Calibration System Module
============================

This module handles dynamic calibration and intelligent fallback mechanisms
for integrating ICAR 2024-25 data with satellite-based NPK estimation.

Features:
- Dynamic calibration system
- Multi-layer calibration
- Intelligent fallback mechanisms
- Real-time adjustment

Author: AI Assistant
Date: 2024
Version: 1.0
"""

import json
import logging
import statistics
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalibrationMethod(Enum):
    """Calibration methods"""
    SATELLITE_ADJUSTED = "satellite_adjusted"
    ZONE_BASED = "zone_based"
    HISTORICAL = "historical"
    WEIGHTED_AVERAGE = "weighted_average"
    FALLBACK = "fallback"

@dataclass
class CalibrationResult:
    """Result of calibration process"""
    calibrated_value: float
    method: CalibrationMethod
    confidence: float
    adjustment_factor: float
    original_value: float
    details: Dict[str, Union[float, str]]

@dataclass
class CalibrationLayer:
    """Calibration layer information"""
    layer_name: str
    weight: float
    value: float
    confidence: float
    method: str

class CalibrationSystem:
    """
    Dynamic calibration system for ICAR integration
    
    This class provides intelligent calibration mechanisms for
    integrating ICAR data with satellite-based NPK estimation.
    """
    
    def __init__(self, icar_data_path: str = "kanker_soil_analysis_data/kanker_complete_soil_analysis_data.json"):
        """Initialize the calibration system"""
        self.icar_data = self._load_icar_data(icar_data_path)
        self.calibration_layers = {
            'satellite': 0.4,      # 40% weight for satellite data
            'icar': 0.3,           # 30% weight for ICAR data
            'historical': 0.2,      # 20% weight for historical data
            'zone': 0.1             # 10% weight for zone data
        }
        
        # Calibration factors for different scenarios
        self.calibration_factors = {
            'high_confidence': 1.0,
            'medium_confidence': 0.9,
            'low_confidence': 0.8,
            'fallback': 0.7
        }
        
        # Nutrient-specific calibration parameters
        self.nutrient_params = {
            'nitrogen': {
                'base_range': (200, 600),
                'calibration_sensitivity': 0.8,
                'zone_weight': 0.15
            },
            'phosphorus': {
                'base_range': (10, 50),
                'calibration_sensitivity': 0.9,
                'zone_weight': 0.10
            },
            'potassium': {
                'base_range': (100, 300),
                'calibration_sensitivity': 0.85,
                'zone_weight': 0.12
            },
            'boron': {
                'base_range': (0.5, 2.0),
                'calibration_sensitivity': 0.95,
                'zone_weight': 0.08
            },
            'iron': {
                'base_range': (3, 15),
                'calibration_sensitivity': 0.9,
                'zone_weight': 0.10
            },
            'zinc': {
                'base_range': (0.5, 3.0),
                'calibration_sensitivity': 0.9,
                'zone_weight': 0.10
            },
            'soil_ph': {
                'base_range': (5.0, 8.5),
                'calibration_sensitivity': 0.95,
                'zone_weight': 0.05
            }
        }
    
    def _load_icar_data(self, data_path: str) -> Dict:
        """Load ICAR data from JSON file"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ICAR data: {e}")
            return {}
    
    def dynamic_calibration(
        self, 
        satellite_data: Dict, 
        icar_data: Dict, 
        village_context: Dict,
        nutrient_type: str = 'nitrogen'
    ) -> CalibrationResult:
        """
        Dynamic calibration system
        
        Args:
            satellite_data: Satellite-derived data
            icar_data: ICAR village data
            village_context: Village context information
            nutrient_type: Type of nutrient
            
        Returns:
            CalibrationResult object with calibrated value
        """
        try:
            # Extract values from data
            satellite_value = satellite_data.get('value', 0)
            icar_value = self._extract_numeric_value(icar_data.get('value', '0'))
            
            if satellite_value == 0 and icar_value == 0:
                return self._fallback_calibration(nutrient_type)
            
            # Create calibration layers
            layers = self._create_calibration_layers(
                satellite_data, icar_data, village_context, nutrient_type
            )
            
            # Calculate weighted calibration
            calibrated_value, method, confidence = self._calculate_weighted_calibration(
                layers, satellite_value, icar_value
            )
            
            # Apply nutrient-specific adjustments
            adjustment_factor = self._calculate_adjustment_factor(
                village_context, nutrient_type, confidence
            )
            
            final_value = calibrated_value * adjustment_factor
            
            # Ensure value is within reasonable bounds
            final_value = self._apply_bounds_check(final_value, nutrient_type)
            
            return CalibrationResult(
                calibrated_value=round(final_value, 2),
                method=method,
                confidence=confidence,
                adjustment_factor=adjustment_factor,
                original_value=icar_value,
                details={
                    'satellite_value': satellite_value,
                    'icar_value': icar_value,
                    'layers_used': len(layers),
                    'nutrient_type': nutrient_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in dynamic calibration: {e}")
            return self._fallback_calibration(nutrient_type)
    
    def multi_layer_calibration(
        self, 
        satellite_data: Dict, 
        icar_data: Dict, 
        weather_data: Dict,
        soil_data: Dict,
        village_context: Dict,
        nutrient_type: str = 'nitrogen'
    ) -> CalibrationResult:
        """
        Multi-layer calibration system
        
        Args:
            satellite_data: Satellite-derived data
            icar_data: ICAR village data
            weather_data: Weather data
            soil_data: Soil data
            village_context: Village context
            nutrient_type: Type of nutrient
            
        Returns:
            CalibrationResult object
        """
        try:
            # Create multiple calibration layers
            layers = []
            
            # Layer 1: Satellite-based calibration
            satellite_layer = self._create_satellite_layer(
                satellite_data, village_context, nutrient_type
            )
            if satellite_layer:
                layers.append(satellite_layer)
            
            # Layer 2: ICAR-based calibration
            icar_layer = self._create_icar_layer(
                icar_data, village_context, nutrient_type
            )
            if icar_layer:
                layers.append(icar_layer)
            
            # Layer 3: Weather-based calibration
            weather_layer = self._create_weather_layer(
                weather_data, village_context, nutrient_type
            )
            if weather_layer:
                layers.append(weather_layer)
            
            # Layer 4: Soil-based calibration
            soil_layer = self._create_soil_layer(
                soil_data, village_context, nutrient_type
            )
            if soil_layer:
                layers.append(soil_layer)
            
            # Layer 5: Zone-based calibration
            zone_layer = self._create_zone_layer(
                village_context, nutrient_type
            )
            if zone_layer:
                layers.append(zone_layer)
            
            if not layers:
                return self._fallback_calibration(nutrient_type)
            
            # Calculate multi-layer calibration
            calibrated_value, method, confidence = self._calculate_multi_layer_calibration(layers)
            
            # Apply final adjustments
            adjustment_factor = self._calculate_final_adjustment_factor(
                layers, village_context, nutrient_type
            )
            
            final_value = calibrated_value * adjustment_factor
            final_value = self._apply_bounds_check(final_value, nutrient_type)
            
            return CalibrationResult(
                calibrated_value=round(final_value, 2),
                method=method,
                confidence=confidence,
                adjustment_factor=adjustment_factor,
                original_value=self._extract_numeric_value(icar_data.get('value', '0')),
                details={
                    'layers_count': len(layers),
                    'layer_details': [layer.__dict__ for layer in layers],
                    'nutrient_type': nutrient_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in multi-layer calibration: {e}")
            return self._fallback_calibration(nutrient_type)
    
    def intelligent_fallback_system(
        self, 
        lat: float, 
        lon: float, 
        icar_data: Dict, 
        satellite_data: Dict,
        nutrient_type: str = 'nitrogen'
    ) -> CalibrationResult:
        """
        Intelligent fallback system
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            icar_data: ICAR village data
            satellite_data: Satellite data
            nutrient_type: Type of nutrient
            
        Returns:
            CalibrationResult object
        """
        try:
            # Try multiple fallback methods in order of preference
            
            # Method 1: Zone-based fallback
            zone_result = self._zone_based_fallback(lat, lon, nutrient_type)
            if zone_result and zone_result.confidence > 0.7:
                return zone_result
            
            # Method 2: Historical pattern fallback
            historical_result = self._historical_pattern_fallback(
                lat, lon, satellite_data, nutrient_type
            )
            if historical_result and historical_result.confidence > 0.6:
                return historical_result
            
            # Method 3: District average fallback
            district_result = self._district_average_fallback(nutrient_type)
            if district_result and district_result.confidence > 0.5:
                return district_result
            
            # Method 4: Default fallback
            return self._default_fallback(nutrient_type)
            
        except Exception as e:
            logger.error(f"Error in intelligent fallback: {e}")
            return self._default_fallback(nutrient_type)
    
    def _create_calibration_layers(
        self, 
        satellite_data: Dict, 
        icar_data: Dict, 
        village_context: Dict,
        nutrient_type: str
    ) -> List[CalibrationLayer]:
        """Create calibration layers"""
        try:
            layers = []
            
            # Satellite layer
            satellite_value = satellite_data.get('value', 0)
            if satellite_value > 0:
                layers.append(CalibrationLayer(
                    layer_name='satellite',
                    weight=self.calibration_layers['satellite'],
                    value=satellite_value,
                    confidence=0.8,
                    method='satellite_derived'
                ))
            
            # ICAR layer
            icar_value = self._extract_numeric_value(icar_data.get('value', '0'))
            if icar_value > 0:
                layers.append(CalibrationLayer(
                    layer_name='icar',
                    weight=self.calibration_layers['icar'],
                    value=icar_value,
                    confidence=0.9,
                    method='icar_lab_data'
                ))
            
            # Zone layer
            zone_value = self._get_zone_typical_value(village_context, nutrient_type)
            if zone_value > 0:
                layers.append(CalibrationLayer(
                    layer_name='zone',
                    weight=self.calibration_layers['zone'],
                    value=zone_value,
                    confidence=0.7,
                    method='zone_typical'
                ))
            
            return layers
            
        except Exception as e:
            logger.error(f"Error creating calibration layers: {e}")
            return []
    
    def _create_satellite_layer(
        self, 
        satellite_data: Dict, 
        village_context: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationLayer]:
        """Create satellite-based calibration layer"""
        try:
            satellite_value = satellite_data.get('value', 0)
            if satellite_value <= 0:
                return None
            
            # Adjust satellite value based on village context
            adjusted_value = self._adjust_satellite_value(
                satellite_value, village_context, nutrient_type
            )
            
            return CalibrationLayer(
                layer_name='satellite',
                weight=self.calibration_layers['satellite'],
                value=adjusted_value,
                confidence=0.8,
                method='satellite_adjusted'
            )
            
        except Exception as e:
            logger.error(f"Error creating satellite layer: {e}")
            return None
    
    def _create_icar_layer(
        self, 
        icar_data: Dict, 
        village_context: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationLayer]:
        """Create ICAR-based calibration layer"""
        try:
            icar_value = self._extract_numeric_value(icar_data.get('value', '0'))
            if icar_value <= 0:
                return None
            
            # Adjust ICAR value based on village context
            adjusted_value = self._adjust_icar_value(
                icar_value, village_context, nutrient_type
            )
            
            return CalibrationLayer(
                layer_name='icar',
                weight=self.calibration_layers['icar'],
                value=adjusted_value,
                confidence=0.9,
                method='icar_adjusted'
            )
            
        except Exception as e:
            logger.error(f"Error creating ICAR layer: {e}")
            return None
    
    def _create_weather_layer(
        self, 
        weather_data: Dict, 
        village_context: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationLayer]:
        """Create weather-based calibration layer"""
        try:
            if not weather_data:
                return None
            
            # Get base value for weather adjustment
            base_value = self._get_base_nutrient_value(nutrient_type)
            
            # Adjust based on weather conditions
            weather_factor = self._calculate_weather_factor(weather_data, nutrient_type)
            adjusted_value = base_value * weather_factor
            
            return CalibrationLayer(
                layer_name='weather',
                weight=0.1,  # Lower weight for weather
                value=adjusted_value,
                confidence=0.6,
                method='weather_adjusted'
            )
            
        except Exception as e:
            logger.error(f"Error creating weather layer: {e}")
            return None
    
    def _create_soil_layer(
        self, 
        soil_data: Dict, 
        village_context: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationLayer]:
        """Create soil-based calibration layer"""
        try:
            if not soil_data:
                return None
            
            # Get base value for soil adjustment
            base_value = self._get_base_nutrient_value(nutrient_type)
            
            # Adjust based on soil properties
            soil_factor = self._calculate_soil_factor(soil_data, nutrient_type)
            adjusted_value = base_value * soil_factor
            
            return CalibrationLayer(
                layer_name='soil',
                weight=0.1,  # Lower weight for soil
                value=adjusted_value,
                confidence=0.7,
                method='soil_adjusted'
            )
            
        except Exception as e:
            logger.error(f"Error creating soil layer: {e}")
            return None
    
    def _create_zone_layer(
        self, 
        village_context: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationLayer]:
        """Create zone-based calibration layer"""
        try:
            zone_value = self._get_zone_typical_value(village_context, nutrient_type)
            if zone_value <= 0:
                return None
            
            return CalibrationLayer(
                layer_name='zone',
                weight=self.calibration_layers['zone'],
                value=zone_value,
                confidence=0.7,
                method='zone_typical'
            )
            
        except Exception as e:
            logger.error(f"Error creating zone layer: {e}")
            return None
    
    def _calculate_weighted_calibration(
        self, 
        layers: List[CalibrationLayer], 
        satellite_value: float, 
        icar_value: float
    ) -> Tuple[float, CalibrationMethod, float]:
        """Calculate weighted calibration from layers"""
        try:
            if not layers:
                return self._fallback_calibration('nitrogen')
            
            # Calculate weighted average
            total_weight = sum(layer.weight for layer in layers)
            weighted_value = sum(layer.value * layer.weight for layer in layers) / total_weight
            
            # Calculate confidence based on layer confidences
            confidence = sum(layer.confidence * layer.weight for layer in layers) / total_weight
            
            # Determine method based on layers used
            if len(layers) >= 3:
                method = CalibrationMethod.WEIGHTED_AVERAGE
            elif any(layer.layer_name == 'satellite' for layer in layers):
                method = CalibrationMethod.SATELLITE_ADJUSTED
            elif any(layer.layer_name == 'zone' for layer in layers):
                method = CalibrationMethod.ZONE_BASED
            else:
                method = CalibrationMethod.HISTORICAL
            
            return weighted_value, method, confidence
            
        except Exception as e:
            logger.error(f"Error calculating weighted calibration: {e}")
            return 0, CalibrationMethod.FALLBACK, 0.0
    
    def _calculate_multi_layer_calibration(
        self, 
        layers: List[CalibrationLayer]
    ) -> Tuple[float, CalibrationMethod, float]:
        """Calculate multi-layer calibration"""
        try:
            if not layers:
                return 0, CalibrationMethod.FALLBACK, 0.0
            
            # Calculate weighted average with confidence weighting
            total_weight = sum(layer.weight for layer in layers)
            weighted_value = sum(layer.value * layer.weight for layer in layers) / total_weight
            
            # Calculate confidence with layer diversity bonus
            base_confidence = sum(layer.confidence * layer.weight for layer in layers) / total_weight
            diversity_bonus = min(0.1, len(layers) * 0.02)  # Bonus for more layers
            final_confidence = min(1.0, base_confidence + diversity_bonus)
            
            method = CalibrationMethod.WEIGHTED_AVERAGE
            
            return weighted_value, method, final_confidence
            
        except Exception as e:
            logger.error(f"Error calculating multi-layer calibration: {e}")
            return 0, CalibrationMethod.FALLBACK, 0.0
    
    def _calculate_adjustment_factor(
        self, 
        village_context: Dict, 
        nutrient_type: str, 
        confidence: float
    ) -> float:
        """Calculate adjustment factor based on context and confidence"""
        try:
            base_factor = 1.0
            
            # Confidence-based adjustment
            if confidence >= 0.9:
                base_factor *= self.calibration_factors['high_confidence']
            elif confidence >= 0.7:
                base_factor *= self.calibration_factors['medium_confidence']
            elif confidence >= 0.5:
                base_factor *= self.calibration_factors['low_confidence']
            else:
                base_factor *= self.calibration_factors['fallback']
            
            # Village context adjustments
            soil_type = village_context.get('soil_type', 'clay')
            crop_type = village_context.get('crop_type', 'rice')
            
            # Soil type adjustments
            soil_adjustments = {
                'clay': 1.05,      # Clay retains nutrients better
                'sandy': 0.95,      # Sandy soil loses nutrients faster
                'loamy': 1.0,      # Loamy soil is balanced
                'silty': 1.02      # Silty soil retains nutrients well
            }
            
            # Crop type adjustments
            crop_adjustments = {
                'rice': 1.05,      # Rice needs more nutrients
                'wheat': 1.0,      # Wheat is balanced
                'maize': 1.1,      # Maize needs more nutrients
                'sugarcane': 1.15, # Sugarcane needs high nutrients
                'cotton': 1.08     # Cotton needs moderate-high nutrients
            }
            
            soil_factor = soil_adjustments.get(soil_type, 1.0)
            crop_factor = crop_adjustments.get(crop_type, 1.0)
            
            # Nutrient-specific adjustments
            nutrient_params = self.nutrient_params.get(nutrient_type, {})
            sensitivity = nutrient_params.get('calibration_sensitivity', 0.9)
            
            final_factor = base_factor * soil_factor * crop_factor * sensitivity
            
            return min(1.2, max(0.8, final_factor))  # Limit adjustment range
            
        except Exception as e:
            logger.error(f"Error calculating adjustment factor: {e}")
            return 1.0
    
    def _calculate_final_adjustment_factor(
        self, 
        layers: List[CalibrationLayer], 
        village_context: Dict, 
        nutrient_type: str
    ) -> float:
        """Calculate final adjustment factor for multi-layer calibration"""
        try:
            # Base adjustment factor
            base_factor = self._calculate_adjustment_factor(village_context, nutrient_type, 0.8)
            
            # Layer consistency bonus
            if len(layers) >= 3:
                consistency_bonus = 1.02  # 2% bonus for multiple layers
            elif len(layers) >= 2:
                consistency_bonus = 1.01  # 1% bonus for two layers
            else:
                consistency_bonus = 1.0
            
            # High confidence bonus
            avg_confidence = sum(layer.confidence for layer in layers) / len(layers) if layers else 0.5
            if avg_confidence >= 0.8:
                confidence_bonus = 1.01
            else:
                confidence_bonus = 1.0
            
            final_factor = base_factor * consistency_bonus * confidence_bonus
            
            return min(1.15, max(0.85, final_factor))  # Limit adjustment range
            
        except Exception as e:
            logger.error(f"Error calculating final adjustment factor: {e}")
            return 1.0
    
    def _apply_bounds_check(self, value: float, nutrient_type: str) -> float:
        """Apply bounds check to ensure value is within reasonable range"""
        try:
            if nutrient_type not in self.nutrient_params:
                return value
            
            base_range = self.nutrient_params[nutrient_type]['base_range']
            min_val, max_val = base_range
            
            # Allow some flexibility (20% beyond range)
            min_bound = min_val * 0.8
            max_bound = max_val * 1.2
            
            return max(min_bound, min(max_bound, value))
            
        except Exception as e:
            logger.error(f"Error applying bounds check: {e}")
            return value
    
    def _extract_numeric_value(self, value_str: str) -> float:
        """Extract numeric value from string"""
        try:
            import re
            match = re.search(r'(\d+\.?\d*)', str(value_str))
            if match:
                return float(match.group(1))
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting numeric value: {e}")
            return 0.0
    
    def _get_zone_typical_value(self, village_context: Dict, nutrient_type: str) -> float:
        """Get zone-typical value for nutrient"""
        try:
            zone = village_context.get('zone', 'yellow')
            
            # Zone-typical values for different nutrients
            zone_values = {
                'nitrogen': {
                    'yellow': 410.0,
                    'red': 480.0,
                    'green': 350.0,
                    'orange': 430.0,
                    'grey': 380.0
                },
                'phosphorus': {
                    'yellow': 25.0,
                    'red': 35.0,
                    'green': 20.0,
                    'orange': 28.0,
                    'grey': 22.0
                },
                'potassium': {
                    'yellow': 150.0,
                    'red': 180.0,
                    'green': 120.0,
                    'orange': 160.0,
                    'grey': 140.0
                }
            }
            
            nutrient_values = zone_values.get(nutrient_type, {})
            return nutrient_values.get(zone, 100.0)  # Default value
            
        except Exception as e:
            logger.error(f"Error getting zone typical value: {e}")
            return 100.0
    
    def _get_base_nutrient_value(self, nutrient_type: str) -> float:
        """Get base nutrient value"""
        try:
            base_values = {
                'nitrogen': 400.0,
                'phosphorus': 30.0,
                'potassium': 165.0,
                'boron': 1.0,
                'iron': 7.0,
                'zinc': 1.5,
                'soil_ph': 6.5
            }
            
            return base_values.get(nutrient_type, 100.0)
            
        except Exception as e:
            logger.error(f"Error getting base nutrient value: {e}")
            return 100.0
    
    def _adjust_satellite_value(
        self, 
        satellite_value: float, 
        village_context: Dict, 
        nutrient_type: str
    ) -> float:
        """Adjust satellite value based on context"""
        try:
            # Basic adjustments based on context
            adjustment_factor = 1.0
            
            # Soil type adjustment
            soil_type = village_context.get('soil_type', 'clay')
            if soil_type == 'clay':
                adjustment_factor *= 1.05  # Clay retains nutrients better
            elif soil_type == 'sandy':
                adjustment_factor *= 0.95  # Sandy soil loses nutrients faster
            
            # Crop type adjustment
            crop_type = village_context.get('crop_type', 'rice')
            if crop_type in ['rice', 'maize']:
                adjustment_factor *= 1.05  # These crops need more nutrients
            
            return satellite_value * adjustment_factor
            
        except Exception as e:
            logger.error(f"Error adjusting satellite value: {e}")
            return satellite_value
    
    def _adjust_icar_value(
        self, 
        icar_value: float, 
        village_context: Dict, 
        nutrient_type: str
    ) -> float:
        """Adjust ICAR value based on context"""
        try:
            # ICAR values are generally more reliable, so smaller adjustments
            adjustment_factor = 1.0
            
            # Season adjustment
            season = village_context.get('season', 'kharif')
            if season == 'rabi':
                adjustment_factor *= 0.98  # Slightly lower in rabi season
            
            # Rainfall adjustment
            rainfall = village_context.get('rainfall', 'normal')
            if rainfall == 'high':
                adjustment_factor *= 0.95  # High rainfall can leach nutrients
            elif rainfall == 'low':
                adjustment_factor *= 1.02  # Low rainfall concentrates nutrients
            
            return icar_value * adjustment_factor
            
        except Exception as e:
            logger.error(f"Error adjusting ICAR value: {e}")
            return icar_value
    
    def _calculate_weather_factor(self, weather_data: Dict, nutrient_type: str) -> float:
        """Calculate weather adjustment factor"""
        try:
            factor = 1.0
            
            rainfall = weather_data.get('rainfall', 'normal')
            temperature = weather_data.get('temperature', 25)
            
            # Rainfall effects
            if rainfall == 'high':
                factor *= 0.95  # High rainfall can leach nutrients
            elif rainfall == 'low':
                factor *= 1.05  # Low rainfall concentrates nutrients
            
            # Temperature effects
            if temperature > 30:
                factor *= 0.98  # High temperature can affect nutrient availability
            elif temperature < 20:
                factor *= 1.02  # Lower temperature can slow nutrient loss
            
            return factor
            
        except Exception as e:
            logger.error(f"Error calculating weather factor: {e}")
            return 1.0
    
    def _calculate_soil_factor(self, soil_data: Dict, nutrient_type: str) -> float:
        """Calculate soil adjustment factor"""
        try:
            factor = 1.0
            
            soil_type = soil_data.get('soil_type', 'clay')
            ph_value = soil_data.get('ph', 6.5)
            
            # Soil type effects
            if soil_type == 'clay':
                factor *= 1.05  # Clay retains nutrients better
            elif soil_type == 'sandy':
                factor *= 0.95  # Sandy soil loses nutrients faster
            
            # pH effects
            if ph_value < 6.0:
                factor *= 0.98  # Acidic soil can affect nutrient availability
            elif ph_value > 7.5:
                factor *= 0.97  # Alkaline soil can affect nutrient availability
            
            return factor
            
        except Exception as e:
            logger.error(f"Error calculating soil factor: {e}")
            return 1.0
    
    def _zone_based_fallback(self, lat: float, lon: float, nutrient_type: str) -> Optional[CalibrationResult]:
        """Zone-based fallback method"""
        try:
            # Find appropriate zone based on coordinates
            zone_value = self._get_zone_typical_value({'zone': 'yellow'}, nutrient_type)
            
            return CalibrationResult(
                calibrated_value=zone_value,
                method=CalibrationMethod.ZONE_BASED,
                confidence=0.7,
                adjustment_factor=1.0,
                original_value=zone_value,
                details={'fallback_method': 'zone_based'}
            )
            
        except Exception as e:
            logger.error(f"Error in zone-based fallback: {e}")
            return None
    
    def _historical_pattern_fallback(
        self, 
        lat: float, 
        lon: float, 
        satellite_data: Dict, 
        nutrient_type: str
    ) -> Optional[CalibrationResult]:
        """Historical pattern fallback method"""
        try:
            # Use satellite data as historical pattern
            satellite_value = satellite_data.get('value', 0)
            if satellite_value <= 0:
                return None
            
            # Apply historical adjustment
            historical_factor = 0.95  # Slight reduction for historical data
            adjusted_value = satellite_value * historical_factor
            
            return CalibrationResult(
                calibrated_value=adjusted_value,
                method=CalibrationMethod.HISTORICAL,
                confidence=0.6,
                adjustment_factor=historical_factor,
                original_value=satellite_value,
                details={'fallback_method': 'historical_pattern'}
            )
            
        except Exception as e:
            logger.error(f"Error in historical pattern fallback: {e}")
            return None
    
    def _district_average_fallback(self, nutrient_type: str) -> Optional[CalibrationResult]:
        """District average fallback method"""
        try:
            # Get district average from ICAR data
            if not self.icar_data or 'village_data' not in self.icar_data:
                return None
            
            villages = self.icar_data['village_data'].get('villages', [])
            if not villages:
                return None
            
            # Calculate average for nutrient type
            nutrient_field = f'estimated_{nutrient_type}'
            values = []
            
            for village in villages:
                if nutrient_field in village:
                    value = self._extract_numeric_value(village[nutrient_field])
                    if value > 0:
                        values.append(value)
            
            if values:
                avg_value = statistics.mean(values)
                return CalibrationResult(
                    calibrated_value=avg_value,
                    method=CalibrationMethod.HISTORICAL,
                    confidence=0.5,
                    adjustment_factor=1.0,
                    original_value=avg_value,
                    details={'fallback_method': 'district_average', 'samples': len(values)}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in district average fallback: {e}")
            return None
    
    def _default_fallback(self, nutrient_type: str) -> CalibrationResult:
        """Default fallback method"""
        try:
            default_value = self._get_base_nutrient_value(nutrient_type)
            
            return CalibrationResult(
                calibrated_value=default_value,
                method=CalibrationMethod.FALLBACK,
                confidence=0.3,
                adjustment_factor=1.0,
                original_value=default_value,
                details={'fallback_method': 'default'}
            )
            
        except Exception as e:
            logger.error(f"Error in default fallback: {e}")
            return CalibrationResult(
                calibrated_value=100.0,
                method=CalibrationMethod.FALLBACK,
                confidence=0.1,
                adjustment_factor=1.0,
                original_value=100.0,
                details={'fallback_method': 'error', 'error': str(e)}
            )
    
    def _fallback_calibration(self, nutrient_type: str) -> CalibrationResult:
        """Fallback calibration when main methods fail"""
        try:
            default_value = self._get_base_nutrient_value(nutrient_type)
            
            return CalibrationResult(
                calibrated_value=default_value,
                method=CalibrationMethod.FALLBACK,
                confidence=0.3,
                adjustment_factor=1.0,
                original_value=default_value,
                details={'fallback_reason': 'main_calibration_failed'}
            )
            
        except Exception as e:
            logger.error(f"Error in fallback calibration: {e}")
            return CalibrationResult(
                calibrated_value=100.0,
                method=CalibrationMethod.FALLBACK,
                confidence=0.1,
                adjustment_factor=1.0,
                original_value=100.0,
                details={'fallback_reason': 'error', 'error': str(e)}
            )

# Example usage and testing
if __name__ == "__main__":
    # Test the calibration system
    calibrator = CalibrationSystem()
    
    # Test data
    test_satellite_data = {'value': 410.0}
    test_icar_data = {'value': '380-440 kg/ha'}
    test_village_context = {
        'village_name': 'Test Village',
        'coordinates': [20.25, 81.35],
        'soil_type': 'clay',
        'crop_type': 'rice',
        'season': 'kharif',
        'rainfall': 'normal',
        'zone': 'yellow'
    }
    
    # Test dynamic calibration
    calibration_result = calibrator.dynamic_calibration(
        test_satellite_data, test_icar_data, test_village_context, 'nitrogen'
    )
    
    print("⚙️ Calibration System Test Results:")
    print(f"Calibrated Value: {calibration_result.calibrated_value}")
    print(f"Method: {calibration_result.method.value}")
    print(f"Confidence: {calibration_result.confidence:.2f}")
    print(f"Adjustment Factor: {calibration_result.adjustment_factor:.2f}")
    print(f"Original Value: {calibration_result.original_value}")
    print(f"Details: {calibration_result.details}")
    
    # Test multi-layer calibration
    test_weather_data = {'rainfall': 'normal', 'temperature': 25, 'humidity': 60}
    test_soil_data = {'soil_type': 'clay', 'ph': 6.8}
    
    multi_layer_result = calibrator.multi_layer_calibration(
        test_satellite_data, test_icar_data, test_weather_data, test_soil_data, test_village_context, 'nitrogen'
    )
    
    print("\n🔧 Multi-Layer Calibration Results:")
    print(f"Calibrated Value: {multi_layer_result.calibrated_value}")
    print(f"Method: {multi_layer_result.method.value}")
    print(f"Confidence: {multi_layer_result.confidence:.2f}")
    print(f"Layers Count: {multi_layer_result.details.get('layers_count', 0)}")
    
    # Test intelligent fallback
    fallback_result = calibrator.intelligent_fallback_system(
        20.25, 81.35, test_icar_data, test_satellite_data, 'nitrogen'
    )
    
    print("\n🔄 Intelligent Fallback Results:")
    print(f"Calibrated Value: {fallback_result.calibrated_value}")
    print(f"Method: {fallback_result.method.value}")
    print(f"Confidence: {fallback_result.confidence:.2f}")
    print(f"Fallback Method: {fallback_result.details.get('fallback_method', 'unknown')}")
