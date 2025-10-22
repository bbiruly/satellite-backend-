import json
import os
import math
from typing import Dict, Any, Optional, Tuple, List

class RajnandgaonDataLoader:
    _instance = None
    _data: Optional[Dict[str, Any]] = None
    _file_path: str = "rajnandgaon_soil_analysis_data/rajnandgaon_complete_soil_analysis_data.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RajnandgaonDataLoader, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        """Loads the Rajnandgaon soil analysis data from the JSON file."""
        if self._data is None:
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                print(f"✅ Rajnandgaon soil analysis data loaded successfully from {self._file_path}")
                print(f"🔍 Debug: Data keys = {list(self._data.keys())}")
                if 'village_data' in self._data:
                    print(f"🔍 Debug: Villages count = {len(self._data['village_data'].get('villages', []))}")
            except FileNotFoundError:
                print(f"❌ Error: Rajnandgaon data file not found at {self._file_path}")
                self._data = {}
            except json.JSONDecodeError:
                print(f"❌ Error: Could not decode JSON from {self._file_path}")
                self._data = {}
            except Exception as e:
                print(f"❌ An unexpected error occurred while loading Rajnandgaon data: {e}")
                self._data = {}

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (in km)."""
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def find_nearest_village(self, lat: float, lon: float, max_distance_km: float = 50) -> Optional[Dict[str, Any]]:
        """Finds the closest village in the Rajnandgaon data within a max_distance_km."""
        if not self._data or 'village_data' not in self._data:
            return None

        closest_village = None
        min_distance = float('inf')

        for village in self._data['village_data'].get('villages', []):
            village_coords = village.get('coordinates', [])
            if len(village_coords) == 2:
                village_lat, village_lon = village_coords
                distance = self._calculate_distance(lat, lon, village_lat, village_lon)

                if distance < min_distance:
                    min_distance = distance
                    closest_village = village.copy()  # Make a copy to avoid modifying original
                    closest_village['distance_km'] = round(distance, 2)

        if closest_village and closest_village['distance_km'] <= max_distance_km:
            return closest_village
        return None

    def get_zone_info(self, lat: float, lon: float, nutrient_type: str) -> Optional[Dict[str, Any]]:
        """
        Returns the zone information for a given nutrient type at specified coordinates.
        Supports 'nitrogen', 'phosphorus', 'potassium', 'boron', 'iron', 'zinc', 'soil_ph'.
        """
        if not self._data or 'nutrient_zones' not in self._data:
            return None

        zones = self._data['nutrient_zones'].get(nutrient_type.lower())
        if not zones:
            return None

        # For Rajnandgaon, we have only Singarpur village, so return its zone info
        village = self.find_nearest_village(lat, lon)
        if village:
            nutrient_level = village.get(f"{nutrient_type.lower()}_level")
            if nutrient_level:
                for zone_key, zone_data in zones.items():
                    if nutrient_level.lower() in zone_key.lower():
                        return zone_data
        return None

    def get_village_nutrient_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Returns nutrient data for the nearest village."""
        village = self.find_nearest_village(lat, lon)
        if not village:
            return None

        def parse_nutrient_value(value_str):
            """Parse nutrient value from string format like '0.5 ppm' to float"""
            if not value_str or not isinstance(value_str, str):
                return 0.0
            try:
                # Extract numeric value from string like "0.5 ppm"
                numeric_part = value_str.split()[0]
                return float(numeric_part)
            except (ValueError, IndexError):
                return 0.0

        def parse_range_value(value_str):
            """Parse range value like '10-25 kg/ha' to get average value"""
            if not value_str or not isinstance(value_str, str):
                return 0.0
            try:
                # Extract numeric range from string like "10-25 kg/ha"
                numeric_part = value_str.split()[0]  # "10-25"
                if '-' in numeric_part:
                    min_val, max_val = numeric_part.split('-')
                    return (float(min_val) + float(max_val)) / 2  # Return average
                else:
                    return float(numeric_part)
            except (ValueError, IndexError):
                return 0.0

        return {
            "village_name": village.get('village_name'),
            "district": village.get('district'),
            "tehsil": village.get('tehsil'),
            "nitrogen_level": village.get('nitrogen_level'),
            "nitrogen_value": village.get('nitrogen_value'),
            "phosphorus_level": village.get('phosphorus_level'),
            "phosphorus_value": parse_range_value(village.get('estimated_phosphorus')),
            "potassium_level": village.get('potassium_level'),
            "potassium_value": parse_nutrient_value(village.get('estimated_potassium')),
            "boron_level": village.get('boron_level'),
            "boron_value": parse_nutrient_value(village.get('estimated_boron')),
            "iron_level": village.get('iron_level'),
            "iron_value": parse_nutrient_value(village.get('estimated_iron')),
            "zinc_level": village.get('zinc_level'),
            "zinc_value": parse_nutrient_value(village.get('estimated_zinc')),
            "soil_ph_level": village.get('soil_ph_level'),
            "soil_ph_value": parse_nutrient_value(village.get('estimated_soil_ph')),
            "farmer_name": village.get('farmer_name'),
            "farm_area_acres": village.get('farm_area_acres')
        }

    def get_recommendations_by_level(self, nutrient_type: str, level: str) -> Optional[str]:
        """
        Returns the general recommendation for a given nutrient type and level from Rajnandgaon data.
        """
        if not self._data or 'statistics' not in self._data or 'recommendations' not in self._data['statistics']:
            return None
        
        recs = self._data['statistics']['recommendations']
        
        if nutrient_type.lower() == 'nitrogen':
            if level.lower() == 'low':
                return recs.get('fertilizer_recommendations', {}).get('rice_crop', {}).get('nitrogen')
        elif nutrient_type.lower() == 'phosphorus':
            if level.lower() == 'medium':
                return recs.get('fertilizer_recommendations', {}).get('rice_crop', {}).get('phosphorus')
        elif nutrient_type.lower() == 'potassium':
            if level.lower() == 'high':
                return recs.get('fertilizer_recommendations', {}).get('rice_crop', {}).get('potassium')
        
        return None

# Initialize the data loader
rajnandgaon_data_loader = RajnandgaonDataLoader()
