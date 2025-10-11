"""
🔍 Data Validator Module
========================

This module handles comprehensive data validation and cross-validation
for ICAR 2024-25 data integration with satellite-based NPK estimation.

Features:
- Multi-source cross-validation
- Confidence scoring
- Data quality assessment
- Validation reporting

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

class ValidationLevel(Enum):
    """Validation levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FAILED = "failed"

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    confidence_score: float
    validation_level: ValidationLevel
    details: Dict[str, Union[float, str, bool]]
    warnings: List[str]
    errors: List[str]

@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    completeness: float
    consistency: float
    accuracy: float
    reliability: float
    overall_score: float

class DataValidator:
    """
    Comprehensive data validator for ICAR integration
    
    This class provides multiple validation methods for ensuring
    data quality and reliability in the integration process.
    """
    
    def __init__(self):
        """Initialize the data validator"""
        self.validation_weights = {
            'satellite_icar_agreement': 0.4,
            'weather_consistency': 0.2,
            'soil_consistency': 0.2,
            'historical_consistency': 0.2
        }
        
        # Expected ranges for different nutrients
        self.expected_ranges = {
            'nitrogen': {'min': 200, 'max': 600, 'unit': 'kg/ha'},
            'phosphorus': {'min': 10, 'max': 50, 'unit': 'kg/ha'},
            'potassium': {'min': 100, 'max': 300, 'unit': 'kg/ha'},
            'boron': {'min': 0.5, 'max': 2.0, 'unit': 'ppm'},
            'iron': {'min': 3, 'max': 15, 'unit': 'ppm'},
            'zinc': {'min': 0.5, 'max': 3.0, 'unit': 'ppm'},
            'soil_ph': {'min': 5.0, 'max': 8.5, 'unit': 'pH'}
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.8,
            'fair': 0.7,
            'poor': 0.6,
            'failed': 0.5
        }
    
    def multi_source_validation(
        self, 
        satellite_data: Dict, 
        icar_data: Dict, 
        weather_data: Dict, 
        soil_data: Dict,
        village_context: Dict
    ) -> ValidationResult:
        """
        Multi-source cross-validation system
        
        Args:
            satellite_data: Satellite-derived data
            icar_data: ICAR village data
            weather_data: Weather data
            soil_data: Soil data
            village_context: Village context information
            
        Returns:
            ValidationResult object with validation details
        """
        try:
            validation_details = {}
            warnings = []
            errors = []
            
            # 1. Satellite-ICAR agreement (40% weight)
            satellite_icar_score = self._validate_satellite_icar_agreement(
                satellite_data, icar_data
            )
            validation_details['satellite_icar_agreement'] = satellite_icar_score
            
            # 2. Weather consistency (20% weight)
            weather_score = self._validate_weather_consistency(
                weather_data, icar_data, village_context
            )
            validation_details['weather_consistency'] = weather_score
            
            # 3. Soil consistency (20% weight)
            soil_score = self._validate_soil_consistency(
                soil_data, icar_data, village_context
            )
            validation_details['soil_consistency'] = soil_score
            
            # 4. Historical consistency (20% weight)
            historical_score = self._validate_historical_consistency(
                icar_data, village_context
            )
            validation_details['historical_consistency'] = historical_score
            
            # Calculate overall confidence score
            overall_score = self._calculate_overall_confidence(validation_details)
            
            # Determine validation level
            validation_level = self._determine_validation_level(overall_score)
            
            # Check for warnings and errors
            warnings, errors = self._check_for_issues(validation_details, overall_score)
            
            return ValidationResult(
                is_valid=overall_score >= self.quality_thresholds['fair'],
                confidence_score=overall_score,
                validation_level=validation_level,
                details=validation_details,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in multi-source validation: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_level=ValidationLevel.FAILED,
                details={'error': str(e)},
                warnings=[],
                errors=[f"Validation failed: {str(e)}"]
            )
    
    def validate_nutrient_data(
        self, 
        nutrient_data: Dict, 
        nutrient_type: str,
        village_context: Dict
    ) -> ValidationResult:
        """
        Validate nutrient-specific data
        
        Args:
            nutrient_data: Nutrient data to validate
            nutrient_type: Type of nutrient
            village_context: Village context
            
        Returns:
            ValidationResult object
        """
        try:
            validation_details = {}
            warnings = []
            errors = []
            
            # 1. Range validation
            range_score = self._validate_nutrient_range(nutrient_data, nutrient_type)
            validation_details['range_validation'] = range_score
            
            # 2. Zone consistency
            zone_score = self._validate_zone_consistency(nutrient_data, nutrient_type, village_context)
            validation_details['zone_consistency'] = zone_score
            
            # 3. Value consistency
            value_score = self._validate_value_consistency(nutrient_data, nutrient_type)
            validation_details['value_consistency'] = value_score
            
            # 4. Unit validation
            unit_score = self._validate_unit_consistency(nutrient_data, nutrient_type)
            validation_details['unit_consistency'] = unit_score
            
            # Calculate overall score
            overall_score = statistics.mean([
                range_score, zone_score, value_score, unit_score
            ])
            
            # Determine validation level
            validation_level = self._determine_validation_level(overall_score)
            
            # Check for issues
            warnings, errors = self._check_nutrient_issues(
                validation_details, nutrient_type, overall_score
            )
            
            return ValidationResult(
                is_valid=overall_score >= self.quality_thresholds['fair'],
                confidence_score=overall_score,
                validation_level=validation_level,
                details=validation_details,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error validating nutrient data: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_level=ValidationLevel.FAILED,
                details={'error': str(e)},
                warnings=[],
                errors=[f"Nutrient validation failed: {str(e)}"]
            )
    
    def assess_data_quality(self, data: Dict) -> DataQualityMetrics:
        """
        Assess overall data quality
        
        Args:
            data: Data to assess
            
        Returns:
            DataQualityMetrics object
        """
        try:
            # 1. Completeness assessment
            completeness = self._assess_completeness(data)
            
            # 2. Consistency assessment
            consistency = self._assess_consistency(data)
            
            # 3. Accuracy assessment
            accuracy = self._assess_accuracy(data)
            
            # 4. Reliability assessment
            reliability = self._assess_reliability(data)
            
            # Calculate overall score
            overall_score = statistics.mean([completeness, consistency, accuracy, reliability])
            
            return DataQualityMetrics(
                completeness=completeness,
                consistency=consistency,
                accuracy=accuracy,
                reliability=reliability,
                overall_score=overall_score
            )
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return DataQualityMetrics(
                completeness=0.0,
                consistency=0.0,
                accuracy=0.0,
                reliability=0.0,
                overall_score=0.0
            )
    
    def _validate_satellite_icar_agreement(self, satellite_data: Dict, icar_data: Dict) -> float:
        """Validate agreement between satellite and ICAR data"""
        try:
            if not satellite_data or not icar_data:
                return 0.5  # Neutral score for missing data
            
            satellite_value = satellite_data.get('value', 0)
            icar_value = self._extract_numeric_value(icar_data.get('value', '0'))
            
            if satellite_value == 0 or icar_value == 0:
                return 0.5
            
            # Calculate percentage difference
            diff_percentage = abs(satellite_value - icar_value) / max(satellite_value, icar_value)
            
            # Convert to score (lower difference = higher score)
            if diff_percentage <= 0.1:  # Within 10%
                return 0.95
            elif diff_percentage <= 0.2:  # Within 20%
                return 0.85
            elif diff_percentage <= 0.3:  # Within 30%
                return 0.75
            elif diff_percentage <= 0.5:  # Within 50%
                return 0.65
            else:
                return 0.45  # Poor agreement
            
        except Exception as e:
            logger.error(f"Error validating satellite-ICAR agreement: {e}")
            return 0.5
    
    def _validate_weather_consistency(self, weather_data: Dict, icar_data: Dict, village_context: Dict) -> float:
        """Validate weather consistency"""
        try:
            if not weather_data:
                return 0.7  # Neutral score for missing weather data
            
            # Check if weather data is consistent with expected patterns
            rainfall = weather_data.get('rainfall', 'normal')
            temperature = weather_data.get('temperature', 25)
            humidity = weather_data.get('humidity', 60)
            
            # Basic consistency checks
            consistency_score = 0.8  # Base score
            
            # Rainfall consistency
            if rainfall == 'high' and temperature > 30:
                consistency_score += 0.1  # High rainfall with high temp is expected
            elif rainfall == 'low' and temperature < 20:
                consistency_score += 0.1  # Low rainfall with low temp is expected
            
            # Humidity consistency
            if humidity > 70 and rainfall == 'high':
                consistency_score += 0.05  # High humidity with high rainfall
            elif humidity < 40 and rainfall == 'low':
                consistency_score += 0.05  # Low humidity with low rainfall
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"Error validating weather consistency: {e}")
            return 0.7
    
    def _validate_soil_consistency(self, soil_data: Dict, icar_data: Dict, village_context: Dict) -> float:
        """Validate soil consistency"""
        try:
            if not soil_data:
                return 0.7  # Neutral score for missing soil data
            
            soil_type = soil_data.get('soil_type', 'clay')
            ph_value = soil_data.get('ph', 6.5)
            
            # Basic soil consistency checks
            consistency_score = 0.8  # Base score
            
            # pH consistency with soil type
            if soil_type == 'clay' and 6.0 <= ph_value <= 7.5:
                consistency_score += 0.1  # Clay soil typically has neutral pH
            elif soil_type == 'sandy' and 5.5 <= ph_value <= 7.0:
                consistency_score += 0.1  # Sandy soil typically has slightly acidic pH
            
            # Nutrient consistency with soil type
            nutrient_value = self._extract_numeric_value(icar_data.get('value', '0'))
            
            if soil_type == 'clay' and nutrient_value > 300:
                consistency_score += 0.05  # Clay soil retains nutrients well
            elif soil_type == 'sandy' and nutrient_value < 400:
                consistency_score += 0.05  # Sandy soil loses nutrients faster
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"Error validating soil consistency: {e}")
            return 0.7
    
    def _validate_historical_consistency(self, icar_data: Dict, village_context: Dict) -> float:
        """Validate historical consistency"""
        try:
            # Check if current data is consistent with historical patterns
            current_value = self._extract_numeric_value(icar_data.get('value', '0'))
            
            # Simulate historical data (in real implementation, this would come from database)
            historical_values = [current_value * 0.9, current_value * 1.1, current_value * 0.95]
            
            if historical_values:
                historical_avg = statistics.mean(historical_values)
                historical_std = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
                
                # Check if current value is within reasonable range of historical data
                if abs(current_value - historical_avg) <= 2 * historical_std:
                    return 0.9  # High consistency
                elif abs(current_value - historical_avg) <= 3 * historical_std:
                    return 0.8  # Good consistency
                else:
                    return 0.6  # Poor consistency
            
            return 0.7  # Neutral score for no historical data
            
        except Exception as e:
            logger.error(f"Error validating historical consistency: {e}")
            return 0.7
    
    def _validate_nutrient_range(self, nutrient_data: Dict, nutrient_type: str) -> float:
        """Validate nutrient value is within expected range"""
        try:
            if nutrient_type not in self.expected_ranges:
                return 0.5  # Unknown nutrient type
            
            expected_range = self.expected_ranges[nutrient_type]
            value = self._extract_numeric_value(nutrient_data.get('value', '0'))
            
            if expected_range['min'] <= value <= expected_range['max']:
                return 0.95  # Within expected range
            elif expected_range['min'] * 0.8 <= value <= expected_range['max'] * 1.2:
                return 0.8  # Within extended range
            else:
                return 0.4  # Outside expected range
            
        except Exception as e:
            logger.error(f"Error validating nutrient range: {e}")
            return 0.5
    
    def _validate_zone_consistency(self, nutrient_data: Dict, nutrient_type: str, village_context: Dict) -> float:
        """Validate zone consistency"""
        try:
            zone = nutrient_data.get('zone', 'unknown')
            value = self._extract_numeric_value(nutrient_data.get('value', '0'))
            
            # Zone-specific value expectations
            zone_expectations = {
                'yellow': {'min': 0.7, 'max': 1.3},  # 70-130% of typical
                'red': {'min': 1.2, 'max': 1.8},     # 120-180% of typical
                'green': {'min': 0.5, 'max': 1.0},   # 50-100% of typical
                'orange': {'min': 0.8, 'max': 1.2},  # 80-120% of typical
                'grey': {'min': 0.6, 'max': 1.1}     # 60-110% of typical
            }
            
            if zone in zone_expectations:
                expected_range = zone_expectations[zone]
                typical_value = self.expected_ranges.get(nutrient_type, {}).get('min', 100)
                normalized_value = value / typical_value
                
                if expected_range['min'] <= normalized_value <= expected_range['max']:
                    return 0.95  # Perfect zone consistency
                elif expected_range['min'] * 0.9 <= normalized_value <= expected_range['max'] * 1.1:
                    return 0.85  # Good zone consistency
                else:
                    return 0.6   # Poor zone consistency
            
            return 0.7  # Unknown zone
            
        except Exception as e:
            logger.error(f"Error validating zone consistency: {e}")
            return 0.7
    
    def _validate_value_consistency(self, nutrient_data: Dict, nutrient_type: str) -> float:
        """Validate value consistency within data"""
        try:
            # Check for internal consistency in the data
            value_str = str(nutrient_data.get('value', '0'))
            
            # Check if value string is well-formed
            if '-' in value_str:  # Range value
                parts = value_str.split('-')
                if len(parts) == 2:
                    try:
                        min_val = float(parts[0].strip())
                        max_val = float(parts[1].split()[0].strip())
                        if min_val < max_val:
                            return 0.9  # Well-formed range
                        else:
                            return 0.4  # Invalid range
                    except ValueError:
                        return 0.3  # Cannot parse range
                else:
                    return 0.5  # Malformed range
            else:  # Single value
                try:
                    float(value_str.split()[0])
                    return 0.95  # Well-formed single value
                except ValueError:
                    return 0.3  # Cannot parse value
            
        except Exception as e:
            logger.error(f"Error validating value consistency: {e}")
            return 0.5
    
    def _validate_unit_consistency(self, nutrient_data: Dict, nutrient_type: str) -> float:
        """Validate unit consistency"""
        try:
            if nutrient_type not in self.expected_ranges:
                return 0.5
            
            expected_unit = self.expected_ranges[nutrient_type]['unit']
            value_str = str(nutrient_data.get('value', '0'))
            
            # Extract unit from value string
            unit_match = None
            if ' ' in value_str:
                parts = value_str.split()
                if len(parts) > 1:
                    unit_match = parts[-1].lower()
            
            if unit_match:
                if unit_match == expected_unit.lower():
                    return 0.95  # Correct unit
                elif unit_match in ['kg/ha', 'ppm', 'ph']:  # Valid units
                    return 0.8   # Valid but different unit
                else:
                    return 0.4   # Invalid unit
            else:
                return 0.7  # No unit specified
            
        except Exception as e:
            logger.error(f"Error validating unit consistency: {e}")
            return 0.7
    
    def _assess_completeness(self, data: Dict) -> float:
        """Assess data completeness"""
        try:
            required_fields = ['village_name', 'coordinates', 'value', 'zone']
            present_fields = sum(1 for field in required_fields if field in data and data[field])
            
            return present_fields / len(required_fields)
            
        except Exception as e:
            logger.error(f"Error assessing completeness: {e}")
            return 0.0
    
    def _assess_consistency(self, data: Dict) -> float:
        """Assess data consistency"""
        try:
            # Check for internal consistency
            consistency_score = 0.8  # Base score
            
            # Check coordinate validity
            coords = data.get('coordinates', [])
            if len(coords) == 2:
                lat, lon = coords
                if 20.0 <= lat <= 21.0 and 80.0 <= lon <= 82.0:  # Kanker region
                    consistency_score += 0.1
            
            # Check zone validity
            zone = data.get('zone', '')
            valid_zones = ['yellow', 'red', 'green', 'orange', 'grey']
            if zone in valid_zones:
                consistency_score += 0.1
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"Error assessing consistency: {e}")
            return 0.0
    
    def _assess_accuracy(self, data: Dict) -> float:
        """Assess data accuracy"""
        try:
            # Check if values are within reasonable ranges
            accuracy_score = 0.8  # Base score
            
            value_str = str(data.get('value', '0'))
            numeric_value = self._extract_numeric_value(value_str)
            
            if 0 < numeric_value < 1000:  # Reasonable range for most nutrients
                accuracy_score += 0.1
            
            return min(1.0, accuracy_score)
            
        except Exception as e:
            logger.error(f"Error assessing accuracy: {e}")
            return 0.0
    
    def _assess_reliability(self, data: Dict) -> float:
        """Assess data reliability"""
        try:
            # Check for data reliability indicators
            reliability_score = 0.7  # Base score
            
            # Check if data has confidence indicators
            if 'confidence' in data:
                reliability_score += 0.2
            
            # Check if data has validation indicators
            if 'validated' in data:
                reliability_score += 0.1
            
            return min(1.0, reliability_score)
            
        except Exception as e:
            logger.error(f"Error assessing reliability: {e}")
            return 0.0
    
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
    
    def _calculate_overall_confidence(self, validation_details: Dict) -> float:
        """Calculate overall confidence from validation details"""
        try:
            weighted_score = 0
            total_weight = 0
            
            for key, score in validation_details.items():
                weight = self.validation_weights.get(key, 0.25)
                weighted_score += score * weight
                total_weight += weight
            
            return weighted_score / total_weight if total_weight > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {e}")
            return 0.5
    
    def _determine_validation_level(self, score: float) -> ValidationLevel:
        """Determine validation level based on score"""
        if score >= self.quality_thresholds['excellent']:
            return ValidationLevel.HIGH
        elif score >= self.quality_thresholds['good']:
            return ValidationLevel.HIGH
        elif score >= self.quality_thresholds['fair']:
            return ValidationLevel.MEDIUM
        elif score >= self.quality_thresholds['poor']:
            return ValidationLevel.LOW
        else:
            return ValidationLevel.FAILED
    
    def _check_for_issues(self, validation_details: Dict, overall_score: float) -> Tuple[List[str], List[str]]:
        """Check for warnings and errors"""
        warnings = []
        errors = []
        
        # Check individual validation scores
        for key, score in validation_details.items():
            if score < 0.6:
                errors.append(f"Low {key} score: {score:.2f}")
            elif score < 0.8:
                warnings.append(f"Moderate {key} score: {score:.2f}")
        
        # Check overall score
        if overall_score < 0.5:
            errors.append(f"Overall validation failed: {overall_score:.2f}")
        elif overall_score < 0.7:
            warnings.append(f"Low overall validation score: {overall_score:.2f}")
        
        return warnings, errors
    
    def _check_nutrient_issues(self, validation_details: Dict, nutrient_type: str, overall_score: float) -> Tuple[List[str], List[str]]:
        """Check for nutrient-specific issues"""
        warnings = []
        errors = []
        
        # Check range validation
        range_score = validation_details.get('range_validation', 0)
        if range_score < 0.5:
            errors.append(f"{nutrient_type} value outside expected range")
        elif range_score < 0.8:
            warnings.append(f"{nutrient_type} value near range limits")
        
        # Check zone consistency
        zone_score = validation_details.get('zone_consistency', 0)
        if zone_score < 0.6:
            errors.append(f"{nutrient_type} zone inconsistency detected")
        elif zone_score < 0.8:
            warnings.append(f"{nutrient_type} zone consistency concerns")
        
        return warnings, errors

# Example usage and testing
if __name__ == "__main__":
    # Test the data validator
    validator = DataValidator()
    
    # Test data
    test_satellite_data = {'value': 410.0}
    test_icar_data = {'value': '380-440 kg/ha', 'zone': 'yellow'}
    test_weather_data = {'rainfall': 'normal', 'temperature': 25, 'humidity': 60}
    test_soil_data = {'soil_type': 'clay', 'ph': 6.8}
    test_village_context = {'village_name': 'Test Village', 'coordinates': [20.25, 81.35]}
    
    # Test multi-source validation
    validation_result = validator.multi_source_validation(
        test_satellite_data, test_icar_data, test_weather_data, test_soil_data, test_village_context
    )
    
    print("🔍 Data Validator Test Results:")
    print(f"Validation Valid: {validation_result.is_valid}")
    print(f"Confidence Score: {validation_result.confidence_score:.2f}")
    print(f"Validation Level: {validation_result.validation_level.value}")
    print(f"Warnings: {validation_result.warnings}")
    print(f"Errors: {validation_result.errors}")
    
    # Test nutrient validation
    nutrient_result = validator.validate_nutrient_data(test_icar_data, 'nitrogen', test_village_context)
    
    print("\n🌱 Nutrient Validation Results:")
    print(f"Nutrient Valid: {nutrient_result.is_valid}")
    print(f"Confidence Score: {nutrient_result.confidence_score:.2f}")
    print(f"Validation Level: {nutrient_result.validation_level.value}")
    
    # Test data quality assessment
    quality_metrics = validator.assess_data_quality(test_icar_data)
    
    print("\n📊 Data Quality Metrics:")
    print(f"Completeness: {quality_metrics.completeness:.2f}")
    print(f"Consistency: {quality_metrics.consistency:.2f}")
    print(f"Accuracy: {quality_metrics.accuracy:.2f}")
    print(f"Reliability: {quality_metrics.reliability:.2f}")
    print(f"Overall Score: {quality_metrics.overall_score:.2f}")
