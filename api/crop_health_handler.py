"""
Crop Health Handler
Handles HTTP requests for crop health monitoring API
"""

import logging
from typing import Dict, List, Any, Optional
from crop_health_service import CropHealthService

logger = logging.getLogger(__name__)

class CropHealthHandler:
    """Handler for crop health monitoring API requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = CropHealthService()

    async def get_crop_health(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get comprehensive crop health analysis
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            crop_type: Type of crop (wheat, rice, corn, etc.)
            
        Returns:
            Dict containing crop health analysis
        """
        try:
            self.logger.info(f"🌱 [CROP-HEALTH-HANDLER] Processing health analysis for field: {field_id}")
            
            # Get health analysis from service
            health_metrics = await self.service.get_crop_health_analysis(
                field_id, coordinates, crop_type
            )
            
            # Format response
            response = {
                "fieldId": field_id,
                "timestamp": health_metrics.indices.get('timestamp', ''),
                "cropHealth": {
                    "overallHealthScore": health_metrics.overall_health_score,
                    "stressLevel": health_metrics.stress_level,
                    "growthStage": health_metrics.growth_stage,
                    "qualityScore": health_metrics.quality_score,
                    "diseaseRisk": health_metrics.disease_risk,
                    "pestRisk": health_metrics.pest_risk,
                    "waterStress": health_metrics.water_stress,
                    "nutrientStress": health_metrics.nutrient_stress,
                    "temperatureStress": health_metrics.temperature_stress
                },
                "vegetationIndices": health_metrics.indices,
                "recommendations": health_metrics.recommendations,
                "confidence": health_metrics.confidence,
                "dataSource": "Microsoft Planetary Computer (pystac_client)",
                "analysisType": "Real-time Crop Health Monitoring"
            }
            
            self.logger.info(f"✅ [CROP-HEALTH-HANDLER] Successfully generated health analysis for field: {field_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH-HANDLER] Error in health analysis: {str(e)}")
            raise

    async def get_crop_stress(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """
        Get detailed stress analysis for the field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dict containing stress analysis
        """
        try:
            self.logger.info(f"🌱 [CROP-HEALTH-HANDLER] Processing stress analysis for field: {field_id}")
            
            # Get stress analysis from service
            stress_data = await self.service.get_crop_stress_analysis(field_id, coordinates)
            
            self.logger.info(f"✅ [CROP-HEALTH-HANDLER] Successfully generated stress analysis for field: {field_id}")
            return stress_data
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH-HANDLER] Error in stress analysis: {str(e)}")
            raise

    async def get_growth_stage(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """
        Get growth stage analysis for the field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dict containing growth stage analysis
        """
        try:
            self.logger.info(f"🌱 [CROP-HEALTH-HANDLER] Processing growth stage analysis for field: {field_id}")
            
            # Get growth stage analysis from service
            growth_data = await self.service.get_growth_stage_analysis(field_id, coordinates)
            
            self.logger.info(f"✅ [CROP-HEALTH-HANDLER] Successfully generated growth stage analysis for field: {field_id}")
            return growth_data
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH-HANDLER] Error in growth stage analysis: {str(e)}")
            raise

    async def get_crop_quality(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """
        Get crop quality analysis for the field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dict containing quality analysis
        """
        try:
            self.logger.info(f"🌱 [CROP-HEALTH-HANDLER] Processing quality analysis for field: {field_id}")
            
            # Get quality analysis from service
            quality_data = await self.service.get_crop_quality_analysis(field_id, coordinates)
            
            self.logger.info(f"✅ [CROP-HEALTH-HANDLER] Successfully generated quality analysis for field: {field_id}")
            return quality_data
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH-HANDLER] Error in quality analysis: {str(e)}")
            raise

# Create handler instance
handler = CropHealthHandler()
