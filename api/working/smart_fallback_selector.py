"""
Smart Fallback Selector
Intelligently selects optimal satellite based on weather, location, and crop conditions
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class SmartFallbackSelector:
    """
    Intelligent satellite selection based on various conditions
    """
    
    def __init__(self):
        self.weather_cache = {}
        self.weather_cache_ttl = 3600  # 1 hour cache for weather data
        
    def select_optimal_satellite(self, coordinates: Tuple[float, float], 
                                date: datetime, crop_type: str, 
                                weather_condition: Optional[str] = None) -> List[str]:
        """
        Select optimal satellite order based on conditions
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
            crop_type: Type of crop
            weather_condition: Weather condition (optional)
        
        Returns:
            List of satellite names in optimal order
        """
        lat, lon = coordinates
        
        # Get weather condition if not provided
        if not weather_condition:
            weather_condition = self._get_weather_condition(coordinates, date)
        
        # Check if location is remote
        is_remote = self._is_remote_area(coordinates)
        
        # Check if location is in high-resolution priority area
        is_high_res_priority = self._is_high_resolution_priority(coordinates)
        
        # Determine optimal order based on conditions
        if weather_condition in ['cloudy', 'rainy', 'overcast']:
            # Cloudy weather - prefer MODIS (better cloud penetration)
            logger.info(f"🌧️ Cloudy weather detected, prioritizing MODIS")
            return ['modis', 'landsat', 'sentinel2', 'icar_only']
        
        elif is_remote:
            # Remote area - prefer satellites over ICAR
            logger.info(f"🏔️ Remote area detected, prioritizing satellites")
            return ['sentinel2', 'landsat', 'modis', 'icar_only']
        
        elif is_high_res_priority:
            # High-resolution priority area - prefer Sentinel-2
            logger.info(f"🎯 High-resolution priority area, prioritizing Sentinel-2")
            return ['sentinel2', 'landsat', 'modis', 'icar_only']
        
        elif crop_type in ['RICE', 'WHEAT', 'CORN']:
            # High-value crops - prefer high resolution
            logger.info(f"🌾 High-value crop ({crop_type}), prioritizing high resolution")
            return ['sentinel2', 'landsat', 'modis', 'icar_only']
        
        elif crop_type in ['VEGETABLES', 'FRUITS']:
            # Precision agriculture - prefer high resolution
            logger.info(f"🥬 Precision agriculture crop ({crop_type}), prioritizing high resolution")
            return ['sentinel2', 'landsat', 'modis', 'icar_only']
        
        elif self._is_rapid_growth_crop(crop_type):
            # Rapid growth crops - prefer frequent revisit
            logger.info(f"🌱 Rapid growth crop ({crop_type}), prioritizing frequent revisit")
            return ['modis', 'sentinel2', 'landsat', 'icar_only']
        
        else:
            # Default order
            logger.info(f"📡 Using default satellite order")
            return ['sentinel2', 'landsat', 'modis', 'icar_only']
    
    def _get_weather_condition(self, coordinates: Tuple[float, float], 
                              date: datetime) -> str:
        """
        Get weather condition for coordinates and date
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
        
        Returns:
            Weather condition string
        """
        lat, lon = coordinates
        cache_key = f"{lat:.2f}_{lon:.2f}_{date.strftime('%Y-%m-%d')}"
        
        # Check cache first
        if cache_key in self.weather_cache:
            cached_data, timestamp = self.weather_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.weather_cache_ttl:
                return cached_data
        
        try:
            # Try to get weather data (simplified - in real implementation, use weather API)
            weather_condition = self._fetch_weather_data(lat, lon, date)
            
            # Cache the result
            self.weather_cache[cache_key] = (weather_condition, datetime.now())
            
            return weather_condition
            
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch weather data: {e}")
            return "unknown"
    
    def _fetch_weather_data(self, lat: float, lon: float, date: datetime) -> str:
        """
        Fetch weather data from external API (placeholder implementation)
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Analysis date
        
        Returns:
            Weather condition string
        """
        # This is a placeholder - in real implementation, integrate with weather API
        # For now, return a default condition
        return "clear"
    
    def _is_remote_area(self, coordinates: Tuple[float, float]) -> bool:
        """
        Check if location is remote (far from villages)
        
        Args:
            coordinates: (latitude, longitude)
        
        Returns:
            True if remote area, False otherwise
        """
        try:
            from .icar_only_analysis import find_nearest_villages
            villages = find_nearest_villages(coordinates, max_distance_km=25.0)
            return len(villages) == 0
        except Exception as e:
            logger.warning(f"⚠️ Could not check remote area status: {e}")
            return False
    
    def _is_high_resolution_priority(self, coordinates: Tuple[float, float]) -> bool:
        """
        Check if location is in high-resolution priority area
        
        Args:
            coordinates: (latitude, longitude)
        
        Returns:
            True if high-resolution priority, False otherwise
        """
        lat, lon = coordinates
        
        # Define high-resolution priority areas (example regions)
        high_res_areas = [
            # Rajnandgaon district
            (21.8, 21.9, 81.9, 82.1),
            # Kanker district
            (20.1, 20.6, 81.1, 81.5),
            # Add more priority areas as needed
        ]
        
        for min_lat, max_lat, min_lon, max_lon in high_res_areas:
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                return True
        
        return False
    
    def _is_rapid_growth_crop(self, crop_type: str) -> bool:
        """
        Check if crop has rapid growth requiring frequent monitoring
        
        Args:
            crop_type: Type of crop
        
        Returns:
            True if rapid growth crop, False otherwise
        """
        rapid_growth_crops = [
            'LETTUCE', 'SPINACH', 'RADISH', 'CUCUMBER', 'TOMATO',
            'PEPPER', 'HERBS', 'MICROGREENS'
        ]
        
        return crop_type.upper() in rapid_growth_crops
    
    def get_selection_reason(self, coordinates: Tuple[float, float], 
                           date: datetime, crop_type: str, 
                           selected_order: List[str]) -> str:
        """
        Get human-readable reason for satellite selection
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
            crop_type: Type of crop
            selected_order: Selected satellite order
        
        Returns:
            Reason string
        """
        weather_condition = self._get_weather_condition(coordinates, date)
        is_remote = self._is_remote_area(coordinates)
        is_high_res = self._is_high_resolution_priority(coordinates)
        is_rapid_growth = self._is_rapid_growth_crop(crop_type)
        
        if weather_condition in ['cloudy', 'rainy', 'overcast']:
            return f"Cloudy weather conditions detected - prioritizing MODIS for better cloud penetration"
        elif is_remote:
            return f"Remote area detected - prioritizing satellite data over ICAR"
        elif is_high_res:
            return f"High-resolution priority area - prioritizing Sentinel-2 for detailed analysis"
        elif crop_type in ['RICE', 'WHEAT', 'CORN']:
            return f"High-value crop ({crop_type}) - prioritizing high-resolution satellite data"
        elif is_rapid_growth:
            return f"Rapid growth crop ({crop_type}) - prioritizing frequent revisit satellites"
        else:
            return f"Standard conditions - using default satellite priority order"
    
    def get_optimal_timeout(self, satellite: str, weather_condition: str) -> int:
        """
        Get optimal timeout for satellite based on conditions
        
        Args:
            satellite: Satellite name
            weather_condition: Weather condition
        
        Returns:
            Timeout in seconds
        """
        base_timeouts = {
            'sentinel2': 30,
            'landsat': 25,
            'modis': 20,
            'icar_only': 5
        }
        
        base_timeout = base_timeouts.get(satellite, 30)
        
        # Adjust timeout based on weather
        if weather_condition in ['cloudy', 'rainy']:
            return int(base_timeout * 1.5)  # Increase timeout for bad weather
        elif weather_condition == 'clear':
            return int(base_timeout * 0.8)  # Decrease timeout for clear weather
        else:
            return base_timeout
    
    def should_skip_satellite(self, satellite: str, coordinates: Tuple[float, float], 
                            date: datetime, crop_type: str) -> bool:
        """
        Determine if a satellite should be skipped based on conditions
        
        Args:
            satellite: Satellite name
            coordinates: (latitude, longitude)
            date: Analysis date
            crop_type: Type of crop
        
        Returns:
            True if should skip, False otherwise
        """
        weather_condition = self._get_weather_condition(coordinates, date)
        
        # Skip Sentinel-2 in very cloudy conditions
        if satellite == 'sentinel2' and weather_condition in ['heavy_rain', 'storm']:
            logger.info(f"⏭️ Skipping Sentinel-2 due to heavy weather conditions")
            return True
        
        # Skip MODIS for high-resolution priority areas
        if satellite == 'modis' and self._is_high_resolution_priority(coordinates):
            logger.info(f"⏭️ Skipping MODIS for high-resolution priority area")
            return True
        
        # Skip Landsat for rapid growth crops (need frequent monitoring)
        if satellite == 'landsat' and self._is_rapid_growth_crop(crop_type):
            logger.info(f"⏭️ Skipping Landsat for rapid growth crop")
            return True
        
        return False

# Global instance
smart_selector = SmartFallbackSelector()

def get_optimal_satellite_order(coordinates: Tuple[float, float], 
                               date: datetime, crop_type: str, 
                               weather_condition: Optional[str] = None) -> List[str]:
    """
    Convenience function to get optimal satellite order
    
    Args:
        coordinates: (latitude, longitude)
        date: Analysis date
        crop_type: Type of crop
        weather_condition: Weather condition (optional)
    
    Returns:
        List of satellite names in optimal order
    """
    return smart_selector.select_optimal_satellite(coordinates, date, crop_type, weather_condition)

def get_selection_reason(coordinates: Tuple[float, float], 
                        date: datetime, crop_type: str, 
                        selected_order: List[str]) -> str:
    """
    Convenience function to get selection reason
    
    Args:
        coordinates: (latitude, longitude)
        date: Analysis date
        crop_type: Type of crop
        selected_order: Selected satellite order
    
    Returns:
        Reason string
    """
    return smart_selector.get_selection_reason(coordinates, date, crop_type, selected_order)
