#!/usr/bin/env python3
"""
Input Validator and Data Cleaner for ZumAgro APIs
Ensures all incoming data is properly formatted and validated
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

class InputValidator:
    """Comprehensive input validation and data cleaning"""
    
    def __init__(self):
        self.coordinate_pattern = re.compile(r'^-?\d+\.?\d*$')
        self.field_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
    def validate_and_clean_coordinates(self, coordinates: Union[List[float], List[List[float]], str]) -> Dict[str, Any]:
        """
        Validate and clean coordinate input
        Handles multiple formats: [lat, lon], [[lat, lon], [lat, lon]], "lat,lon"
        """
        try:
            result = {
                'success': False,
                'cleaned_coordinates': None,
                'error': None,
                'format_detected': None
            }
            
            # Handle string input
            if isinstance(coordinates, str):
                coords_str = coordinates.strip()
                if ',' in coords_str:
                    parts = coords_str.split(',')
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0].strip())
                            lon = float(parts[1].strip())
                            coordinates = [lat, lon]
                        except ValueError:
                            result['error'] = f"Invalid coordinate string format: {coordinates}"
                            return result
                    else:
                        result['error'] = f"String coordinates must have exactly 2 values: {coordinates}"
                        return result
                else:
                    result['error'] = f"String coordinates must contain comma separator: {coordinates}"
                    return result
            
            # Handle list input
            if isinstance(coordinates, list):
                if len(coordinates) == 0:
                    result['error'] = "Coordinates list cannot be empty"
                    return result
                
                # Check if it's a single coordinate pair [lat, lon]
                if len(coordinates) == 2 and all(isinstance(x, (int, float)) for x in coordinates):
                    lat, lon = coordinates
                    cleaned_coords = self._clean_single_coordinate(lat, lon)
                    if cleaned_coords:
                        result['success'] = True
                        result['cleaned_coordinates'] = [cleaned_coords]
                        result['format_detected'] = 'single_pair'
                    else:
                        result['error'] = f"Invalid coordinate values: {coordinates}"
                    return result
                
                # Check if it's multiple coordinate pairs [[lat, lon], [lat, lon], ...]
                elif all(isinstance(x, list) and len(x) == 2 for x in coordinates):
                    cleaned_coords = []
                    for i, coord_pair in enumerate(coordinates):
                        if len(coord_pair) == 2:
                            lat, lon = coord_pair
                            cleaned_coord = self._clean_single_coordinate(lat, lon)
                            if cleaned_coord:
                                cleaned_coords.append(cleaned_coord)
                            else:
                                result['error'] = f"Invalid coordinate pair at index {i}: {coord_pair}"
                                return result
                        else:
                            result['error'] = f"Each coordinate pair must have exactly 2 values at index {i}: {coord_pair}"
                            return result
                    
                    if cleaned_coords:
                        result['success'] = True
                        result['cleaned_coordinates'] = cleaned_coords
                        result['format_detected'] = 'multiple_pairs'
                    else:
                        result['error'] = "No valid coordinate pairs found"
                    return result
                
                else:
                    result['error'] = f"Invalid coordinates format. Expected [lat, lon] or [[lat, lon], ...], got: {coordinates}"
                    return result
            
            else:
                result['error'] = f"Coordinates must be a list or string, got: {type(coordinates)}"
                return result
                
        except Exception as e:
            result['error'] = f"Unexpected error validating coordinates: {str(e)}"
            return result
    
    def _clean_single_coordinate(self, lat: Union[int, float, str], lon: Union[int, float, str]) -> Optional[List[float]]:
        """Clean and validate a single coordinate pair"""
        try:
            # Convert to float
            lat_float = float(lat)
            lon_float = float(lon)
            
            # Validate latitude range (-90 to 90)
            if not (-90 <= lat_float <= 90):
                logger.warning(f"Latitude out of range: {lat_float}")
                return None
            
            # Validate longitude range (-180 to 180)
            if not (-180 <= lon_float <= 180):
                logger.warning(f"Longitude out of range: {lon_float}")
                return None
            
            # Round to reasonable precision (6 decimal places ≈ 0.1m accuracy)
            lat_rounded = round(lat_float, 6)
            lon_rounded = round(lon_float, 6)
            
            return [lat_rounded, lon_rounded]
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid coordinate values: lat={lat}, lon={lon}, error={str(e)}")
            return None
    
    def validate_and_clean_field_id(self, field_id: Any) -> Dict[str, Any]:
        """Validate and clean field ID"""
        result = {
            'success': False,
            'cleaned_field_id': None,
            'error': None
        }
        
        try:
            if field_id is None:
                result['error'] = "Field ID cannot be null"
                return result
            
            # Convert to string and clean
            field_id_str = str(field_id).strip()
            
            if not field_id_str:
                result['error'] = "Field ID cannot be empty"
                return result
            
            # Check length (reasonable limit)
            if len(field_id_str) > 100:
                result['error'] = f"Field ID too long (max 100 characters): {len(field_id_str)}"
                return result
            
            # Check for valid characters (alphanumeric, underscore, hyphen)
            if not self.field_id_pattern.match(field_id_str):
                # Clean invalid characters
                cleaned_id = re.sub(r'[^a-zA-Z0-9_-]', '_', field_id_str)
                logger.warning(f"Field ID contained invalid characters, cleaned: {field_id_str} -> {cleaned_id}")
                field_id_str = cleaned_id
            
            # Ensure it doesn't start with a number (common convention)
            if field_id_str[0].isdigit():
                field_id_str = f"field_{field_id_str}"
                logger.warning(f"Field ID started with number, prefixed 'field_': {field_id_str}")
            
            result['success'] = True
            result['cleaned_field_id'] = field_id_str
            return result
            
        except Exception as e:
            result['error'] = f"Unexpected error validating field ID: {str(e)}"
            return result
    
    def validate_and_clean_metric(self, metric: Any) -> Dict[str, Any]:
        """Validate and clean metric parameter"""
        result = {
            'success': False,
            'cleaned_metric': None,
            'error': None
        }
        
        try:
            if metric is None:
                result['cleaned_metric'] = 'npk'  # Default
                result['success'] = True
                return result
            
            metric_str = str(metric).strip().lower()
            
            # Valid metrics
            valid_metrics = ['npk', 'soil', 'vegetation', 'health', 'all']
            
            if metric_str in valid_metrics:
                result['success'] = True
                result['cleaned_metric'] = metric_str
            else:
                # Default to npk for unknown metrics
                logger.warning(f"Unknown metric '{metric}', defaulting to 'npk'")
                result['success'] = True
                result['cleaned_metric'] = 'npk'
            
            return result
            
        except Exception as e:
            result['error'] = f"Unexpected error validating metric: {str(e)}"
            return result
    
    def validate_and_clean_days(self, days: Any) -> Dict[str, Any]:
        """Validate and clean days parameter for weather API"""
        result = {
            'success': False,
            'cleaned_days': None,
            'error': None
        }
        
        try:
            if days is None:
                result['cleaned_days'] = 7  # Default
                result['success'] = True
                return result
            
            # Convert to int
            days_int = int(days)
            
            # Validate range (1 to 14 days for most weather APIs)
            if 1 <= days_int <= 14:
                result['success'] = True
                result['cleaned_days'] = days_int
            elif days_int < 1:
                logger.warning(f"Days too low ({days_int}), setting to 1")
                result['success'] = True
                result['cleaned_days'] = 1
            else:
                logger.warning(f"Days too high ({days_int}), setting to 14")
                result['success'] = True
                result['cleaned_days'] = 14
            
            return result
            
        except (ValueError, TypeError) as e:
            result['error'] = f"Invalid days value: {days}, error: {str(e)}"
            return result
    
    def validate_and_clean_time_period(self, time_period: Any) -> Dict[str, Any]:
        """Validate and clean time period for trends API"""
        result = {
            'success': False,
            'cleaned_time_period': None,
            'error': None
        }
        
        try:
            if time_period is None:
                result['cleaned_time_period'] = '30d'  # Default
                result['success'] = True
                return result
            
            time_period_str = str(time_period).strip().lower()
            
            # Valid time periods
            valid_periods = ['7d', '30d', '90d', '1y', '7days', '30days', '90days', '1year']
            
            # Map variations to standard format
            period_mapping = {
                '7d': '7d', '7days': '7d',
                '30d': '30d', '30days': '30d',
                '90d': '90d', '90days': '90d',
                '1y': '1y', '1year': '1y'
            }
            
            if time_period_str in valid_periods:
                result['success'] = True
                result['cleaned_time_period'] = period_mapping.get(time_period_str, time_period_str)
            else:
                logger.warning(f"Unknown time period '{time_period}', defaulting to '30d'")
                result['success'] = True
                result['cleaned_time_period'] = '30d'
            
            return result
            
        except Exception as e:
            result['error'] = f"Unexpected error validating time period: {str(e)}"
            return result
    
    def validate_and_clean_crop_type(self, crop_type: Any) -> Dict[str, Any]:
        """Validate and clean crop type"""
        result = {
            'success': False,
            'cleaned_crop_type': None,
            'error': None
        }
        
        try:
            if crop_type is None:
                result['cleaned_crop_type'] = 'general'  # Default
                result['success'] = True
                return result
            
            crop_type_str = str(crop_type).strip().lower()
            
            # Valid crop types
            valid_crops = ['wheat', 'rice', 'corn', 'soybean', 'cotton', 'sugarcane', 'general']
            
            if crop_type_str in valid_crops:
                result['success'] = True
                result['cleaned_crop_type'] = crop_type_str
            else:
                logger.warning(f"Unknown crop type '{crop_type}', defaulting to 'general'")
                result['success'] = True
                result['cleaned_crop_type'] = 'general'
            
            return result
            
        except Exception as e:
            result['error'] = f"Unexpected error validating crop type: {str(e)}"
            return result
    
    def validate_and_clean_analysis_type(self, analysis_type: Any) -> Dict[str, Any]:
        """Validate and clean analysis type for trends API"""
        result = {
            'success': False,
            'cleaned_analysis_type': None,
            'error': None
        }
        
        try:
            if analysis_type is None:
                result['cleaned_analysis_type'] = 'comprehensive'  # Default
                result['success'] = True
                return result
            
            analysis_type_str = str(analysis_type).strip().lower()
            
            # Valid analysis types
            valid_types = ['comprehensive', 'vegetation', 'weather', 'yield']
            
            if analysis_type_str in valid_types:
                result['success'] = True
                result['cleaned_analysis_type'] = analysis_type_str
            else:
                logger.warning(f"Unknown analysis type '{analysis_type}', defaulting to 'comprehensive'")
                result['success'] = True
                result['cleaned_analysis_type'] = 'comprehensive'
            
            return result
            
        except Exception as e:
            result['error'] = f"Unexpected error validating analysis type: {str(e)}"
            return result
    
    def validate_complete_request(self, request_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate complete request with all required fields"""
        result = {
            'success': False,
            'cleaned_data': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in request_data:
                    result['errors'].append(f"Missing required field: {field}")
            
            if result['errors']:
                return result
            
            # Validate and clean each field
            cleaned_data = {}
            
            # Field ID validation
            if 'fieldId' in request_data:
                field_id_result = self.validate_and_clean_field_id(request_data['fieldId'])
                if field_id_result['success']:
                    cleaned_data['fieldId'] = field_id_result['cleaned_field_id']
                else:
                    result['errors'].append(f"Field ID validation failed: {field_id_result['error']}")
            
            # Coordinates validation
            if 'coordinates' in request_data:
                coords_result = self.validate_and_clean_coordinates(request_data['coordinates'])
                if coords_result['success']:
                    cleaned_data['coordinates'] = coords_result['cleaned_coordinates']
                    cleaned_data['coordinate_format'] = coords_result['format_detected']
                else:
                    result['errors'].append(f"Coordinates validation failed: {coords_result['error']}")
            
            # Optional field validations
            if 'metric' in request_data:
                metric_result = self.validate_and_clean_metric(request_data['metric'])
                if metric_result['success']:
                    cleaned_data['metric'] = metric_result['cleaned_metric']
                else:
                    result['warnings'].append(f"Metric validation failed: {metric_result['error']}")
            
            if 'days' in request_data:
                days_result = self.validate_and_clean_days(request_data['days'])
                if days_result['success']:
                    cleaned_data['days'] = days_result['cleaned_days']
                else:
                    result['warnings'].append(f"Days validation failed: {days_result['error']}")
            
            if 'timePeriod' in request_data:
                period_result = self.validate_and_clean_time_period(request_data['timePeriod'])
                if period_result['success']:
                    cleaned_data['timePeriod'] = period_result['cleaned_time_period']
                else:
                    result['warnings'].append(f"Time period validation failed: {period_result['error']}")
            
            if 'cropType' in request_data:
                crop_result = self.validate_and_clean_crop_type(request_data['cropType'])
                if crop_result['success']:
                    cleaned_data['cropType'] = crop_result['cleaned_crop_type']
                else:
                    result['warnings'].append(f"Crop type validation failed: {crop_result['error']}")
            
            if 'analysisType' in request_data:
                analysis_result = self.validate_and_clean_analysis_type(request_data['analysisType'])
                if analysis_result['success']:
                    cleaned_data['analysisType'] = analysis_result['cleaned_analysis_type']
                else:
                    result['warnings'].append(f"Analysis type validation failed: {analysis_result['error']}")
            
            # Copy other fields as-is (for optional data like fieldMetrics, weatherData)
            for key, value in request_data.items():
                if key not in cleaned_data and key not in ['fieldId', 'coordinates', 'metric', 'days', 'timePeriod', 'cropType', 'analysisType']:
                    cleaned_data[key] = value
            
            result['success'] = True
            result['cleaned_data'] = cleaned_data
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Unexpected error during validation: {str(e)}")
            return result

# Global validator instance
input_validator = InputValidator()
