"""
Weather Service for ZumAgro
Agricultural Weather Data Integration
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
import sys
from functools import lru_cache

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from weather_config import WEATHER_API_KEY
except ImportError:
    WEATHER_API_KEY = "YOUR_WEATHERAPI_KEY_HERE"

logger = logging.getLogger(__name__)

class WeatherService:
    """Weather service for agricultural weather data"""
    
    def __init__(self):
        # Use API key from config file
        self.api_key = os.getenv("WEATHER_API_KEY", WEATHER_API_KEY)
        self.base_url = "http://api.weatherapi.com/v1"
        self.cache_ttl = 3600  # 1 hour cache
        self._cache = {}
        
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather conditions for field location"""
        try:
            cache_key = f"current_{lat}_{lon}"
            
            # Check cache first
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.info(f"🌤️ [WEATHER] Using cached current weather for {lat}, {lon}")
                    return cached_data
            
            # Fetch from API
            url = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": f"{lat},{lon}",
                "aqi": "yes"  # Air quality index
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Process and format data
                weather_data = self._process_current_weather(data)
                
                # Cache the result
                self._cache[cache_key] = (weather_data, datetime.now())
                
                logger.info(f"🌤️ [WEATHER] Current weather fetched for {lat}, {lon}")
                return weather_data
                
        except Exception as e:
            logger.error(f"🌤️ [WEATHER] Error fetching current weather: {str(e)}")
            return self._get_fallback_weather()
    
    async def get_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast for field location"""
        try:
            cache_key = f"forecast_{lat}_{lon}_{days}"
            
            # Check cache first
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.info(f"🌤️ [WEATHER] Using cached forecast for {lat}, {lon}")
                    return cached_data
            
            # Fetch from API
            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": f"{lat},{lon}",
                "days": days,
                "aqi": "yes",
                "alerts": "yes"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Process and format data
                forecast_data = self._process_forecast(data)
                
                # Cache the result
                self._cache[cache_key] = (forecast_data, datetime.now())
                
                logger.info(f"🌤️ [WEATHER] Forecast fetched for {lat}, {lon} ({days} days)")
                return forecast_data
                
        except Exception as e:
            logger.error(f"🌤️ [WEATHER] Error fetching forecast: {str(e)}")
            return self._get_fallback_forecast()
    
    async def get_historical_weather(self, lat: float, lon: float, date: str) -> Dict[str, Any]:
        """Get historical weather data for field location"""
        try:
            cache_key = f"historical_{lat}_{lon}_{date}"
            
            # Check cache first
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.info(f"🌤️ [WEATHER] Using cached historical weather for {lat}, {lon}")
                    return cached_data
            
            # Fetch from API
            url = f"{self.base_url}/history.json"
            params = {
                "key": self.api_key,
                "q": f"{lat},{lon}",
                "dt": date,
                "aqi": "yes"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Process and format data
                historical_data = self._process_historical_weather(data)
                
                # Cache the result
                self._cache[cache_key] = (historical_data, datetime.now())
                
                logger.info(f"🌤️ [WEATHER] Historical weather fetched for {lat}, {lon} on {date}")
                return historical_data
                
        except Exception as e:
            logger.error(f"🌤️ [WEATHER] Error fetching historical weather: {str(e)}")
            return self._get_fallback_weather()
    
    def _process_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process current weather data for agricultural use"""
        current = data.get("current", {})
        location = data.get("location", {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "name": location.get("name", "Unknown"),
                "region": location.get("region", "Unknown"),
                "country": location.get("country", "Unknown"),
                "lat": location.get("lat", 0),
                "lon": location.get("lon", 0)
            },
            "current": {
                "temperature": {
                    "celsius": current.get("temp_c", 0),
                    "fahrenheit": current.get("temp_f", 0),
                    "feels_like_c": current.get("feelslike_c", 0),
                    "feels_like_f": current.get("feelslike_f", 0)
                },
                "humidity": current.get("humidity", 0),
                "pressure": {
                    "mb": current.get("pressure_mb", 0),
                    "in": current.get("pressure_in", 0)
                },
                "wind": {
                    "speed_kph": current.get("wind_kph", 0),
                    "speed_mph": current.get("wind_mph", 0),
                    "direction": current.get("wind_dir", "N"),
                    "degree": current.get("wind_degree", 0)
                },
                "precipitation": {
                    "mm": current.get("precip_mm", 0),
                    "inches": current.get("precip_in", 0)
                },
                "visibility": {
                    "km": current.get("vis_km", 0),
                    "miles": current.get("vis_miles", 0)
                },
                "uv_index": current.get("uv", 0),
                "condition": {
                    "text": current.get("condition", {}).get("text", "Unknown"),
                    "icon": current.get("condition", {}).get("icon", ""),
                    "code": current.get("condition", {}).get("code", 0)
                },
                "air_quality": self._process_air_quality(current.get("air_quality", {}))
            },
            "agricultural_indicators": self._calculate_agricultural_indicators(current),
            # Add flat structure for compatibility with existing code
            "temperature": current.get("temp_c", 0),
            "humidity": current.get("humidity", 0),
            "pressure": current.get("pressure_mb", 0),
            "wind_speed": current.get("wind_kph", 0),
            "wind_direction": current.get("wind_degree", 0),
            "visibility": current.get("vis_km", 0),
            "uv_index": current.get("uv", 0),
            "cloud_cover": current.get("cloud", 0),
            "precip_mm": current.get("precip_mm", 0)
        }
    
    def _process_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process forecast data for agricultural use"""
        forecast = data.get("forecast", {}).get("forecastday", [])
        location = data.get("location", {})
        
        processed_forecast = []
        for day in forecast:
            processed_day = {
                "date": day.get("date", ""),
                "day": {
                    "max_temp_c": day.get("day", {}).get("maxtemp_c", 0),
                    "min_temp_c": day.get("day", {}).get("mintemp_c", 0),
                    "avg_temp_c": day.get("day", {}).get("avgtemp_c", 0),
                    "max_wind_kph": day.get("day", {}).get("maxwind_kph", 0),
                    "total_precip_mm": day.get("day", {}).get("totalprecip_mm", 0),
                    "avg_humidity": day.get("day", {}).get("avghumidity", 0),
                    "condition": {
                        "text": day.get("day", {}).get("condition", {}).get("text", "Unknown"),
                        "icon": day.get("day", {}).get("condition", {}).get("icon", "")
                    },
                    "uv": day.get("day", {}).get("uv", 0)
                },
                "agricultural_indicators": self._calculate_agricultural_indicators(day.get("day", {}))
            }
            processed_forecast.append(processed_day)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "name": location.get("name", "Unknown"),
                "region": location.get("region", "Unknown"),
                "country": location.get("country", "Unknown"),
                "lat": location.get("lat", 0),
                "lon": location.get("lon", 0)
            },
            "forecast": processed_forecast,
            "alerts": self._process_alerts(data.get("alerts", {}))
        }
    
    def _process_historical_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process historical weather data"""
        # Similar to current weather processing
        return self._process_current_weather(data)
    
    def _process_air_quality(self, air_quality: Dict[str, Any]) -> Dict[str, Any]:
        """Process air quality data"""
        return {
            "co": air_quality.get("co", 0),
            "no2": air_quality.get("no2", 0),
            "o3": air_quality.get("o3", 0),
            "pm2_5": air_quality.get("pm2_5", 0),
            "pm10": air_quality.get("pm10", 0),
            "so2": air_quality.get("so2", 0),
            "us_epa_index": air_quality.get("us-epa-index", 0),
            "gb_defra_index": air_quality.get("gb-defra-index", 0)
        }
    
    def _process_alerts(self, alerts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process weather alerts"""
        alert_list = alerts.get("alert", [])
        processed_alerts = []
        
        for alert in alert_list:
            processed_alerts.append({
                "headline": alert.get("headline", ""),
                "msgtype": alert.get("msgtype", ""),
                "severity": alert.get("severity", ""),
                "urgency": alert.get("urgency", ""),
                "areas": alert.get("areas", ""),
                "category": alert.get("category", ""),
                "certainty": alert.get("certainty", ""),
                "event": alert.get("event", ""),
                "note": alert.get("note", ""),
                "effective": alert.get("effective", ""),
                "expires": alert.get("expires", ""),
                "desc": alert.get("desc", ""),
                "instruction": alert.get("instruction", "")
            })
        
        return processed_alerts
    
    def _calculate_agricultural_indicators(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate agricultural-specific weather indicators"""
        temp_c = weather_data.get("temp_c", weather_data.get("avgtemp_c", 0))
        humidity = weather_data.get("humidity", weather_data.get("avghumidity", 0))
        wind_kph = weather_data.get("wind_kph", weather_data.get("maxwind_kph", 0))
        precip_mm = weather_data.get("precip_mm", weather_data.get("totalprecip_mm", 0))
        uv = weather_data.get("uv", 0)
        
        # Agricultural indicators
        indicators = {
            "crop_stress": self._calculate_crop_stress(temp_c, humidity, wind_kph),
            "irrigation_need": self._calculate_irrigation_need(precip_mm, humidity, temp_c),
            "pest_risk": self._calculate_pest_risk(temp_c, humidity),
            "disease_risk": self._calculate_disease_risk(humidity, precip_mm),
            "harvest_conditions": self._calculate_harvest_conditions(temp_c, humidity, wind_kph, precip_mm),
            "planting_conditions": self._calculate_planting_conditions(temp_c, precip_mm, wind_kph),
            "fertilizer_timing": self._calculate_fertilizer_timing(precip_mm, wind_kph),
            "uv_damage_risk": self._calculate_uv_damage_risk(uv)
        }
        
        return indicators
    
    def _calculate_crop_stress(self, temp: float, humidity: float, wind: float) -> str:
        """Calculate crop stress level"""
        if temp > 35 or humidity < 30:
            return "high"
        elif temp > 30 or humidity < 40:
            return "moderate"
        else:
            return "low"
    
    def _calculate_irrigation_need(self, precip: float, humidity: float, temp: float) -> str:
        """Calculate irrigation need"""
        if precip < 5 and humidity < 50 and temp > 25:
            return "high"
        elif precip < 10 and humidity < 60:
            return "moderate"
        else:
            return "low"
    
    def _calculate_pest_risk(self, temp: float, humidity: float) -> str:
        """Calculate pest risk"""
        if 20 <= temp <= 30 and humidity > 70:
            return "high"
        elif 15 <= temp <= 35 and humidity > 60:
            return "moderate"
        else:
            return "low"
    
    def _calculate_disease_risk(self, humidity: float, precip: float) -> str:
        """Calculate disease risk"""
        if humidity > 80 and precip > 10:
            return "high"
        elif humidity > 70 and precip > 5:
            return "moderate"
        else:
            return "low"
    
    def _calculate_harvest_conditions(self, temp: float, humidity: float, wind: float, precip: float) -> str:
        """Calculate harvest conditions"""
        if precip > 5 or wind > 30:
            return "poor"
        elif humidity > 80 or temp > 35:
            return "fair"
        else:
            return "good"
    
    def _calculate_planting_conditions(self, temp: float, precip: float, wind: float) -> str:
        """Calculate planting conditions"""
        if precip > 20 or wind > 25:
            return "poor"
        elif 15 <= temp <= 25 and precip < 10:
            return "good"
        else:
            return "fair"
    
    def _calculate_fertilizer_timing(self, precip: float, wind: float) -> str:
        """Calculate fertilizer timing"""
        if precip > 10 or wind > 20:
            return "delay"
        elif precip < 5 and wind < 15:
            return "optimal"
        else:
            return "caution"
    
    def _calculate_uv_damage_risk(self, uv: float) -> str:
        """Calculate UV damage risk"""
        if uv > 8:
            return "high"
        elif uv > 6:
            return "moderate"
        else:
            return "low"
    
    def _get_fallback_weather(self) -> Dict[str, Any]:
        """Fallback weather data when API fails"""
        return {
            "timestamp": datetime.now().isoformat(),
            "location": {"name": "Unknown", "lat": 0, "lon": 0},
            "current": {
                "temperature": {"celsius": 25, "fahrenheit": 77},
                "humidity": 60,
                "pressure": {"mb": 1013},
                "wind": {"speed_kph": 10, "direction": "N"},
                "precipitation": {"mm": 0},
                "visibility": {"km": 10},
                "uv_index": 5,
                "condition": {"text": "Partly Cloudy", "icon": ""},
                "air_quality": {}
            },
            "agricultural_indicators": {
                "crop_stress": "moderate",
                "irrigation_need": "moderate",
                "pest_risk": "low",
                "disease_risk": "low",
                "harvest_conditions": "good",
                "planting_conditions": "good",
                "fertilizer_timing": "optimal",
                "uv_damage_risk": "moderate"
            },
            "error": "Weather data unavailable, using fallback data"
        }
    
    def _get_fallback_forecast(self) -> Dict[str, Any]:
        """Fallback forecast data when API fails"""
        return {
            "timestamp": datetime.now().isoformat(),
            "location": {"name": "Unknown", "lat": 0, "lon": 0},
            "forecast": [],
            "alerts": [],
            "error": "Forecast data unavailable, using fallback data"
        }

# Global weather service instance
weather_service = WeatherService()
