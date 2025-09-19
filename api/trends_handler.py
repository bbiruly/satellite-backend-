"""
Trends Handler - API Handler for Field Trends and Historical Analysis
Orchestrates calls to trends service and processes historical data
"""

import logging
from typing import Dict, List, Any, Optional
from trends_service import trends_service

logger = logging.getLogger(__name__)

class TrendsHandler:
    """Handler for field trends and historical analysis API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service = trends_service
    
    async def get_field_trends(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d",
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Get comprehensive field trends analysis
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period ("7d", "30d", "90d", "1y")
            analysis_type: Type of analysis ("comprehensive", "vegetation", "weather", "yield")
        
        Returns:
            Comprehensive trends analysis for the field
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing trends analysis for field: {field_id}")
            self.logger.info(f"📈 [TRENDS-HANDLER] Period: {time_period}, Type: {analysis_type}")
            
            # Validate inputs
            if not field_id:
                raise ValueError("Field ID is required")
            
            if not coordinates or len(coordinates) != 2:
                raise ValueError("Valid coordinates [lat, lon] are required")
            
            # Get trends analysis from service
            trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type=analysis_type
            )
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated trends analysis for field: {field_id}")
            return trends
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing trends analysis: {str(e)}")
            return {
                "error": "Failed to generate trends analysis",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_vegetation_trends(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get vegetation-specific trends analysis
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period
        
        Returns:
            Vegetation trends analysis
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing vegetation trends for field: {field_id}")
            
            # Get full trends analysis and extract vegetation part
            full_trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type="vegetation"
            )
            
            vegetation_trends = full_trends.get("trends", {}).get("vegetation", {})
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated vegetation trends for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_trends.get("timestamp"),
                "analysisPeriod": full_trends.get("analysisPeriod", {}),
                "trends": vegetation_trends,
                "dataSource": full_trends.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing vegetation trends: {str(e)}")
            return {
                "error": "Failed to generate vegetation trends",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_weather_trends(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get weather-specific trends analysis
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period
        
        Returns:
            Weather trends analysis
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing weather trends for field: {field_id}")
            
            # Get full trends analysis and extract weather part
            full_trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type="weather"
            )
            
            weather_trends = full_trends.get("trends", {}).get("weather", {})
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated weather trends for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_trends.get("timestamp"),
                "analysisPeriod": full_trends.get("analysisPeriod", {}),
                "trends": weather_trends,
                "dataSource": full_trends.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing weather trends: {str(e)}")
            return {
                "error": "Failed to generate weather trends",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_performance_trends(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get performance-specific trends analysis
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period
        
        Returns:
            Performance trends analysis
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing performance trends for field: {field_id}")
            
            # Get full trends analysis and extract performance part
            full_trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type="yield"
            )
            
            performance_trends = full_trends.get("trends", {}).get("performance", {})
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated performance trends for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_trends.get("timestamp"),
                "analysisPeriod": full_trends.get("analysisPeriod", {}),
                "trends": performance_trends,
                "dataSource": full_trends.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing performance trends: {str(e)}")
            return {
                "error": "Failed to generate performance trends",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_seasonal_analysis(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "1y"
    ) -> Dict[str, Any]:
        """
        Get seasonal analysis and patterns
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period (should be at least 1y for seasonal analysis)
        
        Returns:
            Seasonal analysis
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing seasonal analysis for field: {field_id}")
            
            # Get full trends analysis and extract seasonal part
            full_trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type="comprehensive"
            )
            
            seasonal_analysis = full_trends.get("trends", {}).get("seasonal", {})
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated seasonal analysis for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_trends.get("timestamp"),
                "analysisPeriod": full_trends.get("analysisPeriod", {}),
                "analysis": seasonal_analysis,
                "dataSource": full_trends.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing seasonal analysis: {str(e)}")
            return {
                "error": "Failed to generate seasonal analysis",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }
    
    async def get_anomaly_detection(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get anomaly detection results
        
        Args:
            field_id: Unique field identifier
            coordinates: Field coordinates [lat, lon]
            time_period: Analysis period
        
        Returns:
            Anomaly detection results
        """
        try:
            self.logger.info(f"📈 [TRENDS-HANDLER] Processing anomaly detection for field: {field_id}")
            
            # Get full trends analysis and extract anomalies part
            full_trends = await self.service.get_field_trends(
                field_id=field_id,
                coordinates=coordinates,
                time_period=time_period,
                analysis_type="comprehensive"
            )
            
            anomaly_detection = full_trends.get("trends", {}).get("anomalies", {})
            
            self.logger.info(f"✅ [TRENDS-HANDLER] Successfully generated anomaly detection for field: {field_id}")
            return {
                "fieldId": field_id,
                "timestamp": full_trends.get("timestamp"),
                "analysisPeriod": full_trends.get("analysisPeriod", {}),
                "anomalies": anomaly_detection,
                "dataSource": full_trends.get("dataSource", {})
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TRENDS-HANDLER] Error processing anomaly detection: {str(e)}")
            return {
                "error": "Failed to generate anomaly detection",
                "message": str(e),
                "fieldId": field_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }

# Create handler instance
handler = TrendsHandler()
