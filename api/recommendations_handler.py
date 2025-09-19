"""
Recommendations Handler - API Handler for Agricultural Recommendations
Orchestrates calls to recommendations service and processes data
"""

import logging
from typing import Dict, List, Any, Optional
from recommendations_service import recommendations_service

logger = logging.getLogger(__name__)

class RecommendationsHandler:
    """Handler for agricultural recommendations API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = recommendations_service
    
    async def get_field_recommendations(
        self, 
        field_id: str, 
        field_metrics: Dict[str, Any], 
        weather_data: Dict[str, Any],
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """
        Get comprehensive field recommendations
        
        Args:
            field_id: Unique field identifier
            field_metrics: NPK analysis and vegetation indices from field metrics API
            weather_data: Weather data from weather API
            coordinates: Field coordinates [lat, lon]
        
        Returns:
            Comprehensive recommendations for the field
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS-HANDLER] Processing recommendations for field: {field_id}")
            
            # Validate inputs
            if not field_id:
                raise ValueError("Field ID is required")
            
            if not coordinates or len(coordinates) != 2:
                raise ValueError("Valid coordinates [lat, lon] are required")
            
            # Get recommendations from service
            recommendations = await self.service.get_field_recommendations(
                field_id=field_id,
                field_metrics=field_metrics,
                weather_data=weather_data,
                coordinates=coordinates
            )
            
            self.logger.info(f"✅ [RECOMMENDATIONS-HANDLER] Successfully generated recommendations for field: {field_id}")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS-HANDLER] Error processing recommendations: {str(e)}")
            return {
                "error": "Failed to generate recommendations",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_fertilizer_recommendations(
        self, 
        field_id: str, 
        npk_data: Dict[str, Any], 
        indices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get specific fertilizer recommendations
        
        Args:
            field_id: Unique field identifier
            npk_data: NPK analysis data
            indices: Vegetation indices data
        
        Returns:
            Fertilizer-specific recommendations
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS-HANDLER] Processing fertilizer recommendations for field: {field_id}")
            
            # Create mock field metrics and weather data for fertilizer-only analysis
            field_metrics = {
                "npk": npk_data,
                "indices": indices
            }
            
            weather_data = {
                "current": {"temp_c": 25, "humidity": 50, "precip_mm": 0},
                "forecast": []
            }
            
            # Get full recommendations and extract fertilizer part
            full_recommendations = await self.service.get_field_recommendations(
                field_id=field_id,
                field_metrics=field_metrics,
                weather_data=weather_data,
                coordinates=[0, 0]  # Not needed for fertilizer-only analysis
            )
            
            fertilizer_recs = full_recommendations.get("recommendations", {}).get("fertilizer", {})
            
            self.logger.info(f"✅ [RECOMMENDATIONS-HANDLER] Successfully generated fertilizer recommendations for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_recommendations.get("timestamp"),
                "recommendations": fertilizer_recs,
                "dataSource": full_recommendations.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS-HANDLER] Error processing fertilizer recommendations: {str(e)}")
            return {
                "error": "Failed to generate fertilizer recommendations",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_irrigation_recommendations(
        self, 
        field_id: str, 
        weather_data: Dict[str, Any], 
        indices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get specific irrigation recommendations
        
        Args:
            field_id: Unique field identifier
            weather_data: Weather data
            indices: Vegetation indices data
        
        Returns:
            Irrigation-specific recommendations
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS-HANDLER] Processing irrigation recommendations for field: {field_id}")
            
            # Create mock field metrics for irrigation-only analysis
            field_metrics = {
                "npk": {"Nitrogen": "medium", "Phosphorus": "medium", "Potassium": "medium", "SOC": "medium"},
                "indices": indices
            }
            
            # Get full recommendations and extract irrigation part
            full_recommendations = await self.service.get_field_recommendations(
                field_id=field_id,
                field_metrics=field_metrics,
                weather_data=weather_data,
                coordinates=[0, 0]  # Not needed for irrigation-only analysis
            )
            
            irrigation_recs = full_recommendations.get("recommendations", {}).get("irrigation", {})
            
            self.logger.info(f"✅ [RECOMMENDATIONS-HANDLER] Successfully generated irrigation recommendations for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_recommendations.get("timestamp"),
                "recommendations": irrigation_recs,
                "dataSource": full_recommendations.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS-HANDLER] Error processing irrigation recommendations: {str(e)}")
            return {
                "error": "Failed to generate irrigation recommendations",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_crop_health_recommendations(
        self, 
        field_id: str, 
        indices: Dict[str, Any], 
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get specific crop health recommendations
        
        Args:
            field_id: Unique field identifier
            indices: Vegetation indices data
            weather_data: Weather data
        
        Returns:
            Crop health-specific recommendations
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS-HANDLER] Processing crop health recommendations for field: {field_id}")
            
            # Create mock field metrics for crop health-only analysis
            field_metrics = {
                "npk": {"Nitrogen": "medium", "Phosphorus": "medium", "Potassium": "medium", "SOC": "medium"},
                "indices": indices
            }
            
            # Get full recommendations and extract crop health part
            full_recommendations = await self.service.get_field_recommendations(
                field_id=field_id,
                field_metrics=field_metrics,
                weather_data=weather_data,
                coordinates=[0, 0]  # Not needed for crop health-only analysis
            )
            
            crop_health_recs = full_recommendations.get("recommendations", {}).get("cropHealth", {})
            
            self.logger.info(f"✅ [RECOMMENDATIONS-HANDLER] Successfully generated crop health recommendations for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_recommendations.get("timestamp"),
                "recommendations": crop_health_recs,
                "dataSource": full_recommendations.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS-HANDLER] Error processing crop health recommendations: {str(e)}")
            return {
                "error": "Failed to generate crop health recommendations",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_risk_alerts(
        self, 
        field_id: str, 
        weather_data: Dict[str, Any], 
        indices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get risk alerts for the field
        
        Args:
            field_id: Unique field identifier
            weather_data: Weather data
            indices: Vegetation indices data
        
        Returns:
            Risk alerts and warnings
        """
        try:
            self.logger.info(f"🌱 [RECOMMENDATIONS-HANDLER] Processing risk alerts for field: {field_id}")
            
            # Create mock field metrics for risk analysis
            field_metrics = {
                "npk": {"Nitrogen": "medium", "Phosphorus": "medium", "Potassium": "medium", "SOC": "medium"},
                "indices": indices
            }
            
            # Get full recommendations and extract risk alerts part
            full_recommendations = await self.service.get_field_recommendations(
                field_id=field_id,
                field_metrics=field_metrics,
                weather_data=weather_data,
                coordinates=[0, 0]  # Not needed for risk analysis
            )
            
            risk_alerts = full_recommendations.get("recommendations", {}).get("riskAlerts", {})
            
            self.logger.info(f"✅ [RECOMMENDATIONS-HANDLER] Successfully generated risk alerts for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_recommendations.get("timestamp"),
                "alerts": risk_alerts,
                "dataSource": full_recommendations.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [RECOMMENDATIONS-HANDLER] Error processing risk alerts: {str(e)}")
            return {
                "error": "Failed to generate risk alerts",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }

# Create handler instance
handler = RecommendationsHandler()
