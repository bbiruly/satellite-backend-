"""
Kanker Data Loader Module
Loads and queries the Kanker soil analysis data from JSON file
"""

import json
import math
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class KankerDataLoader:
    """Class to load and query Kanker soil analysis data"""
    
    def __init__(self, data_file_path: str = None):
        """
        Initialize Kanker data loader
        
        Args:
            data_file_path: Path to Kanker soil analysis JSON file
        """
        if data_file_path is None:
            # Default path relative to this file
            current_dir = Path(__file__).parent.parent.parent
            data_file_path = current_dir / "kanker_soil_analysis_data" / "kanker_complete_soil_analysis_data.json"
        
        self.data_file_path = data_file_path
        self.data = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load Kanker soil analysis data from JSON file"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ Kanker data loaded successfully from {self.data_file_path}")
        except FileNotFoundError:
            print(f"❌ Error: Kanker data file not found at {self.data_file_path}")
            self.data = None
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in Kanker data file - {e}")
            self.data = None
        except Exception as e:
            print(f"❌ Error loading Kanker data: {e}")
            self.data = None
    
    def is_data_loaded(self) -> bool:
        """Check if data is successfully loaded"""
        return self.data is not None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data"""
        if not self.is_data_loaded():
            return {"error": "Data not loaded"}
        
        villages = self.data.get('village_data', {}).get('villages', [])
        
        return {
            "total_villages": len(villages),
            "data_structure": list(self.data.keys()),
            "sample_village": villages[0] if villages else None,
            "zones_available": list(self.data.get('nutrient_zones', {}).keys()),
            "statistics_available": list(self.data.get('statistics', {}).keys())
        }
    
    def find_nearest_village(self, lat: float, lon: float, max_distance_km: float = 50.0) -> Optional[Dict[str, Any]]:
        """
        Find nearest village in Kanker data
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_km: Maximum distance to search (km)
            
        Returns:
            Dictionary with village data and distance, or None if not found
        """
        if not self.is_data_loaded():
            return None
        
        villages = self.data.get('village_data', {}).get('villages', [])
        if not villages:
            return None
        
        min_distance = float('inf')
        nearest_village = None
        
        for village in villages:
            coords = village.get('coordinates', [])
            if len(coords) == 2:
                v_lat, v_lon = coords
                distance = self._calculate_distance(lat, lon, v_lat, v_lon)
                
                if distance < min_distance and distance <= max_distance_km:
                    min_distance = distance
                    nearest_village = village
        
        if nearest_village:
            return {
                "village_data": nearest_village,
                "distance_km": round(min_distance, 2),
                "coordinates": nearest_village.get('coordinates', []),
                "village_name": nearest_village.get('village_name', 'Unknown')
            }
        
        return None
    
    def get_village_nutrient_data(self, village_name: str) -> Optional[Dict[str, Any]]:
        """
        Get nutrient data for specific village
        
        Args:
            village_name: Name of the village
            
        Returns:
            Village nutrient data or None if not found
        """
        if not self.is_data_loaded():
            return None
        
        villages = self.data.get('village_data', {}).get('villages', [])
        
        for village in villages:
            if village.get('village_name', '').lower() == village_name.lower():
                return {
                    "village_name": village.get('village_name'),
                    "coordinates": village.get('coordinates', []),
                    "nitrogen_level": village.get('nitrogen_level'),
                    "nitrogen_value": village.get('nitrogen_value'),
                    "estimated_nitrogen": village.get('estimated_nitrogen'),
                    "phosphorus_level": village.get('phosphorus_level'),
                    "estimated_phosphorus": village.get('estimated_phosphorus'),
                    "potassium_level": village.get('potassium_level'),
                    "estimated_potassium": village.get('estimated_potassium'),
                    "zinc_level": village.get('zinc_level'),
                    "estimated_zinc": village.get('estimated_zinc'),
                    "boron_level": village.get('boron_level'),
                    "estimated_boron": village.get('estimated_boron'),
                    "iron_level": village.get('iron_level'),
                    "estimated_iron": village.get('estimated_iron'),
                    "ph_level": village.get('ph_level'),
                    "estimated_ph": village.get('estimated_ph')
                }
        
        return None
    
    def get_zone_information(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get zone information for given coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Zone information dictionary
        """
        if not self.is_data_loaded():
            return {"error": "Data not loaded"}
        
        zones = self.data.get('nutrient_zones', {})
        zone_info = {
            "coordinates": [lat, lon],
            "nitrogen_zone": self._identify_nitrogen_zone(lat, lon, zones),
            "phosphorus_zone": self._identify_phosphorus_zone(lat, lon, zones),
            "potassium_zone": self._identify_potassium_zone(lat, lon, zones)
        }
        
        return zone_info
    
    def get_zone_recommendations(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get zone-based recommendations from Kanker data
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Zone recommendations dictionary
        """
        if not self.is_data_loaded():
            return {"error": "Data not loaded"}
        
        zones = self.data.get('nutrient_zones', {})
        recommendations = self.data.get('statistics', {}).get('recommendations', {})
        
        zone_info = self.get_zone_information(lat, lon)
        
        return {
            "zone_info": zone_info,
            "fertilizer_recommendations": recommendations.get('fertilizer_recommendations', {}),
            "zone_strategy": recommendations.get('zone_wise_strategy', ''),
            "general_recommendations": recommendations.get('general_recommendations', {})
        }
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get statistics summary from Kanker data"""
        if not self.is_data_loaded():
            return {"error": "Data not loaded"}
        
        stats = self.data.get('statistics', {})
        
        return {
            "nutrient_statistics": stats.get('nutrient_statistics', {}),
            "zone_statistics": stats.get('zone_statistics', {}),
            "recommendations": stats.get('recommendations', {}),
            "summary": stats.get('summary', {})
        }
    
    def get_villages_in_range(self, lat: float, lon: float, radius_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Get all villages within specified radius
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of villages within radius
        """
        if not self.is_data_loaded():
            return []
        
        villages = self.data.get('village_data', {}).get('villages', [])
        villages_in_range = []
        
        for village in villages:
            coords = village.get('coordinates', [])
            if len(coords) == 2:
                v_lat, v_lon = coords
                distance = self._calculate_distance(lat, lon, v_lat, v_lon)
                
                if distance <= radius_km:
                    villages_in_range.append({
                        "village_data": village,
                        "distance_km": round(distance, 2),
                        "village_name": village.get('village_name', 'Unknown')
                    })
        
        # Sort by distance
        villages_in_range.sort(key=lambda x: x['distance_km'])
        
        return villages_in_range
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def _identify_nitrogen_zone(self, lat: float, lon: float, zones: Dict) -> Dict[str, Any]:
        """Identify nitrogen zone for given coordinates"""
        nitrogen_zones = zones.get('nitrogen', {})
        
        # Check if coordinates fall within zone boundaries
        for zone_name, zone_data in nitrogen_zones.items():
            lat_range = zone_data.get('lat_range', [])
            lon_range = zone_data.get('lon_range', [])
            
            if (len(lat_range) == 2 and len(lon_range) == 2 and
                lat_range[0] <= lat <= lat_range[1] and
                lon_range[0] <= lon <= lon_range[1]):
                
                return {
                    "zone_name": zone_name,
                    "zone_description": zone_data.get('description', ''),
                    "nitrogen_range": zone_data.get('nitrogen_range', []),
                    "villages_count": zone_data.get('villages_count', 0),
                    "characteristics": zone_data.get('characteristics', ''),
                    "recommendation": zone_data.get('recommendation', '')
                }
        
        return {
            "zone_name": "unknown",
            "zone_description": "Zone not identified",
            "nitrogen_range": [],
            "villages_count": 0,
            "characteristics": "Unknown",
            "recommendation": "Manual verification needed"
        }
    
    def _identify_phosphorus_zone(self, lat: float, lon: float, zones: Dict) -> Dict[str, Any]:
        """Identify phosphorus zone for given coordinates"""
        phosphorus_zones = zones.get('phosphorus', {})
        
        # For now, return general phosphorus zone info
        # In future, can be enhanced with specific coordinate-based zones
        return {
            "zone_name": "general_phosphorus_zone",
            "zone_description": "General phosphorus zone",
            "phosphorus_range": [0, 40],
            "villages_count": 91,
            "characteristics": "Mixed phosphorus levels",
            "recommendation": "Apply phosphorus based on soil test"
        }
    
    def _identify_potassium_zone(self, lat: float, lon: float, zones: Dict) -> Dict[str, Any]:
        """Identify potassium zone for given coordinates"""
        potassium_zones = zones.get('potassium', {})
        
        # For now, return general potassium zone info
        return {
            "zone_name": "general_potassium_zone",
            "zone_description": "General potassium zone",
            "potassium_range": [0, 250],
            "villages_count": 91,
            "characteristics": "Mixed potassium levels",
            "recommendation": "Apply potassium based on soil test"
        }
    
    def search_villages_by_nutrient_level(self, nutrient: str, level: str) -> List[Dict[str, Any]]:
        """
        Search villages by nutrient level
        
        Args:
            nutrient: Nutrient name (nitrogen, phosphorus, potassium, zinc, boron, iron)
            level: Level (low, medium, high, very_high)
            
        Returns:
            List of villages matching criteria
        """
        if not self.is_data_loaded():
            return []
        
        villages = self.data.get('village_data', {}).get('villages', [])
        matching_villages = []
        
        for village in villages:
            nutrient_level = village.get(f'{nutrient}_level', '').lower()
            if nutrient_level == level.lower():
                matching_villages.append({
                    "village_name": village.get('village_name'),
                    "coordinates": village.get('coordinates', []),
                    f"{nutrient}_level": village.get(f'{nutrient}_level'),
                    f"estimated_{nutrient}": village.get(f'estimated_{nutrient}')
                })
        
        return matching_villages
    
    def get_nutrient_distribution(self, nutrient: str) -> Dict[str, Any]:
        """
        Get distribution statistics for specific nutrient
        
        Args:
            nutrient: Nutrient name
            
        Returns:
            Distribution statistics
        """
        if not self.is_data_loaded():
            return {"error": "Data not loaded"}
        
        villages = self.data.get('village_data', {}).get('villages', [])
        
        levels = {}
        values = []
        
        for village in villages:
            level = village.get(f'{nutrient}_level', 'unknown')
            value = village.get(f'{nutrient}_value')
            
            if level not in levels:
                levels[level] = 0
            levels[level] += 1
            
            if value is not None:
                values.append(value)
        
        return {
            "nutrient": nutrient,
            "level_distribution": levels,
            "total_villages": len(villages),
            "villages_with_values": len(values),
            "average_value": sum(values) / len(values) if values else 0,
            "min_value": min(values) if values else 0,
            "max_value": max(values) if values else 0
        }

# Global instance for easy access
kanker_loader = KankerDataLoader()

# Export main class and instance
__all__ = [
    "KankerDataLoader",
    "kanker_loader"
]
