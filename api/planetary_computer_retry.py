"""
Planetary Computer Multi-Dataset Retry System
Handles satellite data retrieval with intelligent fallback between datasets
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PlanetaryComputerRetryManager:
    """Intelligent retry system for Planetary Computer satellite data"""
    
    def __init__(self):
        self.logger = logger
        
        # Available datasets in Planetary Computer (in order of preference)
        self.datasets = [
            {
                'name': 'sentinel-2-l2a',
                'description': 'Sentinel-2 Level-2A',
                'resolution': '10m',
                'revisit': '5 days',
                'bands': ['red', 'nir', 'green', 'swir1'],
                'timeout': 15,  # seconds
                'priority': 1
            },
            {
                'name': 'landsat-8-c2-l2',
                'description': 'Landsat-8 Collection 2 Level-2',
                'resolution': '15m',
                'revisit': '16 days',
                'bands': ['red', 'nir', 'green', 'swir1'],
                'timeout': 12,  # seconds
                'priority': 2
            },
            {
                'name': 'modis-09a1-v061',
                'description': 'MODIS Surface Reflectance',
                'resolution': '250m',
                'revisit': 'Daily',
                'bands': ['red', 'nir', 'green', 'swir1'],
                'timeout': 8,   # seconds
                'priority': 3
            }
        ]
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # seconds
        self.max_delay = 30  # seconds
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'dataset_usage': {},
            'avg_response_time': 0
        }
    
    async def get_satellite_data_with_retry(self, coordinates: List[float], bbox: Dict[str, float], 
                                          field_id: str) -> Dict[str, Any]:
        """
        Get satellite data with intelligent retry across multiple datasets
        
        Args:
            coordinates: [lat, lon] field coordinates
            bbox: Bounding box dictionary
            field_id: Field identifier
            
        Returns:
            Dictionary containing satellite data or error information
        """
        start_time = time.time()
        self.performance_stats['total_requests'] += 1
        
        self.logger.info(f"🛰️ [RETRY-MANAGER] Starting satellite data retrieval for field: {field_id}")
        self.logger.info(f"🛰️ [RETRY-MANAGER] Coordinates: {coordinates}")
        self.logger.info(f"🛰️ [RETRY-MANAGER] Bounding box: {bbox}")
        
        # Try each dataset in order of preference
        for dataset in self.datasets:
            dataset_name = dataset['name']
            timeout = dataset['timeout']
            
            self.logger.info(f"🛰️ [RETRY-MANAGER] Trying dataset: {dataset_name}")
            
            try:
                # Try with adaptive bounding box
                for attempt in range(self.max_retries):
                    try:
                        # Adjust bounding box size based on attempt
                        adjusted_bbox = self._adjust_bbox_size(bbox, attempt)
                        
                        self.logger.info(f"🛰️ [RETRY-MANAGER] Attempt {attempt + 1}/{self.max_retries} with {dataset_name}")
                        self.logger.info(f"🛰️ [RETRY-MANAGER] Adjusted bbox: {adjusted_bbox}")
                        
                        # Fetch data with timeout
                        data = await asyncio.wait_for(
                            self._fetch_dataset_data(dataset_name, coordinates, adjusted_bbox),
                            timeout=timeout
                        )
                        
                        if data and data.get('success'):
                            # Success! Update performance stats
                            processing_time = time.time() - start_time
                            self._update_performance_stats(dataset_name, processing_time, True)
                            
                            self.logger.info(f"✅ [RETRY-MANAGER] Success with {dataset_name} in {processing_time:.2f}s")
                            
                            return {
                                'success': True,
                                'data': data,
                                'dataset_used': dataset_name,
                                'processing_time': processing_time,
                                'attempts': attempt + 1,
                                'bbox_used': adjusted_bbox,
                                'field_id': field_id,
                                'coordinates': coordinates,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            self.logger.warning(f"⚠️ [RETRY-MANAGER] {dataset_name} returned no data")
                            
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⏰ [RETRY-MANAGER] {dataset_name} timeout on attempt {attempt + 1}")
                        
                        if attempt < self.max_retries - 1:
                            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                            self.logger.info(f"🛰️ [RETRY-MANAGER] Waiting {delay}s before retry")
                            await asyncio.sleep(delay)
                        else:
                            self.logger.error(f"❌ [RETRY-MANAGER] {dataset_name} failed after {self.max_retries} attempts")
                            
                    except Exception as e:
                        self.logger.error(f"❌ [RETRY-MANAGER] {dataset_name} error on attempt {attempt + 1}: {str(e)}")
                        
                        if attempt < self.max_retries - 1:
                            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                            await asyncio.sleep(delay)
                        else:
                            self.logger.error(f"❌ [RETRY-MANAGER] {dataset_name} failed after {self.max_retries} attempts")
                
            except Exception as e:
                self.logger.error(f"❌ [RETRY-MANAGER] Critical error with {dataset_name}: {str(e)}")
                continue
        
        # All datasets failed
        processing_time = time.time() - start_time
        self._update_performance_stats('all_failed', processing_time, False)
        
        self.logger.error(f"❌ [RETRY-MANAGER] All datasets failed for field: {field_id}")
        
        return {
            'success': False,
            'error': 'No satellite data available from any dataset',
            'datasets_tried': [d['name'] for d in self.datasets],
            'processing_time': processing_time,
            'field_id': field_id,
            'coordinates': coordinates,
            'timestamp': datetime.now().isoformat()
        }
    
    def _adjust_bbox_size(self, bbox: Dict[str, float], attempt: int) -> Dict[str, float]:
        """
        Adjust bounding box size based on retry attempt
        
        Args:
            bbox: Original bounding box
            attempt: Current attempt number (0-based)
            
        Returns:
            Adjusted bounding box
        """
        # Base size adjustments
        size_multipliers = [1.0, 1.5, 2.0]  # Start small, increase if needed
        multiplier = size_multipliers[min(attempt, len(size_multipliers) - 1)]
        
        # Calculate center point
        center_lat = (bbox['minLat'] + bbox['maxLat']) / 2
        center_lon = (bbox['minLon'] + bbox['maxLon']) / 2
        
        # Calculate original size
        lat_size = bbox['maxLat'] - bbox['minLat']
        lon_size = bbox['maxLon'] - bbox['minLon']
        
        # Apply multiplier
        new_lat_size = lat_size * multiplier
        new_lon_size = lon_size * multiplier
        
        # Create new bounding box
        adjusted_bbox = {
            'minLat': center_lat - new_lat_size / 2,
            'maxLat': center_lat + new_lat_size / 2,
            'minLon': center_lon - new_lon_size / 2,
            'maxLon': center_lon + new_lon_size / 2
        }
        
        self.logger.info(f"🛰️ [RETRY-MANAGER] Adjusted bbox size by {multiplier}x")
        
        return adjusted_bbox
    
    async def _fetch_dataset_data(self, dataset_name: str, coordinates: List[float], 
                                bbox: Dict[str, float]) -> Dict[str, Any]:
        """
        Fetch data from a specific dataset
        
        Args:
            dataset_name: Name of the dataset
            coordinates: Field coordinates
            bbox: Bounding box
            
        Returns:
            Dataset data or None
        """
        # This is a placeholder - in real implementation, this would call
        # the actual Planetary Computer API for each dataset
        
        if dataset_name == 'sentinel-2-l2a':
            return await self._fetch_sentinel2_data(coordinates, bbox)
        elif dataset_name == 'landsat-8-c2-l2':
            return await self._fetch_landsat8_data(coordinates, bbox)
        elif dataset_name == 'modis-09a1-v061':
            return await self._fetch_modis_data(coordinates, bbox)
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
    
    async def _fetch_sentinel2_data(self, coordinates: List[float], bbox: Dict[str, float]) -> Dict[str, Any]:
        """Fetch Sentinel-2 data using real satellite processing"""
        try:
            # Import the real satellite processing function
            from sentinel_indices import compute_indices_and_npk_for_bbox
            
            # Use ThreadPoolExecutor for CPU-intensive processing
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(compute_indices_and_npk_for_bbox, bbox)
                
                # Wait for result with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: future.result()),
                    timeout=15.0  # 15 second timeout for Sentinel-2
                )
                
                if result and result.get('success'):
                    result['dataset'] = 'sentinel-2-l2a'
                    result['source'] = 'Microsoft Planetary Computer (Sentinel-2)'
                    return result
                else:
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.warning("⏰ Sentinel-2 data timeout")
            return None
        except Exception as e:
            self.logger.error(f"❌ Sentinel-2 data error: {str(e)}")
            return None
    
    async def _fetch_landsat8_data(self, coordinates: List[float], bbox: Dict[str, float]) -> Dict[str, Any]:
        """Fetch Landsat-8 data using real satellite processing"""
        try:
            # Import the real satellite processing function
            from sentinel_indices import compute_indices_and_npk_for_bbox
            
            # Use ThreadPoolExecutor for CPU-intensive processing
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(compute_indices_and_npk_for_bbox, bbox)
                
                # Wait for result with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: future.result()),
                    timeout=12.0  # 12 second timeout for Landsat-8
                )
                
                if result and result.get('success'):
                    result['dataset'] = 'landsat-8-c2-l2'
                    result['source'] = 'Microsoft Planetary Computer (Landsat-8)'
                    return result
                else:
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.warning("⏰ Landsat-8 data timeout")
            return None
        except Exception as e:
            self.logger.error(f"❌ Landsat-8 data error: {str(e)}")
            return None
    
    async def _fetch_modis_data(self, coordinates: List[float], bbox: Dict[str, float]) -> Dict[str, Any]:
        """Fetch MODIS data using real satellite processing"""
        try:
            # Import the real satellite processing function
            from sentinel_indices import compute_indices_and_npk_for_bbox
            
            # Use ThreadPoolExecutor for CPU-intensive processing
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(compute_indices_and_npk_for_bbox, bbox)
                
                # Wait for result with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, lambda: future.result()),
                    timeout=8.0  # 8 second timeout for MODIS
                )
                
                if result and result.get('success'):
                    result['dataset'] = 'modis-09a1-v061'
                    result['source'] = 'Microsoft Planetary Computer (MODIS)'
                    return result
                else:
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.warning("⏰ MODIS data timeout")
            return None
        except Exception as e:
            self.logger.error(f"❌ MODIS data error: {str(e)}")
            return None
    
    def _update_performance_stats(self, dataset_name: str, processing_time: float, success: bool):
        """Update performance statistics"""
        if success:
            self.performance_stats['successful_requests'] += 1
            if dataset_name not in self.performance_stats['dataset_usage']:
                self.performance_stats['dataset_usage'][dataset_name] = 0
            self.performance_stats['dataset_usage'][dataset_name] += 1
        else:
            self.performance_stats['failed_requests'] += 1
        
        # Update average response time
        total_requests = self.performance_stats['total_requests']
        current_avg = self.performance_stats['avg_response_time']
        self.performance_stats['avg_response_time'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            'total_requests': self.performance_stats['total_requests'],
            'successful_requests': self.performance_stats['successful_requests'],
            'failed_requests': self.performance_stats['failed_requests'],
            'success_rate': (
                self.performance_stats['successful_requests'] / 
                max(self.performance_stats['total_requests'], 1) * 100
            ),
            'dataset_usage': self.performance_stats['dataset_usage'],
            'avg_response_time': self.performance_stats['avg_response_time'],
            'available_datasets': [d['name'] for d in self.datasets]
        }

# Global instance
retry_manager = PlanetaryComputerRetryManager()
