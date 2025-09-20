#!/usr/bin/env python3
"""
Simple Input Validator - Minimal but Effective
Focuses on essential validation without over-engineering
"""

import re
import logging
from typing import Dict, Any, List, Union, Optional

logger = logging.getLogger(__name__)

class SimpleValidator:
    """Minimal input validation focused on essential safety"""
    
    @staticmethod
    def clean_coordinates(coords: Union[List[float], str]) -> List[float]:
        """Clean coordinates - handle string format"""
        if isinstance(coords, str):
            try:
                lat, lon = map(float, coords.split(','))
                return [lat, lon]
            except:
                raise ValueError(f"Invalid coordinate string: {coords}")
        
        if isinstance(coords, list) and len(coords) == 2:
            lat, lon = float(coords[0]), float(coords[1])
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError(f"Coordinates out of range: lat={lat}, lon={lon}")
            return [lat, lon]
        
        raise ValueError(f"Invalid coordinates format: {coords}")
    
    @staticmethod
    def clean_field_id(field_id: str) -> str:
        """Clean field ID - remove dangerous characters"""
        if not field_id or not isinstance(field_id, str):
            raise ValueError("Field ID is required")
        
        # Remove dangerous characters, keep alphanumeric + underscore + hyphen
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', field_id.strip())
        
        # Ensure it doesn't start with number
        if cleaned[0].isdigit():
            cleaned = f"field_{cleaned}"
        
        return cleaned[:50]  # Reasonable length limit
    
    @staticmethod
    def clean_metric(metric: str) -> str:
        """Clean metric - default to npk if invalid"""
        valid_metrics = ['npk', 'soil', 'vegetation', 'health', 'all']
        return metric if metric in valid_metrics else 'npk'
    
    @staticmethod
    def clean_days(days: int) -> int:
        """Clean days - limit to reasonable range"""
        return max(1, min(14, int(days)))
    
    @staticmethod
    def validate_request(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Simple request validation"""
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Clean the data
        cleaned = {}
        
        # Clean field ID
        if 'fieldId' in data:
            cleaned['fieldId'] = SimpleValidator.clean_field_id(data['fieldId'])
        
        # Clean coordinates
        if 'coordinates' in data:
            cleaned['coordinates'] = SimpleValidator.clean_coordinates(data['coordinates'])
        
        # Clean optional fields
        if 'metric' in data:
            cleaned['metric'] = SimpleValidator.clean_metric(data['metric'])
        
        if 'days' in data:
            cleaned['days'] = SimpleValidator.clean_days(data['days'])
        
        # Copy other fields as-is
        for key, value in data.items():
            if key not in cleaned:
                cleaned[key] = value
        
        return cleaned

# Global simple validator
simple_validator = SimpleValidator()
