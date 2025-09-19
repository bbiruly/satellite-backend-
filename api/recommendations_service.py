"""
Recommendations Service - Actionable Agricultural Intelligence
Provides specific, actionable recommendations based on field data
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class RecommendationsService:
    """Service for generating actionable agricultural recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_field_recommendations(
        self, 
        field_id: str, 
        field_metrics: Dict[str, Any], 
        weather_data: Dict[str, Any],
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive field recommendations based on all available data
        
        Args:
            field_id: Unique field identifier
            field_metrics: NPK analysis and vegetation indices
            weather_data: Current and forecast weather data
            coordinates: Field coordinates [lat, lon]
        
        Returns:
            Comprehensive recommendations for the field
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS] Generating recommendations for field: {field_id}")
            
            # Extract data from inputs
            npk_data = field_metrics.get('npk', {})
            indices = field_metrics.get('indices', {})
            current_weather = weather_data.get('current', {})
            forecast = weather_data.get('forecast', [])
            
            # Generate different types of recommendations
            fertilizer_recs = self._generate_fertilizer_recommendations(npk_data, indices)
            irrigation_recs = self._generate_irrigation_recommendations(weather_data, indices)
            crop_health_recs = self._generate_crop_health_recommendations(indices, current_weather)
            timing_recs = self._generate_timing_recommendations(weather_data, coordinates)
            risk_alerts = self._generate_risk_alerts(weather_data, indices)
            
            # Calculate overall field health score
            health_score = self._calculate_field_health_score(indices, npk_data, current_weather)
            
            # Generate priority actions
            priority_actions = self._generate_priority_actions(
                fertilizer_recs, irrigation_recs, crop_health_recs, risk_alerts
            )
            
            recommendations = {
                "fieldId": field_id,
                "timestamp": datetime.utcnow().isoformat(),
                "coordinates": coordinates,
                "fieldHealth": {
                    "overallScore": health_score,
                    "status": self._get_health_status(health_score),
                    "trend": "stable"  # Could be enhanced with historical data
                },
                "recommendations": {
                    "fertilizer": fertilizer_recs,
                    "irrigation": irrigation_recs,
                    "cropHealth": crop_health_recs,
                    "timing": timing_recs,
                    "riskAlerts": risk_alerts
                },
                "priorityActions": priority_actions,
                "nextReviewDate": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "dataSource": {
                    "satelliteData": "Microsoft Planetary Computer",
                    "weatherData": "WeatherAPI.com",
                    "analysisEngine": "ZumAgro AI"
                }
            }
            
            self.logger.info(f"✅ [RECOMMENDATIONS] Generated {len(priority_actions)} priority actions for field: {field_id}")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS] Error generating recommendations: {str(e)}")
            return self._get_fallback_recommendations(field_id, coordinates)
    
    def _generate_fertilizer_recommendations(self, npk_data: Dict, indices: Dict) -> Dict[str, Any]:
        """Generate fertilizer recommendations based on NPK analysis"""
        try:
            recommendations = []
            priority = "medium"
            
            # Analyze NPK levels
            nitrogen = npk_data.get('Nitrogen', 'medium')
            phosphorus = npk_data.get('Phosphorus', 'medium')
            potassium = npk_data.get('Potassium', 'medium')
            soc = npk_data.get('SOC', 'medium')
            
            # Get vegetation health from NDVI
            ndvi_mean = indices.get('NDVI', {}).get('mean', 0.3)
            
            # Nitrogen recommendations
            if nitrogen == 'low':
                recommendations.append({
                    "type": "fertilizer",
                    "nutrient": "Nitrogen",
                    "action": "Apply nitrogen fertilizer",
                    "amount": "40-60 kg/ha",
                    "timing": "Within 7 days",
                    "priority": "high",
                    "reason": "Low nitrogen levels detected - critical for plant growth"
                })
                priority = "high"
            elif nitrogen == 'high':
                recommendations.append({
                    "type": "fertilizer",
                    "nutrient": "Nitrogen",
                    "action": "Reduce nitrogen application",
                    "amount": "0 kg/ha",
                    "timing": "Next application cycle",
                    "priority": "medium",
                    "reason": "High nitrogen levels - risk of over-fertilization"
                })
            
            # Phosphorus recommendations
            if phosphorus == 'low':
                recommendations.append({
                    "type": "fertilizer",
                    "nutrient": "Phosphorus",
                    "action": "Apply phosphorus fertilizer",
                    "amount": "20-30 kg/ha",
                    "timing": "Within 10 days",
                    "priority": "high",
                    "reason": "Low phosphorus levels - essential for root development"
                })
                priority = "high"
            
            # Potassium recommendations
            if potassium == 'low':
                recommendations.append({
                    "type": "fertilizer",
                    "nutrient": "Potassium",
                    "action": "Apply potassium fertilizer",
                    "amount": "30-40 kg/ha",
                    "timing": "Within 14 days",
                    "priority": "medium",
                    "reason": "Low potassium levels - important for disease resistance"
                })
            
            # Soil Organic Carbon recommendations
            if soc == 'low':
                recommendations.append({
                    "type": "soil_improvement",
                    "nutrient": "Organic Matter",
                    "action": "Add organic compost or manure",
                    "amount": "5-10 tons/ha",
                    "timing": "Next planting season",
                    "priority": "medium",
                    "reason": "Low soil organic carbon - improve soil structure and fertility"
                })
            
            # NDVI-based recommendations
            if ndvi_mean < 0.2:
                recommendations.append({
                    "type": "general",
                    "action": "Check for pest or disease issues",
                    "timing": "Immediately",
                    "priority": "high",
                    "reason": "Very low vegetation index - possible crop stress"
                })
                priority = "high"
            elif ndvi_mean > 0.7:
                recommendations.append({
                    "type": "general",
                    "action": "Monitor for overgrowth",
                    "timing": "Ongoing",
                    "priority": "low",
                    "reason": "Very high vegetation index - monitor for lodging risk"
                })
            
            return {
                "recommendations": recommendations,
                "priority": priority,
                "summary": f"Generated {len(recommendations)} fertilizer recommendations"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating fertilizer recommendations: {str(e)}")
            return {"recommendations": [], "priority": "medium", "summary": "Unable to generate recommendations"}
    
    def _generate_irrigation_recommendations(self, weather_data: Dict, indices: Dict) -> Dict[str, Any]:
        """Generate irrigation recommendations based on weather and soil moisture"""
        try:
            recommendations = []
            priority = "medium"
            
            current = weather_data.get('current', {})
            forecast = weather_data.get('forecast', [])
            
            # Current conditions
            temp = current.get('temp_c', 25)
            humidity = current.get('humidity', 50)
            precip_mm = current.get('precip_mm', 0)
            
            # Get moisture index from NDWI
            ndwi_mean = indices.get('NDWI', {}).get('mean', 0)
            
            # Temperature-based recommendations
            if temp > 35:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Increase irrigation frequency",
                    "amount": "Additional 20-30% water",
                    "timing": "Daily",
                    "priority": "high",
                    "reason": "High temperature stress - plants need more water"
                })
                priority = "high"
            elif temp < 10:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Reduce irrigation",
                    "amount": "Reduce by 30-40%",
                    "timing": "Every 2-3 days",
                    "priority": "medium",
                    "reason": "Low temperature - reduced water needs"
                })
            
            # Humidity-based recommendations
            if humidity < 30:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Increase irrigation",
                    "amount": "Additional 15-20% water",
                    "timing": "Daily",
                    "priority": "medium",
                    "reason": "Low humidity - increased evaporation"
                })
            elif humidity > 80:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Reduce irrigation",
                    "amount": "Reduce by 20-30%",
                    "timing": "Every 2-3 days",
                    "priority": "low",
                    "reason": "High humidity - reduced evaporation"
                })
            
            # Precipitation-based recommendations
            if precip_mm > 20:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Skip irrigation",
                    "amount": "0 mm",
                    "timing": "Next 2-3 days",
                    "priority": "low",
                    "reason": "Recent heavy rainfall - soil is saturated"
                })
            elif precip_mm < 1 and len(forecast) > 0:
                # Check if rain is forecast
                next_rain = any(day.get('day', {}).get('totalprecip_mm', 0) > 5 for day in forecast[:3])
                if not next_rain:
                    recommendations.append({
                        "type": "irrigation",
                        "action": "Plan irrigation",
                        "amount": "Normal irrigation",
                        "timing": "Within 2 days",
                        "priority": "medium",
                        "reason": "No recent rain and none forecast - irrigation needed"
                    })
            
            # NDWI-based recommendations
            if ndwi_mean < -0.3:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Urgent irrigation needed",
                    "amount": "Heavy irrigation",
                    "timing": "Immediately",
                    "priority": "high",
                    "reason": "Very low water content detected in vegetation"
                })
                priority = "high"
            elif ndwi_mean > 0.2:
                recommendations.append({
                    "type": "irrigation",
                    "action": "Reduce irrigation",
                    "amount": "Reduce by 25%",
                    "timing": "Next irrigation cycle",
                    "priority": "low",
                    "reason": "High water content - risk of overwatering"
                })
            
            return {
                "recommendations": recommendations,
                "priority": priority,
                "summary": f"Generated {len(recommendations)} irrigation recommendations"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating irrigation recommendations: {str(e)}")
            return {"recommendations": [], "priority": "medium", "summary": "Unable to generate recommendations"}
    
    def _generate_crop_health_recommendations(self, indices: Dict, current_weather: Dict) -> Dict[str, Any]:
        """Generate crop health recommendations based on vegetation indices"""
        try:
            recommendations = []
            priority = "medium"
            
            ndvi = indices.get('NDVI', {}).get('mean', 0.3)
            ndmi = indices.get('NDMI', {}).get('mean', 0.2)
            savi = indices.get('SAVI', {}).get('mean', 0.3)
            
            temp = current_weather.get('temp_c', 25)
            humidity = current_weather.get('humidity', 50)
            
            # NDVI-based health assessment
            if ndvi < 0.2:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Immediate field inspection needed",
                    "timing": "Today",
                    "priority": "high",
                    "reason": "Very low vegetation index - possible crop failure or pest damage"
                })
                priority = "high"
            elif ndvi < 0.4:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Check for nutrient deficiency or disease",
                    "timing": "Within 3 days",
                    "priority": "medium",
                    "reason": "Low vegetation index - crop stress detected"
                })
            elif ndvi > 0.7:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Monitor for lodging or overgrowth",
                    "timing": "Ongoing",
                    "priority": "low",
                    "reason": "Very high vegetation index - monitor plant height"
                })
            
            # NDMI-based moisture stress
            if ndmi < 0.1:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Check for drought stress",
                    "timing": "Within 2 days",
                    "priority": "high",
                    "reason": "Very low moisture index - severe drought stress"
                })
                priority = "high"
            elif ndmi < 0.2:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Monitor soil moisture",
                    "timing": "Daily",
                    "priority": "medium",
                    "reason": "Low moisture index - possible water stress"
                })
            
            # SAVI-based soil adjustment
            if savi < 0.2:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Check soil conditions and root health",
                    "timing": "Within 5 days",
                    "priority": "medium",
                    "reason": "Low soil-adjusted vegetation index - possible soil issues"
                })
            
            # Weather-based health recommendations
            if temp > 35 and humidity > 70:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Monitor for fungal diseases",
                    "timing": "Daily",
                    "priority": "medium",
                    "reason": "Hot and humid conditions favor fungal growth"
                })
            elif temp < 5:
                recommendations.append({
                    "type": "crop_health",
                    "action": "Protect from frost damage",
                    "timing": "Immediately",
                    "priority": "high",
                    "reason": "Low temperature - risk of frost damage"
                })
                priority = "high"
            
            return {
                "recommendations": recommendations,
                "priority": priority,
                "summary": f"Generated {len(recommendations)} crop health recommendations"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating crop health recommendations: {str(e)}")
            return {"recommendations": [], "priority": "medium", "summary": "Unable to generate recommendations"}
    
    def _generate_timing_recommendations(self, weather_data: Dict, coordinates: List[float]) -> Dict[str, Any]:
        """Generate timing recommendations for farming activities"""
        try:
            recommendations = []
            priority = "medium"
            
            current = weather_data.get('current', {})
            forecast = weather_data.get('forecast', [])
            
            # Get next 7 days forecast
            next_week = forecast[:7] if len(forecast) >= 7 else forecast
            
            # Find best days for field work
            good_weather_days = []
            for i, day in enumerate(next_week):
                day_data = day.get('day', {})
                max_temp = day_data.get('maxtemp_c', 25)
                min_temp = day_data.get('mintemp_c', 15)
                precip = day_data.get('totalprecip_mm', 0)
                wind_speed = day_data.get('maxwind_kph', 10)
                
                # Good conditions: moderate temp, no rain, low wind
                if (15 <= min_temp <= 30 and 20 <= max_temp <= 35 and 
                    precip < 5 and wind_speed < 25):
                    good_weather_days.append({
                        "day": i + 1,
                        "date": (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "conditions": f"Temp: {min_temp}-{max_temp}°C, Rain: {precip}mm, Wind: {wind_speed}km/h"
                    })
            
            if good_weather_days:
                recommendations.append({
                    "type": "timing",
                    "action": "Plan field work activities",
                    "timing": f"Next {len(good_weather_days)} days",
                    "priority": "medium",
                    "reason": f"Good weather conditions available for {len(good_weather_days)} days",
                    "details": good_weather_days[:3]  # Show next 3 good days
                })
            
            # Planting window recommendation (simplified)
            if coordinates[0] > 20:  # Northern hemisphere
                current_month = datetime.utcnow().month
                if 3 <= current_month <= 5:
                    recommendations.append({
                        "type": "timing",
                        "action": "Optimal planting window",
                        "timing": "Spring season",
                        "priority": "high",
                        "reason": "Current season is ideal for planting most crops"
                    })
                    priority = "high"
                elif 9 <= current_month <= 11:
                    recommendations.append({
                        "type": "timing",
                        "action": "Harvest preparation",
                        "timing": "Fall season",
                        "priority": "medium",
                        "reason": "Harvest season - prepare for crop collection"
                    })
            
            return {
                "recommendations": recommendations,
                "priority": priority,
                "summary": f"Generated {len(recommendations)} timing recommendations"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating timing recommendations: {str(e)}")
            return {"recommendations": [], "priority": "medium", "summary": "Unable to generate recommendations"}
    
    def _generate_risk_alerts(self, weather_data: Dict, indices: Dict) -> Dict[str, Any]:
        """Generate risk alerts for weather and crop conditions"""
        try:
            alerts = []
            priority = "low"
            
            current = weather_data.get('current', {})
            forecast = weather_data.get('forecast', [])
            
            # Current weather alerts
            temp = current.get('temp_c', 25)
            wind_speed = current.get('wind_kph', 10)
            precip = current.get('precip_mm', 0)
            humidity = current.get('humidity', 50)
            
            # Temperature alerts
            if temp > 40:
                alerts.append({
                    "type": "weather",
                    "severity": "high",
                    "alert": "Extreme heat warning",
                    "action": "Provide shade and increase irrigation",
                    "timing": "Immediately",
                    "reason": f"Temperature {temp}°C is dangerous for crops"
                })
                priority = "high"
            elif temp < 0:
                alerts.append({
                    "type": "weather",
                    "severity": "high",
                    "alert": "Frost warning",
                    "action": "Cover crops or use frost protection",
                    "timing": "Immediately",
                    "reason": f"Temperature {temp}°C can damage crops"
                })
                priority = "high"
            
            # Wind alerts
            if wind_speed > 50:
                alerts.append({
                    "type": "weather",
                    "severity": "high",
                    "alert": "High wind warning",
                    "action": "Secure equipment and check for lodging",
                    "timing": "Immediately",
                    "reason": f"Wind speed {wind_speed} km/h can cause damage"
                })
                priority = "high"
            
            # Precipitation alerts
            if precip > 50:
                alerts.append({
                    "type": "weather",
                    "severity": "medium",
                    "alert": "Heavy rainfall warning",
                    "action": "Check drainage and prevent waterlogging",
                    "timing": "Within 2 hours",
                    "reason": f"Heavy rain {precip}mm can cause flooding"
                })
                priority = "medium"
            
            # Forecast alerts
            for i, day in enumerate(forecast[:3]):  # Next 3 days
                day_data = day.get('day', {})
                max_temp = day_data.get('maxtemp_c', 25)
                min_temp = day_data.get('mintemp_c', 15)
                day_precip = day_data.get('totalprecip_mm', 0)
                day_wind = day_data.get('maxwind_kph', 10)
                
                if max_temp > 35:
                    alerts.append({
                        "type": "forecast",
                        "severity": "medium",
                        "alert": f"Hot day forecast - Day {i+1}",
                        "action": "Prepare for heat stress management",
                        "timing": f"Day {i+1}",
                        "reason": f"Temperature will reach {max_temp}°C"
                    })
                    priority = "medium"
                
                if day_precip > 30:
                    alerts.append({
                        "type": "forecast",
                        "severity": "medium",
                        "alert": f"Heavy rain forecast - Day {i+1}",
                        "action": "Prepare drainage and delay field work",
                        "timing": f"Day {i+1}",
                        "reason": f"Expected {day_precip}mm of rain"
                    })
                    priority = "medium"
            
            # Crop health alerts based on indices
            ndvi = indices.get('NDVI', {}).get('mean', 0.3)
            if ndvi < 0.15:
                alerts.append({
                    "type": "crop_health",
                    "severity": "high",
                    "alert": "Severe crop stress detected",
                    "action": "Immediate field inspection required",
                    "timing": "Today",
                    "reason": "Very low vegetation index indicates serious problems"
                })
                priority = "high"
            
            return {
                "alerts": alerts,
                "priority": priority,
                "summary": f"Generated {len(alerts)} risk alerts"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating risk alerts: {str(e)}")
            return {"alerts": [], "priority": "low", "summary": "Unable to generate alerts"}
    
    def _calculate_field_health_score(self, indices: Dict, npk_data: Dict, current_weather: Dict) -> float:
        """Calculate overall field health score (0-100)"""
        try:
            score = 50.0  # Base score
            
            # NDVI contribution (40% weight)
            ndvi = indices.get('NDVI', {}).get('mean', 0.3)
            if ndvi > 0.7:
                score += 20
            elif ndvi > 0.5:
                score += 15
            elif ndvi > 0.3:
                score += 10
            elif ndvi > 0.2:
                score += 5
            else:
                score -= 10
            
            # NPK contribution (30% weight)
            npk_score = 0
            for nutrient in ['Nitrogen', 'Phosphorus', 'Potassium']:
                level = npk_data.get(nutrient, 'medium')
                if level == 'high':
                    npk_score += 8
                elif level == 'medium':
                    npk_score += 6
                elif level == 'low':
                    npk_score += 3
            score += npk_score
            
            # Weather contribution (20% weight)
            temp = current_weather.get('temp_c', 25)
            if 15 <= temp <= 30:
                score += 10
            elif 10 <= temp <= 35:
                score += 5
            else:
                score -= 5
            
            # Moisture contribution (10% weight)
            ndwi = indices.get('NDWI', {}).get('mean', 0)
            if ndwi > 0.1:
                score += 5
            elif ndwi > -0.1:
                score += 3
            else:
                score -= 5
            
            # Ensure score is between 0 and 100
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating health score: {str(e)}")
            return 50.0
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        elif score >= 20:
            return "poor"
        else:
            return "critical"
    
    def _generate_priority_actions(self, fertilizer_recs: Dict, irrigation_recs: Dict, 
                                 crop_health_recs: Dict, risk_alerts: Dict) -> List[Dict[str, Any]]:
        """Generate prioritized action list"""
        try:
            all_actions = []
            
            # Collect all recommendations
            all_actions.extend(fertilizer_recs.get('recommendations', []))
            all_actions.extend(irrigation_recs.get('recommendations', []))
            all_actions.extend(crop_health_recs.get('recommendations', []))
            all_actions.extend(risk_alerts.get('alerts', []))
            
            # Sort by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            all_actions.sort(key=lambda x: priority_order.get(x.get('priority', 'medium'), 2), reverse=True)
            
            # Return top 5 actions
            return all_actions[:5]
            
        except Exception as e:
            self.logger.error(f"Error generating priority actions: {str(e)}")
            return []
    
    def _get_fallback_recommendations(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """Fallback recommendations when data is unavailable"""
        return {
            "fieldId": field_id,
            "timestamp": datetime.utcnow().isoformat(),
            "coordinates": coordinates,
            "fieldHealth": {
                "overallScore": 50.0,
                "status": "unknown",
                "trend": "stable"
            },
            "recommendations": {
                "fertilizer": {"recommendations": [], "priority": "medium", "summary": "Data unavailable"},
                "irrigation": {"recommendations": [], "priority": "medium", "summary": "Data unavailable"},
                "cropHealth": {"recommendations": [], "priority": "medium", "summary": "Data unavailable"},
                "timing": {"recommendations": [], "priority": "medium", "summary": "Data unavailable"},
                "riskAlerts": {"alerts": [], "priority": "low", "summary": "Data unavailable"}
            },
            "priorityActions": [],
            "nextReviewDate": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "dataSource": {
                "satelliteData": "Unavailable",
                "weatherData": "Unavailable",
                "analysisEngine": "ZumAgro AI"
            },
            "warning": "Limited data available - recommendations may not be accurate"
        }

# Create service instance
recommendations_service = RecommendationsService()
