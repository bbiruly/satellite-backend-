"""
🗺️ Coordinate Matcher Module
============================

This module handles intelligent coordinate matching and zone assignment
for ICAR 2024-25 data integration with satellite-based NPK estimation.

Features:
- Multi-layer coordinate validation
- Smart zone interpolation
- Historical pattern matching
- Distance-based village matching

Author: AI Assistant
Date: 2024
Version: 1.0
"""

import json
import math
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZoneType(Enum):
    """Zone types for nutrient classification"""
    YELLOW = "yellow"
    RED = "red"
    GREEN = "green"
    ORANGE = "orange"
    GREY = "grey"

@dataclass
class ZoneInfo:
    """Information about a nutrient zone"""
    zone_type: ZoneType
    lat_range: Tuple[float, float]
    lon_range: Tuple[float, float]
    center_lat: float
    center_lon: float
    typical_value: float
    confidence: float = 0.8

@dataclass
class VillageMatch:
    """Result of village matching"""
    village_name: str
    coordinates: Tuple[float, float]
    distance: float
    zone_matches: List[ZoneType]
    confidence: float
    method: str

class CoordinateMatcher:
    """
    Intelligent coordinate matcher for ICAR village data
    
    This class provides multiple methods for matching coordinates
    with ICAR village data and assigning appropriate zones.
    """
    
    def __init__(self, icar_data_path: str = "kanker_complete_soil_analysis_data.json"):
        """Initialize the coordinate matcher with ICAR data"""
        self.icar_data = self._load_icar_data(icar_data_path)
        self.nutrient_zones = self._extract_nutrient_zones()
        self.village_data = self._extract_village_data()
        
        # Kanker tehsil boundaries
        self.kanker_bounds = {
            'lat_min': 20.16,
            'lat_max': 20.33,
            'lon_min': 81.15,
            'lon_max': 81.49
        }
        
        # Zone definitions for each nutrient
        self.zone_definitions = {
            'nitrogen': {
                'yellow': ZoneInfo(
                    zone_type=ZoneType.YELLOW,
                    lat_range=(20.10, 20.58),
                    lon_range=(80.90, 81.40),
                    center_lat=20.34,
                    center_lon=81.15,
                    typical_value=410.0,
                    confidence=0.85
                ),
                'red': ZoneInfo(
                    zone_type=ZoneType.RED,
                    lat_range=(20.05, 20.80),
                    lon_range=(81.25, 82.00),
                    center_lat=20.425,
                    center_lon=81.625,
                    typical_value=480.0,
                    confidence=0.85
                )
            },
            'phosphorus': {
                'yellow': ZoneInfo(
                    zone_type=ZoneType.YELLOW,
                    lat_range=(20.35, 20.45),
                    lon_range=(81.40, 81.50),
                    center_lat=20.40,
                    center_lon=81.45,
                    typical_value=25.0,
                    confidence=0.80
                ),
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.50, 20.55),
                    lon_range=(81.60, 81.65),
                    center_lat=20.525,
                    center_lon=81.625,
                    typical_value=35.0,
                    confidence=0.80
                )
            },
            'potassium': {
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.16, 20.33),
                    lon_range=(81.27, 81.49),
                    center_lat=20.245,
                    center_lon=81.38,
                    typical_value=180.0,
                    confidence=0.80
                ),
                'yellow': ZoneInfo(
                    zone_type=ZoneType.YELLOW,
                    lat_range=(20.22, 20.30),
                    lon_range=(81.21, 81.49),
                    center_lat=20.26,
                    center_lon=81.35,
                    typical_value=150.0,
                    confidence=0.80
                )
            },
            'boron': {
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.20, 20.33),
                    lon_range=(81.30, 81.49),
                    center_lat=20.265,
                    center_lon=81.395,
                    typical_value=1.2,
                    confidence=0.80
                ),
                'red': ZoneInfo(
                    zone_type=ZoneType.RED,
                    lat_range=(20.16, 20.25),
                    lon_range=(81.21, 81.47),
                    center_lat=20.205,
                    center_lon=81.34,
                    typical_value=0.8,
                    confidence=0.80
                )
            },
            'iron': {
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.20, 20.32),
                    lon_range=(81.15, 81.40),
                    center_lat=20.26,
                    center_lon=81.275,
                    typical_value=8.5,
                    confidence=0.80
                ),
                'red': ZoneInfo(
                    zone_type=ZoneType.RED,
                    lat_range=(20.22, 20.26),
                    lon_range=(81.17, 81.32),
                    center_lat=20.24,
                    center_lon=81.245,
                    typical_value=5.5,
                    confidence=0.80
                )
            },
            'zinc': {
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.20, 20.32),
                    lon_range=(81.15, 81.40),
                    center_lat=20.26,
                    center_lon=81.275,
                    typical_value=1.8,
                    confidence=0.80
                ),
                'red': ZoneInfo(
                    zone_type=ZoneType.RED,
                    lat_range=(20.30, 20.33),
                    lon_range=(81.38, 81.49),
                    center_lat=20.315,
                    center_lon=81.435,
                    typical_value=1.2,
                    confidence=0.80
                )
            },
            'soil_ph': {
                'green': ZoneInfo(
                    zone_type=ZoneType.GREEN,
                    lat_range=(20.20, 20.32),
                    lon_range=(81.15, 81.40),
                    center_lat=20.26,
                    center_lon=81.275,
                    typical_value=6.8,
                    confidence=0.80
                ),
                'orange': ZoneInfo(
                    zone_type=ZoneType.ORANGE,
                    lat_range=(20.17, 20.30),
                    lon_range=(81.21, 81.49),
                    center_lat=20.235,
                    center_lon=81.35,
                    typical_value=6.2,
                    confidence=0.80
                ),
                'grey': ZoneInfo(
                    zone_type=ZoneType.GREY,
                    lat_range=(20.22, 20.22),
                    lon_range=(81.38, 81.38),
                    center_lat=20.22,
                    center_lon=81.38,
                    typical_value=5.8,
                    confidence=0.80
                )
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
    
    def _extract_nutrient_zones(self) -> Dict:
        """Extract nutrient zones from ICAR data"""
        try:
            return self.icar_data.get('nutrient_zones', {})
        except Exception as e:
            logger.error(f"Error extracting nutrient zones: {e}")
            return {}
    
    def _extract_village_data(self) -> List[Dict]:
        """Extract village data from ICAR data"""
        try:
            return self.icar_data.get('village_data', {}).get('villages', [])
        except Exception as e:
            logger.error(f"Error extracting village data: {e}")
            return []
    
    def multi_layer_coordinate_matching(
        self, 
        lat: float, 
        lon: float, 
        nutrient_type: str = 'nitrogen'
    ) -> VillageMatch:
        """
        Multi-layer coordinate matching system
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            nutrient_type: Type of nutrient for zone matching
            
        Returns:
            VillageMatch object with best match
        """
        try:
            # Layer 1: Zone-based matching
            zone_matches = self._find_villages_in_zones(lat, lon, nutrient_type)
            
            # Layer 2: Distance-based matching
            distance_matches = self._find_villages_by_distance(lat, lon)
            
            # Layer 3: Population-weighted matching
            population_matches = self._find_villages_by_population(lat, lon)
            
            # Layer 4: Nutrient-pattern matching
            pattern_matches = self._find_villages_by_nutrient_pattern(lat, lon, nutrient_type)
            
            # Combine all matches and score
            all_matches = zone_matches + distance_matches + population_matches + pattern_matches
            
            # Score villages based on which layers match
            village_scores = {}
            for match in all_matches:
                village_name = match['village_name']
                if village_name not in village_scores:
                    village_scores[village_name] = {
                        'village': match,
                        'score': 0,
                        'methods': []
                    }
                
                # Score based on method
                method_scores = {
                    'zone_based': 3,
                    'distance_based': 2,
                    'population_based': 1,
                    'pattern_based': 2
                }
                
                score = method_scores.get(match.get('method', 'unknown'), 1)
                village_scores[village_name]['score'] += score
                village_scores[village_name]['methods'].append(match.get('method', 'unknown'))
            
            # Find best match
            if village_scores:
                best_village_name = max(village_scores.keys(), key=lambda k: village_scores[k]['score'])
                best_match = village_scores[best_village_name]['village']
                
                # Calculate confidence based on score and methods
                max_possible_score = 8  # 3+2+1+2
                confidence = min(1.0, best_match['score'] / max_possible_score)
                
                return VillageMatch(
                    village_name=best_match['village_name'],
                    coordinates=(lat, lon),
                    distance=best_match.get('distance', 0),
                    zone_matches=best_match.get('zone_matches', []),
                    confidence=confidence,
                    method='multi_layer_matching'
                )
            
            # Fallback to closest village
            return self._fallback_to_closest_village(lat, lon)
            
        except Exception as e:
            logger.error(f"Error in multi-layer matching: {e}")
            return self._fallback_to_closest_village(lat, lon)
    
    def smart_zone_interpolation(
        self, 
        lat: float, 
        lon: float, 
        nutrient_type: str = 'nitrogen'
    ) -> Dict[str, Union[float, str, List[str]]]:
        """
        Smart zone interpolation for better accuracy
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            nutrient_type: Type of nutrient
            
        Returns:
            Dictionary with interpolated values and zones
        """
        try:
            if nutrient_type not in self.zone_definitions:
                return self._get_default_values(nutrient_type)
            
            zones = self.zone_definitions[nutrient_type]
            overlapping_zones = []
            
            # Find overlapping zones
            for zone_name, zone_info in zones.items():
                if self._is_point_in_zone(lat, lon, zone_info):
                    overlapping_zones.append((zone_name, zone_info))
            
            if len(overlapping_zones) == 1:
                # Single zone match
                zone_name, zone_info = overlapping_zones[0]
                return {
                    'value': zone_info.typical_value,
                    'zone': zone_name,
                    'confidence': zone_info.confidence,
                    'method': 'single_zone_match'
                }
            
            elif len(overlapping_zones) > 1:
                # Multiple zones - interpolate
                interpolated_value = 0
                total_weight = 0
                zone_names = []
                
                for zone_name, zone_info in overlapping_zones:
                    # Calculate distance from zone center
                    distance = self._calculate_distance(
                        lat, lon, 
                        zone_info.center_lat, zone_info.center_lon
                    )
                    
                    # Weight based on distance (closer = higher weight)
                    weight = 1 / (1 + distance)
                    
                    interpolated_value += zone_info.typical_value * weight
                    total_weight += weight
                    zone_names.append(zone_name)
                
                if total_weight > 0:
                    final_value = interpolated_value / total_weight
                    confidence = min(0.95, 0.8 + (len(overlapping_zones) * 0.05))
                    
                    return {
                        'value': round(final_value, 2),
                        'zone': '+'.join(zone_names),
                        'confidence': confidence,
                        'method': 'zone_interpolation',
                        'zones_count': len(overlapping_zones)
                    }
            
            # No zone match - use nearest zone
            return self._get_nearest_zone_value(lat, lon, nutrient_type)
            
        except Exception as e:
            logger.error(f"Error in zone interpolation: {e}")
            return self._get_default_values(nutrient_type)
    
    def historical_pattern_matching(
        self, 
        lat: float, 
        lon: float, 
        satellite_data: Dict,
        nutrient_type: str = 'nitrogen'
    ) -> Optional[VillageMatch]:
        """
        Match based on historical patterns
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            satellite_data: Satellite-derived data
            nutrient_type: Type of nutrient
            
        Returns:
            VillageMatch object or None
        """
        try:
            similar_villages = []
            
            for village in self.village_data:
                village_lat, village_lon = village['coordinates']
                
                # Calculate satellite pattern similarity
                pattern_similarity = self._calculate_pattern_similarity(
                    satellite_data, 
                    village_lat, 
                    village_lon,
                    nutrient_type
                )
                
                if pattern_similarity > 0.7:  # 70% similarity threshold
                    distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                    
                    similar_villages.append({
                        'village_name': village['village_name'],
                        'coordinates': (village_lat, village_lon),
                        'distance': distance,
                        'pattern_similarity': pattern_similarity,
                        'method': 'pattern_matching'
                    })
            
            if similar_villages:
                # Sort by pattern similarity
                similar_villages.sort(key=lambda x: x['pattern_similarity'], reverse=True)
                best_match = similar_villages[0]
                
                return VillageMatch(
                    village_name=best_match['village_name'],
                    coordinates=best_match['coordinates'],
                    distance=best_match['distance'],
                    zone_matches=[],
                    confidence=best_match['pattern_similarity'],
                    method='pattern_matching'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in pattern matching: {e}")
            return None
    
    def _find_villages_in_zones(self, lat: float, lon: float, nutrient_type: str) -> List[Dict]:
        """Find villages in nutrient zones"""
        try:
            matches = []
            
            if nutrient_type not in self.zone_definitions:
                return matches
            
            zones = self.zone_definitions[nutrient_type]
            
            for zone_name, zone_info in zones.items():
                if self._is_point_in_zone(lat, lon, zone_info):
                    # Find villages in this zone
                    for village in self.village_data:
                        village_lat, village_lon = village['coordinates']
                        if self._is_point_in_zone(village_lat, village_lon, zone_info):
                            distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                            
                            matches.append({
                                'village_name': village['village_name'],
                                'coordinates': (village_lat, village_lon),
                                'distance': distance,
                                'zone_matches': [zone_info.zone_type],
                                'method': 'zone_based',
                                'score': 3
                            })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding villages in zones: {e}")
            return []
    
    def _find_villages_by_distance(self, lat: float, lon: float) -> List[Dict]:
        """Find villages by distance"""
        try:
            matches = []
            
            for village in self.village_data:
                village_lat, village_lon = village['coordinates']
                distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                
                # Only consider villages within 10km
                if distance <= 10.0:
                    matches.append({
                        'village_name': village['village_name'],
                        'coordinates': (village_lat, village_lon),
                        'distance': distance,
                        'zone_matches': [],
                        'method': 'distance_based',
                        'score': 2
                    })
            
            # Sort by distance
            matches.sort(key=lambda x: x['distance'])
            return matches[:5]  # Return top 5 closest
            
        except Exception as e:
            logger.error(f"Error finding villages by distance: {e}")
            return []
    
    def _find_villages_by_population(self, lat: float, lon: float) -> List[Dict]:
        """Find villages by population (simplified)"""
        try:
            matches = []
            
            for village in self.village_data:
                village_lat, village_lon = village['coordinates']
                distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                
                # Simulate population-based scoring (larger villages get higher scores)
                population_score = hash(village['village_name']) % 100  # Simplified
                
                if distance <= 15.0:  # Within 15km
                    matches.append({
                        'village_name': village['village_name'],
                        'coordinates': (village_lat, village_lon),
                        'distance': distance,
                        'zone_matches': [],
                        'method': 'population_based',
                        'score': 1,
                        'population_score': population_score
                    })
            
            # Sort by population score
            matches.sort(key=lambda x: x['population_score'], reverse=True)
            return matches[:3]  # Return top 3 by population
            
        except Exception as e:
            logger.error(f"Error finding villages by population: {e}")
            return []
    
    def _find_villages_by_nutrient_pattern(
        self, 
        lat: float, 
        lon: float, 
        nutrient_type: str
    ) -> List[Dict]:
        """Find villages by nutrient pattern similarity"""
        try:
            matches = []
            
            # Get expected nutrient value for this location
            expected_value = self._get_expected_nutrient_value(lat, lon, nutrient_type)
            
            for village in self.village_data:
                village_lat, village_lon = village['coordinates']
                distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                
                if distance <= 20.0:  # Within 20km
                    # Get village nutrient value
                    village_value = self._get_village_nutrient_value(village, nutrient_type)
                    
                    if village_value:
                        # Calculate pattern similarity
                        pattern_similarity = 1 - abs(expected_value - village_value) / max(expected_value, village_value)
                        
                        if pattern_similarity > 0.6:  # 60% similarity threshold
                            matches.append({
                                'village_name': village['village_name'],
                                'coordinates': (village_lat, village_lon),
                                'distance': distance,
                                'zone_matches': [],
                                'method': 'pattern_based',
                                'score': 2,
                                'pattern_similarity': pattern_similarity
                            })
            
            # Sort by pattern similarity
            matches.sort(key=lambda x: x['pattern_similarity'], reverse=True)
            return matches[:3]  # Return top 3 by pattern similarity
            
        except Exception as e:
            logger.error(f"Error finding villages by nutrient pattern: {e}")
            return []
    
    def _is_point_in_zone(self, lat: float, lon: float, zone_info: ZoneInfo) -> bool:
        """Check if point is within zone boundaries"""
        try:
            return (zone_info.lat_range[0] <= lat <= zone_info.lat_range[1] and
                    zone_info.lon_range[0] <= lon <= zone_info.lon_range[1])
        except Exception as e:
            logger.error(f"Error checking point in zone: {e}")
            return False
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        try:
            # Haversine formula
            R = 6371  # Earth's radius in kilometers
            
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = (math.sin(dlat/2) * math.sin(dlat/2) +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon/2) * math.sin(dlon/2))
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return distance
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')
    
    def _calculate_pattern_similarity(
        self, 
        satellite_data: Dict, 
        village_lat: float, 
        village_lon: float,
        nutrient_type: str
    ) -> float:
        """Calculate pattern similarity between satellite and village data"""
        try:
            # Simplified pattern similarity calculation
            # In real implementation, this would compare multiple satellite indices
            
            expected_value = self._get_expected_nutrient_value(village_lat, village_lon, nutrient_type)
            satellite_value = satellite_data.get('value', expected_value)
            
            # Calculate similarity based on value difference
            if expected_value > 0:
                similarity = 1 - abs(expected_value - satellite_value) / max(expected_value, satellite_value)
                return max(0, min(1, similarity))
            
            return 0.5  # Default similarity
            
        except Exception as e:
            logger.error(f"Error calculating pattern similarity: {e}")
            return 0.5
    
    def _get_expected_nutrient_value(self, lat: float, lon: float, nutrient_type: str) -> float:
        """Get expected nutrient value for coordinates"""
        try:
            if nutrient_type not in self.zone_definitions:
                return 100.0  # Default value
            
            zones = self.zone_definitions[nutrient_type]
            
            for zone_name, zone_info in zones.items():
                if self._is_point_in_zone(lat, lon, zone_info):
                    return zone_info.typical_value
            
            # If not in any zone, return average
            avg_value = sum(zone_info.typical_value for zone_info in zones.values()) / len(zones)
            return avg_value
            
        except Exception as e:
            logger.error(f"Error getting expected nutrient value: {e}")
            return 100.0
    
    def _get_village_nutrient_value(self, village: Dict, nutrient_type: str) -> Optional[float]:
        """Get nutrient value for a village"""
        try:
            nutrient_field = f'estimated_{nutrient_type}'
            if nutrient_field in village:
                value_str = village[nutrient_field]
                # Extract numeric value from range string
                import re
                match = re.search(r'(\d+\.?\d*)', str(value_str))
                if match:
                    return float(match.group(1))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting village nutrient value: {e}")
            return None
    
    def _get_nearest_zone_value(self, lat: float, lon: float, nutrient_type: str) -> Dict:
        """Get value from nearest zone"""
        try:
            if nutrient_type not in self.zone_definitions:
                return self._get_default_values(nutrient_type)
            
            zones = self.zone_definitions[nutrient_type]
            nearest_zone = None
            min_distance = float('inf')
            
            for zone_name, zone_info in zones.items():
                distance = self._calculate_distance(
                    lat, lon, 
                    zone_info.center_lat, zone_info.center_lon
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_zone = (zone_name, zone_info)
            
            if nearest_zone:
                zone_name, zone_info = nearest_zone
                return {
                    'value': zone_info.typical_value,
                    'zone': zone_name,
                    'confidence': zone_info.confidence * 0.8,  # Reduce confidence for nearest zone
                    'method': 'nearest_zone',
                    'distance_to_zone': min_distance
                }
            
            return self._get_default_values(nutrient_type)
            
        except Exception as e:
            logger.error(f"Error getting nearest zone value: {e}")
            return self._get_default_values(nutrient_type)
    
    def _get_default_values(self, nutrient_type: str) -> Dict:
        """Get default values for nutrient type"""
        default_values = {
            'nitrogen': 400.0,
            'phosphorus': 30.0,
            'potassium': 165.0,
            'boron': 1.0,
            'iron': 7.0,
            'zinc': 1.5,
            'soil_ph': 6.5
        }
        
        return {
            'value': default_values.get(nutrient_type, 100.0),
            'zone': 'unknown',
            'confidence': 0.3,
            'method': 'default_fallback'
        }
    
    def _fallback_to_closest_village(self, lat: float, lon: float) -> VillageMatch:
        """Fallback to closest village"""
        try:
            if not self.village_data:
                return VillageMatch(
                    village_name="Unknown",
                    coordinates=(lat, lon),
                    distance=0,
                    zone_matches=[],
                    confidence=0.1,
                    method='fallback_error'
                )
            
            closest_village = min(
                self.village_data,
                key=lambda v: self._calculate_distance(lat, lon, v['coordinates'][0], v['coordinates'][1])
            )
            
            distance = self._calculate_distance(
                lat, lon, 
                closest_village['coordinates'][0], 
                closest_village['coordinates'][1]
            )
            
            return VillageMatch(
                village_name=closest_village['village_name'],
                coordinates=closest_village['coordinates'],
                distance=distance,
                zone_matches=[],
                confidence=0.5,
                method='fallback_closest'
            )
            
        except Exception as e:
            logger.error(f"Error in fallback to closest village: {e}")
            return VillageMatch(
                village_name="Error",
                coordinates=(lat, lon),
                distance=0,
                zone_matches=[],
                confidence=0.0,
                method='fallback_error'
            )

# Example usage and testing
if __name__ == "__main__":
    # Test the coordinate matcher
    matcher = CoordinateMatcher()
    
    # Test coordinates
    test_lat, test_lon = 20.25, 81.35
    
    # Test multi-layer matching
    match_result = matcher.multi_layer_coordinate_matching(test_lat, test_lon, 'nitrogen')
    
    print("🗺️ Coordinate Matcher Test Results:")
    print(f"Test Coordinates: ({test_lat}, {test_lon})")
    print(f"Matched Village: {match_result.village_name}")
    print(f"Distance: {match_result.distance:.2f} km")
    print(f"Confidence: {match_result.confidence:.2f}")
    print(f"Method: {match_result.method}")
    print(f"Zone Matches: {match_result.zone_matches}")
    
    # Test zone interpolation
    zone_result = matcher.smart_zone_interpolation(test_lat, test_lon, 'nitrogen')
    
    print("\n🎯 Zone Interpolation Results:")
    print(f"Value: {zone_result['value']}")
    print(f"Zone: {zone_result['zone']}")
    print(f"Confidence: {zone_result['confidence']:.2f}")
    print(f"Method: {zone_result['method']}")
