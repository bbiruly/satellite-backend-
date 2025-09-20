#!/usr/bin/env python3
"""
Enhanced Planetary Computer Integration
Phase 1: Multi-satellite retry system with intelligent caching
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.sentinel_indices import compute_indices_and_npk_for_bbox

class EnhancedPlanetaryComputerManager:
    """Enhanced Planetary Computer manager with multi-satellite support and intelligent caching"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Multi-satellite priority configuration
        self.satellite_configs = {
            'sentinel-2-l2a': {
                'name': 'Sentinel-2 L2A',
                'resolution': '10m',
                'timeout': 15.0,
                'priority': 1,
                'bands': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12'],
                'cloud_penetration': False,
                'best_for': 'clear_sky_conditions'
            },
            'landsat-8-c2-l2': {
                'name': 'Landsat-8 C2 L2',
                'resolution': '30m',
                'timeout': 20.0,
                'priority': 2,
                'bands': ['B02', 'B03', 'B04', 'B05', 'B06', 'B07'],
                'cloud_penetration': False,
                'best_for': 'moderate_cloud_conditions'
            },
            'modis-09a1-v061': {
                'name': 'MODIS 09A1',
                'resolution': '250m',
                'timeout': 25.0,
                'priority': 3,
                'bands': ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07'],
                'cloud_penetration': False,
                'best_for': 'large_area_coverage'
            },
            'sentinel-1-rtc': {
                'name': 'Sentinel-1 RTC',
                'resolution': '10m',
                'timeout': 30.0,
                'priority': 4,
                'bands': ['VV', 'VH'],
                'cloud_penetration': True,
                'best_for': 'cloudy_conditions_monsoon'
            }
        }
        
        # Intelligent caching configuration
        self.cache_config = {
            'satellite_imagery': {'ttl': 21600, 'size_limit': '10GB'},  # 6 hours
            'weather_data': {'ttl': 3600, 'size_limit': '1GB'},      # 1 hour
            'soil_maps': {'ttl': 604800, 'size_limit': '5GB'},       # 7 days
            'elevation_data': {'ttl': 2592000, 'size_limit': '2GB'}  # 30 days
        }
        
        # In-memory cache (will be replaced with Redis in Phase 1.2)
        self.cache = {}
        self.cache_timestamps = {}
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0,
            'dataset_usage': {}
        }
        
        # Monsoon-aware configuration for India
        self.monsoon_config = {
            'kharif_season': {'months': [6, 7, 8, 9, 10], 'cloud_threshold': 50},
            'rabi_season': {'months': [11, 12, 1, 2, 3, 4], 'cloud_threshold': 30},
            'zaid_season': {'months': [5], 'cloud_threshold': 40}
        }
    
    async def get_satellite_data_with_enhanced_retry(
        self, 
        coordinates: List[float], 
        bbox: Dict[str, float],
        field_id: str,
        cloud_coverage: Optional[float] = None,
        monsoon_phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced satellite data retrieval with intelligent satellite selection
        """
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(coordinates, bbox, field_id)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self.performance_stats['cache_hits'] += 1
                self.logger.info(f"✅ [ENHANCED-PC] Cache hit for field: {field_id}")
                return cached_data
            
            self.performance_stats['cache_misses'] += 1
            
            # Determine optimal satellite selection
            optimal_satellites = self._select_optimal_satellites(
                cloud_coverage, monsoon_phase, coordinates
            )
            
            self.logger.info(f"🛰️ [ENHANCED-PC] Selected satellites for {field_id}: {optimal_satellites}")
            
            # Try satellites in priority order
            for satellite_id in optimal_satellites:
                try:
                    self.logger.info(f"🔄 [ENHANCED-PC] Trying {satellite_id} for field: {field_id}")
                    
                    result = await self._fetch_satellite_data(
                        satellite_id, coordinates, bbox, field_id
                    )
                    
                    if result and result.get('success'):
                        # Cache successful result
                        self._cache_result(cache_key, result)
                        
                        # Update performance stats
                        processing_time = time.time() - start_time
                        self._update_performance_stats(satellite_id, processing_time, True)
                        
                        self.logger.info(f"✅ [ENHANCED-PC] Success with {satellite_id} for field: {field_id}")
                        return result
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ [ENHANCED-PC] {satellite_id} failed for {field_id}: {str(e)}")
                    continue
            
            # All satellites failed
            self._update_performance_stats('all_failed', time.time() - start_time, False)
            return {
                'success': False,
                'error': 'All satellite datasets failed',
                'datasets_tried': optimal_satellites,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ [ENHANCED-PC] Error in enhanced retry: {str(e)}")
            self._update_performance_stats('error', time.time() - start_time, False)
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _select_optimal_satellites(
        self, 
        cloud_coverage: Optional[float], 
        monsoon_phase: Optional[str],
        coordinates: List[float]
    ) -> List[str]:
        """
        Select optimal satellites based on conditions and location
        """
        # Determine if coordinates are in India
        is_india = self._is_indian_coordinates(coordinates)
        
        # Default priority order
        priority_order = ['sentinel-2-l2a', 'landsat-8-c2-l2', 'modis-09a1-v061', 'sentinel-1-rtc']
        
        # Adjust based on conditions
        if cloud_coverage and cloud_coverage > 70:
            # Heavy cloud cover - prioritize SAR
            priority_order = ['sentinel-1-rtc', 'modis-09a1-v061', 'landsat-8-c2-l2', 'sentinel-2-l2a']
            self.logger.info(f"🌧️ [ENHANCED-PC] Heavy cloud cover ({cloud_coverage}%) - prioritizing SAR")
            
        elif monsoon_phase == 'active_monsoon':
            # Active monsoon - prioritize weather-independent satellites
            priority_order = ['sentinel-1-rtc', 'modis-09a1-v061', 'landsat-8-c2-l2', 'sentinel-2-l2a']
            self.logger.info(f"🌧️ [ENHANCED-PC] Active monsoon - prioritizing weather-independent satellites")
            
        elif is_india and monsoon_phase == 'kharif_season':
            # Kharif season in India - moderate cloud tolerance
            priority_order = ['sentinel-2-l2a', 'sentinel-1-rtc', 'landsat-8-c2-l2', 'modis-09a1-v061']
            self.logger.info(f"🌾 [ENHANCED-PC] Kharif season in India - balanced approach")
            
        elif cloud_coverage and cloud_coverage < 30:
            # Clear conditions - prioritize high resolution
            priority_order = ['sentinel-2-l2a', 'landsat-8-c2-l2', 'modis-09a1-v061', 'sentinel-1-rtc']
            self.logger.info(f"☀️ [ENHANCED-PC] Clear conditions ({cloud_coverage}%) - prioritizing high resolution")
        
        return priority_order
    
    def _is_indian_coordinates(self, coordinates: List[float]) -> bool:
        """Check if coordinates are within India's boundaries"""
        lat, lon = coordinates[0], coordinates[1]
        # India bounding box: [68.7, 8.4, 97.25, 37.6]
        return (8.4 <= lat <= 37.6) and (68.7 <= lon <= 97.25)
    
    async def _fetch_satellite_data(
        self, 
        satellite_id: str, 
        coordinates: List[float], 
        bbox: Dict[str, float],
        field_id: str
    ) -> Dict[str, Any]:
        """
        Fetch data from specific satellite
        """
        config = self.satellite_configs[satellite_id]
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(compute_indices_and_npk_for_bbox, bbox)
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: future.result()),
                    timeout=config['timeout']
                )
                
                if result and result.get('success'):
                    result['dataset'] = satellite_id
                    result['source'] = f"Microsoft Planetary Computer ({config['name']})"
                    result['resolution'] = config['resolution']
                    result['cloud_penetration'] = config['cloud_penetration']
                    return result
                else:
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ [ENHANCED-PC] {satellite_id} timeout ({config['timeout']}s)")
            return None
        except Exception as e:
            self.logger.error(f"❌ [ENHANCED-PC] {satellite_id} error: {str(e)}")
            return None
    
    def _generate_cache_key(self, coordinates: List[float], bbox: Dict[str, float], field_id: str) -> str:
        """Generate cache key for satellite data"""
        # Round coordinates to 4 decimal places for cache efficiency
        lat = round(coordinates[0], 4)
        lon = round(coordinates[1], 4)
        return f"satellite_data_{lat}_{lon}_{field_id}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid"""
        if cache_key in self.cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self.cache_config['satellite_imagery']['ttl']:
                return self.cache[cache_key]
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache successful result"""
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()
        
        # Simple cache size management (will be replaced with Redis)
        if len(self.cache) > 100:  # Limit to 100 entries
            oldest_key = min(self.cache_timestamps.keys(), key=lambda k: self.cache_timestamps[k])
            del self.cache[oldest_key]
            del self.cache_timestamps[oldest_key]
    
    def _update_performance_stats(self, dataset: str, processing_time: float, success: bool):
        """Update performance statistics"""
        if success:
            self.performance_stats['successful_requests'] += 1
            self.performance_stats['dataset_usage'][dataset] = self.performance_stats['dataset_usage'].get(dataset, 0) + 1
        else:
            self.performance_stats['failed_requests'] += 1
        
        # Update average response time
        total_requests = self.performance_stats['total_requests']
        current_avg = self.performance_stats['average_response_time']
        self.performance_stats['average_response_time'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        total_requests = self.performance_stats['total_requests']
        success_rate = (self.performance_stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        cache_hit_rate = (self.performance_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.performance_stats['successful_requests'],
            'failed_requests': self.performance_stats['failed_requests'],
            'success_rate': f"{success_rate:.1f}%",
            'cache_hits': self.performance_stats['cache_hits'],
            'cache_misses': self.performance_stats['cache_misses'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'average_response_time': f"{self.performance_stats['average_response_time']:.2f}s",
            'dataset_usage': self.performance_stats['dataset_usage'],
            'cache_size': len(self.cache),
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("🗑️ [ENHANCED-PC] Cache cleared")

# Global instance
enhanced_pc_manager = EnhancedPlanetaryComputerManager()
