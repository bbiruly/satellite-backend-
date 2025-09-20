#!/usr/bin/env python3
"""
Optimized Trends Handler - B2B Ready
Fast HTTP request processing with performance monitoring
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import time

from optimized_trends_service import optimized_trends_service
from performance_optimizer import performance_optimizer

logger = logging.getLogger("optimized_trends_handler")
logger.setLevel(logging.INFO)

class OptimizedTrendsHandler:
    """Optimized handler for trends API requests"""
    
    def __init__(self):
        self.logger = logger
        self.service = optimized_trends_service
        self.performance_optimizer = performance_optimizer
    
    async def get_field_trends(
        self, 
        field_id: str, 
        coordinates: List[float],
        time_period: str = "30d",
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Get optimized field trends with performance monitoring"""
        start_time = time.time()
        
        try:
            self.logger.info(f"📈 [OPTIMIZED-TRENDS] Processing request for field: {field_id}")
            self.logger.info(f"📈 [OPTIMIZED-TRENDS] Coordinates: {coordinates}")
            self.logger.info(f"📈 [OPTIMIZED-TRENDS] Time period: {time_period}")
            
            # Validate coordinates
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            # Get trends from optimized service
            trends_data = await self.service.get_field_trends(
                field_id, coordinates, time_period, analysis_type
            )
            
            # Add performance metadata
            processing_time = time.time() - start_time
            trends_data['performance'] = {
                'processingTime': round(processing_time, 2),
                'targetTime': 8.0,
                'status': 'optimized' if processing_time <= 8.0 else 'fallback',
                'cacheHit': 'cached' in trends_data.get('dataSource', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ [OPTIMIZED-TRENDS] Successfully processed field: {field_id}")
            self.logger.info(f"📊 [OPTIMIZED-TRENDS] Processing time: {processing_time:.2f}s")
            
            return trends_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ [OPTIMIZED-TRENDS] Error processing field {field_id}: {str(e)}")
            
            # Return fallback response for B2B smoothness
            return self._create_error_response(field_id, coordinates, time_period, str(e), processing_time)
    
    def _create_error_response(
        self, 
        field_id: str, 
        coordinates: List[float], 
        time_period: str,
        error_message: str, 
        processing_time: float
    ) -> Dict[str, Any]:
        """Create error response with fallback data for B2B smoothness"""
        return {
            'fieldId': field_id,
            'timestamp': datetime.now().isoformat(),
            'coordinates': coordinates,
            'timePeriod': time_period,
            'vegetation_trend': 'stable',
            'weather_trend': 'normal',
            'performance_trend': 'good',
            'seasonal_analysis': 'on_track',
            'anomalies': [],
            'historical_summary': {
                'avg_ndvi': 0.65,
                'avg_health': 75.0,
                'trend_direction': 'stable',
                'confidence': 0.6,
                'data_points': 0,
                'last_updated': datetime.now().isoformat()
            },
            'dataSource': 'Fallback (Error recovery)',
            'warning': f'Using fallback data due to error: {error_message}',
            'performance': {
                'processingTime': round(processing_time, 2),
                'targetTime': 8.0,
                'status': 'fallback',
                'cacheHit': False,
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            },
            'analysisType': 'Fallback Trends Analysis',
            'performance': 'Optimized with error recovery'
        }

# Global handler instance
handler = OptimizedTrendsHandler()
