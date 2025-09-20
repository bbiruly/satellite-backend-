#!/usr/bin/env python3
"""
Terrain Handler - HTTP request processing for terrain analysis
"""
import logging
from typing import Dict, Any, List
from terrain_service import terrain_service

logger = logging.getLogger("terrain_handler")
logger.setLevel(logging.INFO)

class TerrainHandler:
    """Handler for terrain analysis requests"""
    
    def __init__(self):
        self.logger = logger
        self.terrain_service = terrain_service
    
    async def get_elevation_analysis(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get elevation analysis for a field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with elevation analysis response
        """
        try:
            self.logger.info(f"🏔️ [TERRAIN-HANDLER] Processing elevation analysis for field: {field_id}")
            
            # Get elevation analysis
            elevation_data = await self.terrain_service.get_elevation_analysis(coordinates)
            
            # Format response
            response = {
                "success": True,
                "fieldId": field_id,
                "coordinates": coordinates,
                "elevationAnalysis": elevation_data,
                "metadata": {
                    "analysisType": "Elevation Analysis",
                    "dataSource": "Microsoft Planetary Computer (Copernicus DEM)",
                    "confidence": 1.0 if elevation_data.get("success", False) else 0.0,
                    "timestamp": elevation_data.get("metadata", {}).get("analysisDate", "")
                }
            }
            
            self.logger.info(f"✅ [TERRAIN-HANDLER] Successfully generated elevation analysis for field: {field_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN-HANDLER] Error in elevation analysis: {str(e)}")
            return {
                "success": False,
                "fieldId": field_id,
                "coordinates": coordinates,
                "error": str(e),
                "elevationAnalysis": None
            }
    
    async def get_land_cover_analysis(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get land cover analysis for a field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with land cover analysis response
        """
        try:
            self.logger.info(f"🌍 [TERRAIN-HANDLER] Processing land cover analysis for field: {field_id}")
            
            # Get land cover analysis
            land_cover_data = await self.terrain_service.get_land_cover_analysis(coordinates)
            
            # Format response
            response = {
                "success": True,
                "fieldId": field_id,
                "coordinates": coordinates,
                "landCoverAnalysis": land_cover_data,
                "metadata": {
                    "analysisType": "Land Cover Analysis",
                    "dataSource": "Microsoft Planetary Computer (ESA WorldCover / Esri Land Cover)",
                    "confidence": 1.0 if land_cover_data.get("success", False) else 0.0,
                    "timestamp": land_cover_data.get("metadata", {}).get("analysisDate", "")
                }
            }
            
            self.logger.info(f"✅ [TERRAIN-HANDLER] Successfully generated land cover analysis for field: {field_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN-HANDLER] Error in land cover analysis: {str(e)}")
            return {
                "success": False,
                "fieldId": field_id,
                "coordinates": coordinates,
                "error": str(e),
                "landCoverAnalysis": None
            }
    
    async def get_comprehensive_terrain_analysis(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get comprehensive terrain analysis for a field
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with comprehensive terrain analysis response
        """
        try:
            self.logger.info(f"🏔️🌍 [TERRAIN-HANDLER] Processing comprehensive terrain analysis for field: {field_id}")
            
            # Get comprehensive terrain analysis
            terrain_data = await self.terrain_service.get_comprehensive_terrain_analysis(coordinates)
            
            # Format response
            response = {
                "success": True,
                "fieldId": field_id,
                "coordinates": coordinates,
                "terrainAnalysis": terrain_data,
                "metadata": {
                    "analysisType": "Comprehensive Terrain Analysis",
                    "dataSource": "Microsoft Planetary Computer (Copernicus DEM + ESA WorldCover)",
                    "confidence": 1.0 if terrain_data.get("success", False) else 0.0,
                    "timestamp": terrain_data.get("metadata", {}).get("analysisDate", "")
                }
            }
            
            self.logger.info(f"✅ [TERRAIN-HANDLER] Successfully generated comprehensive terrain analysis for field: {field_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN-HANDLER] Error in comprehensive terrain analysis: {str(e)}")
            return {
                "success": False,
                "fieldId": field_id,
                "coordinates": coordinates,
                "error": str(e),
                "terrainAnalysis": None
            }

# Create handler instance
handler = TerrainHandler()
