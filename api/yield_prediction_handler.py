"""
Yield Prediction Handler - HTTP request processing for yield prediction endpoints
"""

import logging
from typing import Dict, Any, List
from api.yield_prediction_service import yield_prediction_service

logger = logging.getLogger(__name__)

class YieldPredictionHandler:
    """
    Handler for yield prediction API endpoints
    """
    
    def __init__(self):
        self.logger = logger
        self.logger.info("🌾 [YIELD-HANDLER] Yield Prediction Handler initialized")
    
    async def get_yield_prediction(
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
            Dict containing complete yield prediction analysis
        """
        try:
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield prediction request for field: {field_id}")
            self.logger.info(f"🌾 [YIELD-HANDLER] Coordinates: {coordinates}, Crop: {crop_type}, Period: {prediction_period}")
            
            result = await yield_prediction_service.get_field_yield_prediction(
                field_id, coordinates, crop_type, prediction_period
            )
            
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield prediction completed for field: {field_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-HANDLER] Error in yield prediction: {str(e)}")
            return {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "predictionPeriod": prediction_period,
                "error": str(e),
                "status": "error"
            }
    
    async def get_yield_confidence(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get yield prediction confidence score
        
        Args:
            field_id: Unique field identifier
            coordinates: [latitude, longitude]
            crop_type: Type of crop
        
        Returns:
            Dict containing confidence analysis
        """
        try:
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield confidence request for field: {field_id}")
            
            # Get full prediction to extract confidence
            full_prediction = await yield_prediction_service.get_field_yield_prediction(
                field_id, coordinates, crop_type, "seasonal"
            )
            
            confidence_data = {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "timestamp": full_prediction.get("timestamp"),
                "confidence": full_prediction.get("confidence", {}),
                "dataQuality": full_prediction.get("dataQuality", {}),
                "recommendations": [
                    {
                        "type": "confidence_improvement",
                        "priority": "medium",
                        "title": "Improve Prediction Confidence",
                        "description": "Consider collecting more satellite and weather data for better predictions.",
                        "impact": "medium"
                    }
                ]
            }
            
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield confidence completed for field: {field_id}")
            return confidence_data
            
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-HANDLER] Error in yield confidence: {str(e)}")
            return {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "error": str(e),
                "status": "error"
            }
    
    async def get_yield_factors(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get key factors affecting yield
        
        Args:
            field_id: Unique field identifier
            coordinates: [latitude, longitude]
            crop_type: Type of crop
        
        Returns:
            Dict containing yield factors analysis
        """
        try:
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield factors request for field: {field_id}")
            
            # Get full prediction to extract factors
            full_prediction = await yield_prediction_service.get_field_yield_prediction(
                field_id, coordinates, crop_type, "seasonal"
            )
            
            factors_data = {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "timestamp": full_prediction.get("timestamp"),
                "factors": full_prediction.get("factors", {}),
                "yieldPrediction": full_prediction.get("yieldPrediction", {}),
                "dataQuality": full_prediction.get("dataQuality", {}),
                "analysis": {
                    "totalFactors": len(full_prediction.get("factors", {}).get("positive", [])) + 
                                  len(full_prediction.get("factors", {}).get("negative", [])) + 
                                  len(full_prediction.get("factors", {}).get("neutral", [])),
                    "positiveCount": len(full_prediction.get("factors", {}).get("positive", [])),
                    "negativeCount": len(full_prediction.get("factors", {}).get("negative", [])),
                    "neutralCount": len(full_prediction.get("factors", {}).get("neutral", []))
                }
            }
            
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield factors completed for field: {field_id}")
            return factors_data
            
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-HANDLER] Error in yield factors: {str(e)}")
            return {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "error": str(e),
                "status": "error"
            }
    
    async def get_yield_recommendations(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get yield optimization recommendations
        
        Args:
            field_id: Unique field identifier
            coordinates: [latitude, longitude]
            crop_type: Type of crop
        
        Returns:
            Dict containing yield optimization recommendations
        """
        try:
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield recommendations request for field: {field_id}")
            
            # Get full prediction to extract recommendations
            full_prediction = await yield_prediction_service.get_field_yield_prediction(
                field_id, coordinates, crop_type, "seasonal"
            )
            
            recommendations_data = {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "timestamp": full_prediction.get("timestamp"),
                "recommendations": full_prediction.get("recommendations", []),
                "yieldPrediction": full_prediction.get("yieldPrediction", {}),
                "factors": full_prediction.get("factors", {}),
                "dataQuality": full_prediction.get("dataQuality", {}),
                "summary": {
                    "totalRecommendations": len(full_prediction.get("recommendations", [])),
                    "highPriority": len([r for r in full_prediction.get("recommendations", []) if r.get("priority") == "high"]),
                    "mediumPriority": len([r for r in full_prediction.get("recommendations", []) if r.get("priority") == "medium"]),
                    "lowPriority": len([r for r in full_prediction.get("recommendations", []) if r.get("priority") == "low"])
                }
            }
            
            self.logger.info(f"🌾 [YIELD-HANDLER] Yield recommendations completed for field: {field_id}")
            return recommendations_data
            
        except Exception as e:
            self.logger.error(f"🌾 [YIELD-HANDLER] Error in yield recommendations: {str(e)}")
            return {
                "fieldId": field_id,
                "coordinates": coordinates,
                "cropType": crop_type,
                "error": str(e),
                "status": "error"
            }

# Create handler instance
yield_prediction_handler = YieldPredictionHandler()

# Export handler for main.py
handler = yield_prediction_handler
