#!/usr/bin/env python3
"""
Enhanced Satellite Manager
Intelligent satellite selection and retry system
"""

import asyncio
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from api.working.satellite_processors import get_satellite_processor, BaseSatelliteProcessor

logger = logging.getLogger(__name__)

class SatelliteSelector:
    """Intelligent satellite selection based on conditions"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SatelliteSelector")
        
        # Satellite configurations with priorities
        self.satellite_configs = {
            'sentinel-2-l2a': {
                'priority': 1,
                'resolution': '10m',
                'cloud_penetration': False,
                'best_for': 'clear_sky_conditions',
                'min_field_size': 0.01,  # 1 hectare
                'max_field_size': 1000,  # 1000 hectares
                'timeout': 35.0
            },
            'landsat-8-c2-l2': {
                'priority': 2,
                'resolution': '30m',
                'cloud_penetration': False,
                'best_for': 'moderate_cloud_conditions',
                'min_field_size': 0.1,  # 10 hectares
                'max_field_size': 10000,  # 10000 hectares
                'timeout': 35.0
            },
            'modis-09a1-v061': {
                'priority': 3,
                'resolution': '250m',
                'cloud_penetration': False,
                'best_for': 'large_area_coverage',
                'min_field_size': 1.0,  # 100 hectares
                'max_field_size': 100000,  # 100000 hectares
                'timeout': 25.0
            },
            'sentinel-1-rtc': {
                'priority': 4,
                'resolution': '10m',
                'cloud_penetration': True,
                'best_for': 'cloudy_conditions_monsoon',
                'min_field_size': 0.01,  # 1 hectare
                'max_field_size': 1000,  # 1000 hectares
                'timeout': 30.0
            }
        }
    
    def calculate_field_size(self, bbox: Dict[str, float]) -> float:
        """Calculate field size in hectares"""
        # Convert degrees to approximate meters (rough calculation)
        lat_center = (bbox['minLat'] + bbox['maxLat']) / 2
        
        # More accurate conversion factors
        # 1 degree latitude ≈ 111,320 meters (constant)
        # 1 degree longitude ≈ 111,320 * cos(latitude) meters
        lat_factor = 111320  # meters per degree latitude
        lon_factor = 111320 * abs(np.cos(np.radians(lat_center)))  # meters per degree longitude
        
        width_m = (bbox['maxLon'] - bbox['minLon']) * lon_factor
        height_m = (bbox['maxLat'] - bbox['minLat']) * lat_factor
        
        area_m2 = width_m * height_m
        area_hectares = area_m2 / 10000
        
        return area_hectares
    
    def detect_monsoon_phase(self, current_date: datetime = None) -> str:
        """Detect monsoon phase for India"""
        if current_date is None:
            current_date = datetime.now()
        
        month = current_date.month
        
        # Indian monsoon seasons
        if month in [6, 7, 8, 9]:  # June-September
            return 'monsoon'
        elif month in [10, 11]:  # October-November
            return 'post_monsoon'
        elif month in [12, 1, 2]:  # December-February
            return 'winter'
        else:  # March-May
            return 'pre_monsoon'
    
    def select_optimal_satellites(self, 
                                 bbox: Dict[str, float],
                                 cloud_coverage: Optional[float] = None,
                                 monsoon_phase: Optional[str] = None,
                                 field_size: Optional[float] = None) -> List[str]:
        """Select optimal satellites based on conditions"""
        
        if field_size is None:
            field_size = self.calculate_field_size(bbox)
        
        if monsoon_phase is None:
            monsoon_phase = self.detect_monsoon_phase()
        
        self.logger.info(f"🎯 Selecting satellites for field_size={field_size:.2f}ha, "
                        f"cloud_coverage={cloud_coverage}%, monsoon_phase={monsoon_phase}")
        
        selected_satellites = []
        
        # Priority 1: Clear sky conditions
        if cloud_coverage is None or cloud_coverage < 30:
            # Small to medium fields: Sentinel-2 first
            if field_size < 100:
                selected_satellites.append('sentinel-2-l2a')
                selected_satellites.append('landsat-8-c2-l2')
            # Large fields: MODIS first
            else:
                selected_satellites.append('modis-09a1-v061')
                selected_satellites.append('landsat-8-c2-l2')
                selected_satellites.append('sentinel-2-l2a')
        
        # Priority 2: Cloudy conditions
        elif cloud_coverage < 70:
            # Try optical satellites first, then SAR
            if field_size < 100:
                selected_satellites.append('sentinel-2-l2a')
                selected_satellites.append('landsat-8-c2-l2')
                selected_satellites.append('sentinel-1-rtc')
            else:
                selected_satellites.append('modis-09a1-v061')
                selected_satellites.append('landsat-8-c2-l2')
                selected_satellites.append('sentinel-1-rtc')
        
        # Priority 3: Heavy clouds or monsoon
        else:
            # SAR first for cloud penetration
            selected_satellites.append('sentinel-1-rtc')
            selected_satellites.append('modis-09a1-v061')
            selected_satellites.append('landsat-8-c2-l2')
        
        # Filter by field size constraints
        filtered_satellites = []
        for satellite_id in selected_satellites:
            config = self.satellite_configs[satellite_id]
            if config['min_field_size'] <= field_size <= config['max_field_size']:
                filtered_satellites.append(satellite_id)
        
        self.logger.info(f"🎯 Selected satellites: {filtered_satellites}")
        return filtered_satellites


class EnhancedRetryManager:
    """Enhanced retry manager with intelligent satellite selection"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EnhancedRetryManager")
        self.selector = SatelliteSelector()
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'satellite_stats': {}
        }
        
        # Simple cache (no Redis for now)
        self.coordinate_cache = {}
        self.cache_ttl = 600  # 10 minutes
        self.max_cache_size = 100
    
    def _update_performance_stats(self, satellite_id: str, processing_time: float, success: bool):
        """Update performance statistics"""
        self.performance_stats['total_requests'] += 1
        
        if success:
            self.performance_stats['successful_requests'] += 1
        else:
            self.performance_stats['failed_requests'] += 1
        
        if satellite_id not in self.performance_stats['satellite_stats']:
            self.performance_stats['satellite_stats'][satellite_id] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_processing_time': 0.0
            }
        
        stats = self.performance_stats['satellite_stats'][satellite_id]
        stats['total_requests'] += 1
        
        if success:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
        
        # Update average processing time
        stats['avg_processing_time'] = (
            (stats['avg_processing_time'] * (stats['total_requests'] - 1) + processing_time) 
            / stats['total_requests']
        )
    
    def _manage_cache_size(self):
        """Manage cache size to prevent memory issues"""
        if len(self.coordinate_cache) > self.max_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(self.coordinate_cache.keys(), 
                               key=lambda k: self.coordinate_cache[k][1])[:10]
            for key in oldest_keys:
                del self.coordinate_cache[key]
    
    def _get_cache_key(self, bbox: Dict[str, float]) -> str:
        """Generate cache key for bbox"""
        return f"{bbox['minLon']:.4f},{bbox['minLat']:.4f},{bbox['maxLon']:.4f},{bbox['maxLat']:.4f}"
    
    async def _fetch_satellite_data(self, 
                                   satellite_id: str,
                                   bbox: Dict[str, float],
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Fetch data from specific satellite"""
        config = self.selector.satellite_configs[satellite_id]
        
        try:
            # Get the appropriate processor
            processor = get_satellite_processor(satellite_id)
            
            # Run the synchronous function in an executor
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    processor.process_satellite_data,
                    bbox,
                    start_date,
                    end_date
                ),
                timeout=config['timeout']
            )
            
            if result and result.get('success'):
                result['dataset'] = satellite_id
                self.logger.info(f"✅ [ENHANCED] Success with {satellite_id}")
                return result
            else:
                self.logger.warning(f"⚠️ [ENHANCED] {satellite_id} returned no data")
                return {
                    'success': False,
                    'error': f'No data from {satellite_id}',
                    'satellite': satellite_id
                }
                
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ [ENHANCED] {satellite_id} timeout ({config['timeout']}s)")
            return {
                'success': False,
                'error': f'{satellite_id} timeout',
                'satellite': satellite_id
            }
        except Exception as e:
            self.logger.error(f"💥 [ENHANCED] {satellite_id} error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'satellite': satellite_id
            }
    
    async def get_satellite_data_with_enhanced_retry(self,
                                                   bbox: Dict[str, float],
                                                   field_id: str,
                                                   cloud_coverage: Optional[float] = None,
                                                   monsoon_phase: Optional[str] = None,
                                                   start_date: datetime = None,
                                                   end_date: datetime = None) -> Dict[str, Any]:
        """Enhanced satellite data retrieval with intelligent satellite selection"""
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(bbox)
        if cache_key in self.coordinate_cache:
            cached_result, timestamp = self.coordinate_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.logger.info(f"📦 [ENHANCED] Cache hit for {field_id}")
                return cached_result
        
        try:
            # Select optimal satellites
            optimal_satellites = self.selector.select_optimal_satellites(
                bbox=bbox,
                cloud_coverage=cloud_coverage,
                monsoon_phase=monsoon_phase
            )
            
            if not optimal_satellites:
                return {
                    'success': False,
                    'error': 'No suitable satellites found',
                    'processing_time': time.time() - start_time
                }
            
            self.logger.info(f"🛰️ [ENHANCED] Trying {len(optimal_satellites)} satellites for {field_id}")
            
            # Create tasks for all satellites
            tasks = []
            for satellite_id in optimal_satellites:
                task = asyncio.create_task(
                    self._fetch_satellite_data(satellite_id, bbox, start_date, end_date)
                )
                tasks.append((satellite_id, task))
            
            # Wait for ALL tasks to complete or timeout
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.ALL_COMPLETED,
                timeout=60.0  # Maximum 60s wait for all satellites
            )
            
            self.logger.info(f"⏱️ [ENHANCED] {len(done)} tasks completed, {len(pending)} pending")
            
            # Check ALL completed tasks for success
            successful_results = []
            for task in done:
                try:
                    result = task.result()
                    if result and result.get('success'):
                        successful_results.append(result)
                        self.logger.info(f"✅ [ENHANCED] Found successful result from task")
                except Exception as e:
                    self.logger.warning(f"⚠️ [ENHANCED] Task failed: {str(e)}")
                    continue
            
            # If we have successful results, return the first one
            if successful_results:
                result = successful_results[0]
                
                # Find which satellite succeeded
                for satellite_id, original_task in tasks:
                    if original_task.done() and original_task.result() == result:
                        # Update performance stats
                        processing_time = time.time() - start_time
                        self._update_performance_stats(satellite_id, processing_time, True)
                        
                        # Cache successful result
                        self._manage_cache_size()
                        self.coordinate_cache[cache_key] = (result, time.time())
                        
                        self.logger.info(f"✅ [ENHANCED] Success with {satellite_id} for {field_id}")
                        return result
            
            # If no successful results, return failure
            self.logger.error(f"❌ [ENHANCED] All satellites failed for {field_id}")
            return {
                'success': False,
                'error': 'All satellite datasets failed',
                'datasets_tried': optimal_satellites,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ [ENHANCED] Error in enhanced retry: {str(e)}")
            self._update_performance_stats('error', time.time() - start_time, False)
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total = self.performance_stats['total_requests']
        successful = self.performance_stats['successful_requests']
        
        stats = {
            'total_requests': total,
            'successful_requests': successful,
            'failed_requests': self.performance_stats['failed_requests'],
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'satellite_stats': self.performance_stats['satellite_stats'],
            'cache_size': len(self.coordinate_cache)
        }
        
        return stats
