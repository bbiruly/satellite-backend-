#!/usr/bin/env python3
"""
Optimized Terrain Handler - B2B Ready
Fast HTTP request processing with performance monitoring
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import time

from optimized_terrain_service import optimized_terrain_service
from performance_optimizer import performance_optimizer

logger = logging.getLogger("optimized_terrain_handler")
logger.setLevel(logging.INFO)

class OptimizedTerrainHandler:
    """Optimized handler for terrain API requests"""
    
    def __init__(self):
        self.logger = logger
        self.service = optimized_terrain_service
        self.performance_optimizer = performance_optimizer
    
    async def get_elevation_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """Get optimized elevation analysis with performance monitoring"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🏔️ [OPTIMIZED-TERRAIN] Processing elevation analysis")
            self.logger.info(f"🏔️ [OPTIMIZED-TERRAIN] Coordinates: {coordinates}")
            
            # Validate coordinates
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            # Get elevation from optimized service
            elevation_data = await self.service.get_elevation_analysis(coordinates)
            
            # Add performance metadata
            processing_time = time.time() - start_time
            elevation_data['performance'] = {
                'processingTime': round(processing_time, 2),
                'targetTime': 3.0,
                'status': 'optimized' if processing_time <= 3.0 else 'fallback',
                'cacheHit': 'cached' in elevation_data.get('dataSource', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ [OPTIMIZED-TERRAIN] Successfully processed elevation analysis")
            self.logger.info(f"📊 [OPTIMIZED-TERRAIN] Processing time: {processing_time:.2f}s")
            
            return elevation_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ [OPTIMIZED-TERRAIN] Error processing elevation: {str(e)}")
            
            # Return fallback response for B2B smoothness
            return self._create_error_response(coordinates, 'elevation', str(e), processing_time)
    
    async def get_land_cover_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """Get optimized land cover analysis with performance monitoring"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🌍 [OPTIMIZED-TERRAIN] Processing land cover analysis")
            self.logger.info(f"🌍 [OPTIMIZED-TERRAIN] Coordinates: {coordinates}")
            
            # Validate coordinates
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            # Get land cover from optimized service
            land_cover_data = await self.service.get_land_cover_analysis(coordinates)
            
            # Add performance metadata
            processing_time = time.time() - start_time
            land_cover_data['performance'] = {
                'processingTime': round(processing_time, 2),
                'targetTime': 3.0,
                'status': 'optimized' if processing_time <= 3.0 else 'fallback',
                'cacheHit': 'cached' in land_cover_data.get('dataSource', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ [OPTIMIZED-TERRAIN] Successfully processed land cover analysis")
            self.logger.info(f"📊 [OPTIMIZED-TERRAIN] Processing time: {processing_time:.2f}s")
            
            return land_cover_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ [OPTIMIZED-TERRAIN] Error processing land cover: {str(e)}")
            
            # Return fallback response for B2B smoothness
            return self._create_error_response(coordinates, 'land_cover', str(e), processing_time)
    
    async def get_comprehensive_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """Get optimized comprehensive terrain analysis with performance monitoring"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🏔️🌍 [OPTIMIZED-TERRAIN] Processing comprehensive analysis")
            self.logger.info(f"🏔️🌍 [OPTIMIZED-TERRAIN] Coordinates: {coordinates}")
            
            # Validate coordinates
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            # Get comprehensive analysis from optimized service
            comprehensive_data = await self.service.get_comprehensive_analysis(coordinates)
            
            # Add performance metadata
            processing_time = time.time() - start_time
            comprehensive_data['performance'] = {
                'processingTime': round(processing_time, 2),
                'targetTime': 3.0,
                'status': 'optimized' if processing_time <= 3.0 else 'fallback',
                'cacheHit': 'cached' in comprehensive_data.get('dataSource', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ [OPTIMIZED-TERRAIN] Successfully processed comprehensive analysis")
            self.logger.info(f"📊 [OPTIMIZED-TERRAIN] Processing time: {processing_time:.2f}s")
            
            return comprehensive_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ [OPTIMIZED-TERRAIN] Error processing comprehensive analysis: {str(e)}")
            
            # Return fallback response for B2B smoothness
            return self._create_error_response(coordinates, 'comprehensive', str(e), processing_time)
    
    def _create_error_response(
        self, 
        coordinates: List[float], 
        analysis_type: str,
        error_message: str, 
        processing_time: float
    ) -> Dict[str, Any]:
        """Create error response with fallback data for B2B smoothness"""
        fallback_data = {
            'elevation': {
                'elevation': 850.0,
                'unit': 'meters',
                'slope': 2.5,
                'aspect': 'south',
                'drainage': 'good',
                'source': 'Fallback (Error recovery)'
            },
            'landCover': {
                'primary': 'agricultural',
                'percentage': 85.0,
                'suitability': 'high',
                'source': 'Fallback (Error recovery)'
            }
        }
        
        return {
            'coordinates': coordinates,
            'timestamp': datetime.now().isoformat(),
            **fallback_data,
            'dataSource': 'Fallback (Error recovery)',
            'warning': f'Using fallback data due to error: {error_message}',
            'performance': {
                'processingTime': round(processing_time, 2),
                'targetTime': 3.0,
                'status': 'fallback',
                'cacheHit': False,
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            },
            'analysisType': f'Fallback {analysis_type.title()} Analysis',
            'performance': 'Optimized with error recovery'
        }

# Global handler instance
handler = OptimizedTerrainHandler()
