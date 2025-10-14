"""
Weather Data Integration
Provides real weather data for historical analysis
"""

import logging
import requests
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class WeatherDataProvider:
    """
    Provides weather data for historical analysis
    Falls back to reasonable defaults if API unavailable
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.api_key = None  # Set if weather API available
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_weather_condition(self, coordinates: Tuple[float, float], 
                            date: datetime) -> Dict[str, Any]:
        """
        Get weather condition for coordinates and date
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
        
        Returns:
            Weather data dictionary
        """
        lat, lon = coordinates
        cache_key = f"{lat:.2f}_{lon:.2f}_{date.strftime('%Y-%m-%d')}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Try to get real weather data
        weather_data = self._fetch_real_weather_data(lat, lon, date)
        
        # Cache the result
        self.cache[cache_key] = (weather_data, time.time())
        
        return weather_data
    
    def _fetch_real_weather_data(self, lat: float, lon: float, 
                                date: datetime) -> Dict[str, Any]:
        """
        Fetch real weather data from API or use intelligent defaults
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Analysis date
        
        Returns:
            Weather data dictionary
        """
        # If no API key, use intelligent defaults based on location and season
        if not self.api_key:
            return self._get_intelligent_default_weather(lat, lon, date)
        
        try:
            # Try to get current weather (simplified for demo)
            response = requests.get(
                f"{self.base_url}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "condition": data["weather"][0]["main"].lower(),
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "cloud_cover": data["clouds"]["all"],
                    "source": "api"
                }
        except Exception as e:
            logger.warning(f"Weather API error: {e}")
        
        # Fallback to intelligent defaults
        return self._get_intelligent_default_weather(lat, lon, date)
    
    def _get_intelligent_default_weather(self, lat: float, lon: float, 
                                       date: datetime) -> Dict[str, Any]:
        """
        Get intelligent default weather based on location and season
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Analysis date
        
        Returns:
            Weather data dictionary
        """
        month = date.month
        
        # Determine season based on month
        if month in [6, 7, 8, 9]:  # Monsoon season
            condition = "rainy"
            temperature = 28.0
            humidity = 80.0
            cloud_cover = 70.0
        elif month in [10, 11, 12, 1]:  # Winter
            condition = "clear"
            temperature = 22.0
            humidity = 50.0
            cloud_cover = 20.0
        else:  # Summer
            condition = "clear"
            temperature = 35.0
            humidity = 40.0
            cloud_cover = 10.0
        
        # Adjust based on location (India-specific)
        if 8.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0:  # India
            # Monsoon adjustment for India
            if month in [6, 7, 8, 9]:
                condition = "rainy"
                humidity = 85.0
                cloud_cover = 80.0
        
        return {
            "condition": condition,
            "temperature": temperature,
            "humidity": humidity,
            "cloud_cover": cloud_cover,
            "source": "intelligent_default"
        }
    
    def get_historical_weather(self, coordinates: Tuple[float, float], 
                             date: datetime) -> Dict[str, Any]:
        """
        Get historical weather data (same as current for now)
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
        
        Returns:
            Weather data dictionary
        """
        return self.get_weather_condition(coordinates, date)
    
    def calculate_seasonal_factor(self, weather_data: Dict[str, Any], 
                                date: datetime) -> float:
        """
        Calculate seasonal factor based on weather data
        
        Args:
            weather_data: Weather information
            date: Analysis date
        
        Returns:
            Seasonal factor multiplier
        """
        month = date.month
        
        # Base seasonal factor
        if month in [6, 7, 8, 9]:  # Monsoon
            base_factor = 1.2
        elif month in [10, 11, 12, 1]:  # Winter
            base_factor = 0.8
        else:  # Summer
            base_factor = 1.0
        
        # Adjust based on weather conditions
        condition = weather_data.get("condition", "clear")
        humidity = weather_data.get("humidity", 60.0)
        
        if condition == "rainy":
            base_factor *= 1.1  # Rain increases nutrient availability
        elif condition == "clear" and humidity < 40:
            base_factor *= 0.95  # Dry clear weather slightly reduces
        
        return round(base_factor, 2)

# Global instance
weather_provider = WeatherDataProvider()

def get_weather_data(coordinates: Tuple[float, float], date: datetime) -> Dict[str, Any]:
    """
    Convenience function to get weather data
    
    Args:
        coordinates: (latitude, longitude)
        date: Analysis date
    
    Returns:
        Weather data dictionary
    """
    return weather_provider.get_weather_condition(coordinates, date)
