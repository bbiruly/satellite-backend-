#!/usr/bin/env python3
"""
Optimized Field Metrics Handler - B2B Ready
Fast, reliable HTTP request processing with performance monitoring
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import time

from optimized_field_metrics import optimized_field_metrics_service
from performance_optimizer import performance_optimizer

logger = logging.getLogger("optimized_field_metrics_handler")
logger.setLevel(logging.INFO)

class OptimizedFieldMetricsHandler:
    """Optimized handler for field metrics API requests"""
    
    def __init__(self):
        self.logger = logger
        self.service = optimized_field_metrics_service
        self.performance_optimizer = performance_optimizer
    
    async def get_field_metrics(self, field_id: str, coordinates: List[float]) -> Dict[str, Any]:
        """Get optimized field metrics with performance monitoring"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🌾 [OPTIMIZED-FIELD-METRICS] Processing request for field: {field_id}")
            self.logger.info(f"🌾 [OPTIMIZED-FIELD-METRICS] Coordinates: {coordinates}")
            
            # Validate coordinates
            if not coordinates or len(coordinates) < 2:
                raise ValueError("Invalid coordinates provided")
            
            # Get field metrics from optimized service
            metrics_data = await self.service.get_field_metrics(field_id, coordinates)
            
            # Add performance metadata
            processing_time = time.time() - start_time
            metrics_data['performance'] = {
                'processingTime': round(processing_time, 2),
                'targetTime': 5.0,
                'status': 'optimized' if processing_time <= 5.0 else 'slow',
                'cacheHit': 'cached' in metrics_data.get('dataSource', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ [OPTIMIZED-FIELD-METRICS] Successfully processed field: {field_id}")
            self.logger.info(f"📊 [OPTIMIZED-FIELD-METRICS] Processing time: {processing_time:.2f}s")
            
            return metrics_data
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ [OPTIMIZED-FIELD-METRICS] Error processing field {field_id}: {str(e)}")
            
            # Re-raise error - customers pay for real data only
            raise Exception(f"Field metrics processing failed: {str(e)}")
    

# Global handler instance
handler = OptimizedFieldMetricsHandler()
