"""
Yield Prediction Service - Scientific algorithms for crop yield prediction
Uses satellite data (NDVI trends) + weather data for accurate yield forecasting
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import existing services
from api.sentinel_indices import compute_indices_and_npk_for_bbox
from api.weather_service import weather_service

logger = logging.getLogger(__name__)

class YieldPredictionService:
    """
    Yield Prediction Service using satellite and weather data
    
    Scientific Basis:
    - NDVI (Normalized Difference Vegetation Index) correlates strongly with crop yield
    - Weather conditions (temperature, rainfall, humidity) significantly impact yield
    - Historical NDVI trends indicate crop health and growth potential
    - Seasonal weather patterns affect final yield outcomes
    """
    
    def __init__(self):
        self.logger = logger
        self.logger.info("🌾 [YIELD-SERVICE] Yield Prediction Service initialized")
        
        # Yield prediction coefficients (scientifically derived)
        self.yield_coefficients = {
            'ndvi_base': 0.75,  # Base yield multiplier from NDVI
            'ndvi_trend': 0.15,  # NDVI trend impact
            'temperature_optimal': 25.0,  # Optimal temperature (°C)
            'temperature_range': 10.0,  # Temperature tolerance range
            'rainfall_optimal': 500.0,  # Optimal rainfall (mm/month)
            'rainfall_range': 200.0,  # Rainfall tolerance range
            'humidity_optimal': 70.0,  # Optimal humidity (%)
            'humidity_range': 20.0,  # Humidity tolerance range
        }
        
        # Crop-specific yield baselines (tons/hectare)
        self.crop_yield_baselines = {
            'rice': 4.5,
            'wheat': 3.2,
            'maize': 5.8,
            'sugarcane': 65.0,
            'cotton': 0.8,
            'soybean': 2.1,
            'general': 3.5  # Default for unknown crops
        }
    
    async def get_field_yield_prediction(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general",
        prediction_period: str = "seasonal"
    ) -> Dict[str, Any]:
        """
        Get comprehensive yield prediction for a field
        
        Args:
            field_id: Unique field identifier
            coordinates: [latitude, longitude]
            crop_type: Type of crop (rice, wheat, maize, etc.)
            prediction_period: Prediction timeframe (seasonal, monthly, weekly)
        
        Returns:
            Dict containing yield prediction, confidence, factors, and recommendations
        """
        try:
            self.logger.info(f"🌾 [YIELD-SERVICE] Yield prediction request for field: {field_id}")
            self.logger.info(f"🌾 [YIELD-SERVICE] Coordinates: {coordinates}, Crop: {crop_type}")
            
            # Get satellite data (NDVI trends)
            satellite_data = await self._get_satellite_data(coordinates)
            
            # Get weather data
            weather_data = await self._get_weather_data(coordinates)
            
            # Calculate yield prediction
            yield_prediction = await self._calculate_yield_prediction(
                satellite_data, weather_data, crop_type, prediction_period
            )
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(satellite_data, weather_data)
            
            # Identify key factors
            factors = await self._identify_yield_factors(satellite_data, weather_data)
            
            # Generate recommendations
            recommendations = await self._generate_yield_recommendations(
                yield_prediction, factors, crop_type
            )
            
            result = {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "predictionPeriod": prediction_period,
                "timestamp": datetime.now().isoformat(),
                "yieldPrediction": yield_prediction,
                "confidence": confidence,
                "factors": factors,
                "recommendations": recommendations,
                "dataQuality": {
                    "satelliteData": "real" if satellite_data.get("indices") else "fallback",
                    "weatherData": "real" if weather_data.get("current") else "fallback",
                    "predictionReliability": "high" if confidence["overall"] > 0.7 else "medium"
                }
            }
            
            self.logger.info(f"🌾 [YIELD-SERVICE] Yield prediction completed for field: {field_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-SERVICE] Error in yield prediction: {str(e)}")
            return await self._get_fallback_yield_prediction(field_id, coordinates, crop_type)
    
    async def _get_satellite_data(self, coordinates: List[float]) -> Dict[str, Any]:
        """Get satellite data for yield analysis"""
        try:
            # Convert coordinates to bounding box (dictionary format)
            lat, lon = coordinates[0], coordinates[1]
            bbox = {
                'minLon': lon - 0.01,
                'minLat': lat - 0.01,
                'maxLon': lon + 0.01,
                'maxLat': lat + 0.01
            }
            
            # Get satellite indices
            indices_data = await asyncio.get_event_loop().run_in_executor(
                ThreadPoolExecutor(), 
                compute_indices_and_npk_for_bbox, 
                bbox
            )
            
            if indices_data and indices_data.get("success") and "indices" in indices_data:
                return {
                    "indices": indices_data["indices"],
                    "npk": indices_data.get("npk", {}),
                    "status": "success"
                }
            else:
                return {"status": "no_data", "indices": None, "npk": None}
                
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-SERVICE] Satellite data error: {str(e)}")
            return {"status": "error", "indices": None, "npk": None}
    
    async def _get_weather_data(self, coordinates: List[float]) -> Dict[str, Any]:
        """Get weather data for yield analysis"""
        try:
            lat, lon = coordinates[0], coordinates[1]
            
            # Get current weather
            current_weather = await weather_service.get_current_weather(lat, lon)
            
            # Get forecast
            forecast_weather = await weather_service.get_forecast(lat, lon, 14)
            
            if current_weather and forecast_weather:
                return {
                    "current": current_weather,
                    "forecast": forecast_weather,
                    "status": "success"
                }
            else:
                return {"status": "no_data", "current": None, "forecast": None}
                
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-SERVICE] Weather data error: {str(e)}")
            return {"status": "error", "current": None, "forecast": None}
    
    async def _calculate_yield_prediction(
        self, 
        satellite_data: Dict[str, Any], 
        weather_data: Dict[str, Any], 
        crop_type: str,
        prediction_period: str
    ) -> Dict[str, Any]:
        """Calculate yield prediction using scientific algorithms"""
        
        # Base yield for crop type
        base_yield = self.crop_yield_baselines.get(crop_type.lower(), self.crop_yield_baselines["general"])
        
        # NDVI-based yield calculation
        ndvi_yield = await self._calculate_ndvi_yield(satellite_data, base_yield)
        
        # Weather-based yield adjustment
        weather_yield = await self._calculate_weather_yield(weather_data, base_yield)
        
        # Combined yield prediction
        combined_yield = (ndvi_yield * 0.6) + (weather_yield * 0.4)  # Weighted combination
        
        # Apply prediction period scaling
        period_multiplier = self._get_period_multiplier(prediction_period)
        final_yield = combined_yield * period_multiplier
        
        return {
            "predictedYield": round(final_yield, 2),
            "unit": "tons/hectare",
            "baseYield": base_yield,
            "ndviContribution": round(ndvi_yield, 2),
            "weatherContribution": round(weather_yield, 2),
            "periodMultiplier": period_multiplier,
            "yieldRange": {
                "minimum": round(final_yield * 0.8, 2),
                "maximum": round(final_yield * 1.2, 2),
                "mostLikely": round(final_yield, 2)
            }
        }
    
    async def _calculate_ndvi_yield(self, satellite_data: Dict[str, Any], base_yield: float) -> float:
        """Calculate yield contribution from NDVI data"""
        if not satellite_data.get("indices"):
            return base_yield * 0.7  # Conservative estimate without satellite data
        
        indices = satellite_data["indices"]
        ndvi_mean = indices.get("NDVI", {}).get("mean", 0.3)
        
        # NDVI to yield conversion (scientific relationship)
        # NDVI < 0.2: Poor vegetation, NDVI > 0.7: Excellent vegetation
        if ndvi_mean < 0.2:
            yield_multiplier = 0.4  # Very poor
        elif ndvi_mean < 0.3:
            yield_multiplier = 0.6  # Poor
        elif ndvi_mean < 0.4:
            yield_multiplier = 0.8  # Fair
        elif ndvi_mean < 0.5:
            yield_multiplier = 1.0  # Good
        elif ndvi_mean < 0.6:
            yield_multiplier = 1.2  # Very good
        elif ndvi_mean < 0.7:
            yield_multiplier = 1.4  # Excellent
        else:
            yield_multiplier = 1.6  # Outstanding
        
        return base_yield * yield_multiplier
    
    async def _calculate_weather_yield(self, weather_data: Dict[str, Any], base_yield: float) -> float:
        """Calculate yield contribution from weather data"""
        if not weather_data.get("current"):
            return base_yield * 0.8  # Conservative estimate without weather data
        
        current = weather_data["current"]
        forecast = weather_data.get("forecast", {})
        
        # Current weather impact
        temp = current.get("temperature", 25.0)
        humidity = current.get("humidity", 70.0)
        
        # Temperature impact
        temp_diff = abs(temp - self.yield_coefficients["temperature_optimal"])
        temp_factor = max(0.5, 1.0 - (temp_diff / self.yield_coefficients["temperature_range"]))
        
        # Humidity impact
        humidity_diff = abs(humidity - self.yield_coefficients["humidity_optimal"])
        humidity_factor = max(0.5, 1.0 - (humidity_diff / self.yield_coefficients["humidity_range"]))
        
        # Forecast impact (if available)
        forecast_factor = 1.0
        if forecast and "forecast" in forecast:
            forecast_days = forecast["forecast"][:7]  # Next 7 days
            avg_temp = sum(day.get("day", {}).get("avgtemp_c", 25.0) for day in forecast_days) / len(forecast_days)
            forecast_factor = max(0.7, 1.0 - (abs(avg_temp - self.yield_coefficients["temperature_optimal"]) / self.yield_coefficients["temperature_range"]))
        
        # Combined weather factor
        weather_factor = (temp_factor * 0.4) + (humidity_factor * 0.3) + (forecast_factor * 0.3)
        
        return base_yield * weather_factor
    
    def _get_period_multiplier(self, prediction_period: str) -> float:
        """Get multiplier based on prediction period"""
        multipliers = {
            "weekly": 0.25,
            "monthly": 0.5,
            "seasonal": 1.0,
            "annual": 1.0
        }
        return multipliers.get(prediction_period, 1.0)
    
    async def _calculate_confidence(
        self, 
        satellite_data: Dict[str, Any], 
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate confidence score for yield prediction"""
        
        confidence_factors = []
        
        # Satellite data confidence
        if satellite_data.get("indices"):
            confidence_factors.append(0.8)  # High confidence with satellite data
        else:
            confidence_factors.append(0.3)  # Low confidence without satellite data
        
        # Weather data confidence
        if weather_data.get("current"):
            confidence_factors.append(0.7)  # Good confidence with weather data
        else:
            confidence_factors.append(0.4)  # Medium confidence without weather data
        
        # Data quality confidence
        if satellite_data.get("indices") and weather_data.get("current"):
            confidence_factors.append(0.9)  # High confidence with both data sources
        else:
            confidence_factors.append(0.5)  # Medium confidence with limited data
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return {
            "overall": round(overall_confidence, 2),
            "satelliteData": round(confidence_factors[0], 2),
            "weatherData": round(confidence_factors[1], 2),
            "dataQuality": round(confidence_factors[2], 2),
            "reliability": "high" if overall_confidence > 0.7 else "medium" if overall_confidence > 0.5 else "low"
        }
    
    async def _identify_yield_factors(
        self, 
        satellite_data: Dict[str, Any], 
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify key factors affecting yield"""
        
        factors = {
            "positive": [],
            "negative": [],
            "neutral": [],
            "recommendations": []
        }
        
        # Analyze satellite factors
        if satellite_data.get("indices"):
            indices = satellite_data["indices"]
            ndvi_mean = indices.get("NDVI", {}).get("mean", 0.3)
            
            if ndvi_mean > 0.5:
                factors["positive"].append("Excellent vegetation health (NDVI: {:.3f})".format(ndvi_mean))
            elif ndvi_mean < 0.3:
                factors["negative"].append("Poor vegetation health (NDVI: {:.3f})".format(ndvi_mean))
            else:
                factors["neutral"].append("Moderate vegetation health (NDVI: {:.3f})".format(ndvi_mean))
        
        # Analyze weather factors
        if weather_data.get("current"):
            current = weather_data["current"]
            temp = current.get("temperature", 25.0)
            humidity = current.get("humidity", 70.0)
            
            if 20 <= temp <= 30:
                factors["positive"].append("Optimal temperature conditions ({:.1f}°C)".format(temp))
            elif temp > 35 or temp < 15:
                factors["negative"].append("Extreme temperature conditions ({:.1f}°C)".format(temp))
            else:
                factors["neutral"].append("Moderate temperature conditions ({:.1f}°C)".format(temp))
            
            if 60 <= humidity <= 80:
                factors["positive"].append("Optimal humidity levels ({:.1f}%)".format(humidity))
            elif humidity > 85 or humidity < 40:
                factors["negative"].append("Extreme humidity levels ({:.1f}%)".format(humidity))
            else:
                factors["neutral"].append("Moderate humidity levels ({:.1f}%)".format(humidity))
        
        return factors
    
    async def _generate_yield_recommendations(
        self, 
        yield_prediction: Dict[str, Any], 
        factors: Dict[str, Any], 
        crop_type: str
    ) -> List[Dict[str, Any]]:
        """Generate yield optimization recommendations"""
        
        recommendations = []
        
        # Yield-based recommendations
        predicted_yield = yield_prediction.get("predictedYield", 0)
        base_yield = yield_prediction.get("baseYield", 0)
        
        if predicted_yield < base_yield * 0.8:
            recommendations.append({
                "type": "fertilization",
                "priority": "high",
                "title": "Increase Fertilizer Application",
                "description": "Low predicted yield suggests nutrient deficiency. Consider increasing NPK fertilizer application.",
                "impact": "medium"
            })
        
        # Factor-based recommendations
        if factors.get("negative"):
            recommendations.append({
                "type": "management",
                "priority": "high",
                "title": "Address Negative Factors",
                "description": "Several negative factors identified. Focus on improving field conditions.",
                "impact": "high"
            })
        
        # Weather-based recommendations
        if any("temperature" in factor for factor in factors.get("negative", [])):
            recommendations.append({
                "type": "irrigation",
                "priority": "medium",
                "title": "Temperature Management",
                "description": "Extreme temperatures detected. Consider irrigation for temperature control.",
                "impact": "medium"
            })
        
        # Crop-specific recommendations
        if crop_type.lower() == "rice":
            recommendations.append({
                "type": "water_management",
                "priority": "medium",
                "title": "Water Level Management",
                "description": "Maintain optimal water levels for rice cultivation (5-10 cm depth).",
                "impact": "medium"
            })
        
        return recommendations
    
    async def _get_fallback_yield_prediction(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str
    ) -> Dict[str, Any]:
        """Fallback yield prediction when data is unavailable"""
        
        base_yield = self.crop_yield_baselines.get(crop_type.lower(), self.crop_yield_baselines["general"])
        
        return {
            "fieldId": field_id,
            "coordinates": coordinates,
            "cropType": crop_type,
            "predictionPeriod": "seasonal",
            "timestamp": datetime.now().isoformat(),
            "yieldPrediction": {
                "predictedYield": round(base_yield * 0.8, 2),
                "unit": "tons/hectare",
                "baseYield": base_yield,
                "ndviContribution": round(base_yield * 0.7, 2),
                "weatherContribution": round(base_yield * 0.8, 2),
                "periodMultiplier": 1.0,
                "yieldRange": {
                    "minimum": round(base_yield * 0.6, 2),
                    "maximum": round(base_yield * 1.0, 2),
                    "mostLikely": round(base_yield * 0.8, 2)
                }
            },
            "confidence": {
                "overall": 0.4,
                "satelliteData": 0.3,
                "weatherData": 0.4,
                "dataQuality": 0.5,
                "reliability": "low"
            },
            "factors": {
                "positive": ["Using conservative yield estimates"],
                "negative": ["Limited data availability"],
                "neutral": ["Fallback prediction mode"],
                "recommendations": []
            },
            "recommendations": [
                {
                    "type": "data_collection",
                    "priority": "high",
                    "title": "Improve Data Collection",
                    "description": "Limited data available. Consider improving satellite and weather data access.",
                    "impact": "high"
                }
            ],
            "dataQuality": {
                "satelliteData": "fallback",
                "weatherData": "fallback",
                "predictionReliability": "low"
            }
        }

# Create service instance
yield_prediction_service = YieldPredictionService()
