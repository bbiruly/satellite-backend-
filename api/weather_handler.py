"""
Weather API Handler for ZumAgro
Handles weather data requests and responses
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from weather_service import weather_service

logger = logging.getLogger(__name__)

class WeatherHandler:
    """Handler for weather API requests"""
    
    def __init__(self):
        self.service = weather_service
    
    async def get_field_weather(self, field_id: str, coordinates: List[float], days: int = 7) -> Dict[str, Any]:
        """Get comprehensive weather data for a field"""
        try:
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather request for field: {field_id}")
            
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            lat, lon = coordinates[0], coordinates[1]
            
            # Get current weather and forecast concurrently
            current_task = self.service.get_current_weather(lat, lon)
            forecast_task = self.service.get_forecast(lat, lon, days)
            
            current_weather, forecast = await asyncio.gather(current_task, forecast_task)
            
            # Combine data
            weather_data = {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "coordinates": {"lat": lat, "lon": lon},
                "current": current_weather.get("current", {}),
                "forecast": forecast.get("forecast", []),
                "alerts": forecast.get("alerts", []),
                "location": current_weather.get("location", {}),
                "agricultural_summary": self._generate_agricultural_summary(current_weather, forecast),
                "recommendations": self._generate_weather_recommendations(current_weather, forecast)
            }
            
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather data generated for field: {field_id}")
            return weather_data
            
        except Exception as e:
            logger.error(f"🌤️ [WEATHER-HANDLER] Error processing weather request: {str(e)}")
            return self._get_error_response(field_id, str(e))
    
    async def get_weather_alerts(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """Get weather alerts for a field"""
        try:
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather alerts request for field: {field_id}")
            
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            lat, lon = coordinates[0], coordinates[1]
            forecast = await self.service.get_forecast(lat, lon, 7)
            alerts = forecast.get("alerts", [])
            
            alert_data = {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "coordinates": {"lat": lat, "lon": lon},
                "alerts": alerts,
                "alert_count": len(alerts),
                "severity_levels": self._categorize_alerts(alerts)
            }
            
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather alerts processed for field: {field_id}")
            return alert_data
            
        except Exception as e:
            logger.error(f"🌤️ [WEATHER-HANDLER] Error processing alerts request: {str(e)}")
            return self._get_error_response(field_id, str(e))
    
    async def get_historical_weather(self, field_id: str, coordinates: List[float], date: str) -> Dict[str, Any]:
        """Get historical weather data for a field"""
        try:
            logger.info(f"🌤️ [WEATHER-HANDLER] Historical weather request for field: {field_id}, date: {date}")
            
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            lat, lon = coordinates[0], coordinates[1]
            historical = await self.service.get_historical_weather(lat, lon, date)
            
            historical_data = {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "coordinates": {"lat": lat, "lon": lon},
                "date": date,
                "historical": historical.get("current", {}),
                "location": historical.get("location", {}),
                "agricultural_analysis": self._analyze_historical_weather(historical)
            }
            
            logger.info(f"🌤️ [WEATHER-HANDLER] Historical weather processed for field: {field_id}")
            return historical_data
            
        except Exception as e:
            logger.error(f"🌤️ [WEATHER-HANDLER] Error processing historical request: {str(e)}")
            return self._get_error_response(field_id, str(e))
    
    async def get_forecast(self, field_id: str, coordinates: List[float], days: int = 14) -> Dict[str, Any]:
        """Get weather forecast for a field"""
        try:
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather forecast request for field: {field_id}, days: {days}")
            
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            lat, lon = coordinates[0], coordinates[1]
            forecast = await self.service.get_forecast(lat, lon, days)
            
            forecast_data = {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "coordinates": {"lat": lat, "lon": lon},
                "forecast_days": days,
                "forecast": forecast.get("forecast", []),
                "alerts": forecast.get("alerts", []),
                "location": forecast.get("location", {}),
                "agricultural_forecast": self._analyze_forecast_weather(forecast)
            }
            
            logger.info(f"🌤️ [WEATHER-HANDLER] Weather forecast processed for field: {field_id}")
            return forecast_data
            
        except Exception as e:
            logger.error(f"🌤️ [WEATHER-HANDLER] Error processing forecast request: {str(e)}")
            return self._get_error_response(field_id, str(e))
    
    def _generate_agricultural_summary(self, current: Dict[str, Any], forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agricultural summary from weather data"""
        current_indicators = current.get("agricultural_indicators", {})
        forecast_days = forecast.get("forecast", [])
        
        # Analyze forecast trends
        temp_trend = self._analyze_temperature_trend(forecast_days)
        precip_trend = self._analyze_precipitation_trend(forecast_days)
        humidity_trend = self._analyze_humidity_trend(forecast_days)
        
        return {
            "current_conditions": {
                "crop_stress": current_indicators.get("crop_stress", "unknown"),
                "irrigation_need": current_indicators.get("irrigation_need", "unknown"),
                "pest_risk": current_indicators.get("pest_risk", "unknown"),
                "disease_risk": current_indicators.get("disease_risk", "unknown")
            },
            "forecast_trends": {
                "temperature": temp_trend,
                "precipitation": precip_trend,
                "humidity": humidity_trend
            },
            "overall_assessment": self._assess_overall_conditions(current_indicators, forecast_days)
        }
    
    def _generate_weather_recommendations(self, current: Dict[str, Any], forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate weather-based recommendations"""
        recommendations = []
        current_indicators = current.get("agricultural_indicators", {})
        forecast_days = forecast.get("forecast", [])
        
        # Irrigation recommendations
        irrigation_need = current_indicators.get("irrigation_need", "unknown")
        if irrigation_need == "high":
            recommendations.append({
                "type": "irrigation",
                "priority": "high",
                "message": "High irrigation need detected. Consider watering crops.",
                "action": "Schedule irrigation within 24 hours"
            })
        
        # Pest and disease recommendations
        pest_risk = current_indicators.get("pest_risk", "unknown")
        if pest_risk == "high":
            recommendations.append({
                "type": "pest_control",
                "priority": "high",
                "message": "High pest risk conditions. Monitor crops closely.",
                "action": "Consider preventive pest control measures"
            })
        
        disease_risk = current_indicators.get("disease_risk", "unknown")
        if disease_risk == "high":
            recommendations.append({
                "type": "disease_prevention",
                "priority": "high",
                "message": "High disease risk conditions detected.",
                "action": "Apply fungicide if conditions persist"
            })
        
        # Fertilizer timing recommendations
        fertilizer_timing = current_indicators.get("fertilizer_timing", "unknown")
        if fertilizer_timing == "delay":
            recommendations.append({
                "type": "fertilizer",
                "priority": "medium",
                "message": "Weather conditions not optimal for fertilizer application.",
                "action": "Delay fertilizer application until conditions improve"
            })
        
        # Harvest recommendations
        harvest_conditions = current_indicators.get("harvest_conditions", "unknown")
        if harvest_conditions == "poor":
            recommendations.append({
                "type": "harvest",
                "priority": "medium",
                "message": "Poor harvest conditions. Consider delaying harvest.",
                "action": "Wait for better weather conditions"
            })
        
        return recommendations
    
    def _analyze_temperature_trend(self, forecast_days: List[Dict[str, Any]]) -> str:
        """Analyze temperature trend over forecast period"""
        if len(forecast_days) < 3:
            return "insufficient_data"
        
        temps = [day.get("day", {}).get("avg_temp_c", 0) for day in forecast_days[:3]]
        if temps[2] > temps[0] + 2:
            return "increasing"
        elif temps[2] < temps[0] - 2:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_precipitation_trend(self, forecast_days: List[Dict[str, Any]]) -> str:
        """Analyze precipitation trend over forecast period"""
        if len(forecast_days) < 3:
            return "insufficient_data"
        
        precip = [day.get("day", {}).get("total_precip_mm", 0) for day in forecast_days[:3]]
        total_precip = sum(precip)
        
        if total_precip > 20:
            return "heavy_rain_expected"
        elif total_precip > 10:
            return "moderate_rain_expected"
        elif total_precip > 0:
            return "light_rain_expected"
        else:
            return "no_rain_expected"
    
    def _analyze_humidity_trend(self, forecast_days: List[Dict[str, Any]]) -> str:
        """Analyze humidity trend over forecast period"""
        if len(forecast_days) < 3:
            return "insufficient_data"
        
        humidities = [day.get("day", {}).get("avg_humidity", 0) for day in forecast_days[:3]]
        avg_humidity = sum(humidities) / len(humidities)
        
        if avg_humidity > 80:
            return "high_humidity"
        elif avg_humidity > 60:
            return "moderate_humidity"
        else:
            return "low_humidity"
    
    def _assess_overall_conditions(self, current_indicators: Dict[str, Any], forecast_days: List[Dict[str, Any]]) -> str:
        """Assess overall agricultural conditions"""
        high_risk_factors = 0
        
        if current_indicators.get("crop_stress") == "high":
            high_risk_factors += 1
        if current_indicators.get("pest_risk") == "high":
            high_risk_factors += 1
        if current_indicators.get("disease_risk") == "high":
            high_risk_factors += 1
        
        # Check forecast for adverse conditions
        for day in forecast_days[:3]:
            day_data = day.get("day", {})
            if day_data.get("total_precip_mm", 0) > 15:
                high_risk_factors += 1
            if day_data.get("max_temp_c", 0) > 35:
                high_risk_factors += 1
        
        if high_risk_factors >= 3:
            return "challenging"
        elif high_risk_factors >= 1:
            return "moderate"
        else:
            return "favorable"
    
    def _categorize_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize alerts by severity"""
        severity_counts = {"minor": 0, "moderate": 0, "severe": 0, "extreme": 0}
        
        for alert in alerts:
            severity = alert.get("severity", "minor").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _analyze_historical_weather(self, historical: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical weather data"""
        current = historical.get("current", {})
        indicators = current.get("agricultural_indicators", {})
        
        return {
            "conditions": {
                "temperature": current.get("temperature", {}).get("celsius", 0),
                "humidity": current.get("humidity", 0),
                "precipitation": current.get("precipitation", {}).get("mm", 0),
                "wind_speed": current.get("wind", {}).get("speed_kph", 0)
            },
            "agricultural_impact": {
                "crop_stress": indicators.get("crop_stress", "unknown"),
                "irrigation_need": indicators.get("irrigation_need", "unknown"),
                "pest_risk": indicators.get("pest_risk", "unknown"),
                "disease_risk": indicators.get("disease_risk", "unknown")
            },
            "summary": "Historical weather analysis completed"
        }
    
    def _analyze_forecast_weather(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze forecast weather data"""
        forecast_days = forecast.get("forecast", [])
        
        if not forecast_days:
            return {"message": "No forecast data available"}
        
        # Analyze first 7 days
        week_forecast = forecast_days[:7]
        
        # Calculate averages
        avg_temp = sum(day.get("day", {}).get("avgtemp_c", 0) for day in week_forecast) / len(week_forecast)
        total_precip = sum(day.get("day", {}).get("totalprecip_mm", 0) for day in week_forecast)
        avg_humidity = sum(day.get("day", {}).get("avghumidity", 0) for day in week_forecast) / len(week_forecast)
        
        return {
            "week_summary": {
                "average_temperature": round(avg_temp, 1),
                "total_precipitation": round(total_precip, 1),
                "average_humidity": round(avg_humidity, 1)
            },
            "agricultural_outlook": {
                "irrigation_need": "high" if total_precip < 10 else "low",
                "crop_stress": "high" if avg_temp > 35 else "medium" if avg_temp > 25 else "low",
                "disease_risk": "high" if avg_humidity > 80 else "medium" if avg_humidity > 60 else "low"
            },
            "summary": "Weather forecast analysis completed"
        }
    
    def _get_error_response(self, field_id: str, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "fieldId": field_id,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "status": "error",
            "message": "Weather data unavailable"
        }

# Global weather handler instance
handler = WeatherHandler()
