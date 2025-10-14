"""
Multi-Satellite Fallback Manager
Orchestrates fallback between different satellite data sources
Implements 4-tier fallback: Sentinel-2 → Landsat → MODIS → ICAR-Only
"""

import logging
import time
import asyncio
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

# Import satellite processing modules
from .sentinel_indices import compute_indices_and_npk_for_bbox
from .landsat_indices import compute_indices_and_npk_for_bbox_landsat
from .modis_indices import compute_indices_and_npk_for_bbox_modis
from .icar_only_analysis import generate_icar_only_analysis
from .cache_manager import get_cached_satellite_data, cache_satellite_data
from .smart_fallback_selector import get_optimal_satellite_order, get_selection_reason

logger = logging.getLogger(__name__)

# Configuration for fallback system
FALLBACK_CONFIG = {
    "sentinel2": {
        "max_cloud_cover": 80,
        "timeout_seconds": 30,
        "priority": 1,
        "name": "Sentinel-2 L2A",
        "resolution": "10m",
        "revisit_days": 5
    },
    "landsat": {
        "max_cloud_cover": 80,
        "timeout_seconds": 30,
        "priority": 2,
        "name": "Landsat-8/9 L2",
        "resolution": "30m",
        "revisit_days": 16
    },
    "modis": {
        "max_cloud_cover": 90,
        "timeout_seconds": 20,
        "priority": 3,
        "name": "MODIS Terra/Aqua",
        "resolution": "250m",
        "revisit_days": 1
    },
    "icar_only": {
        "priority": 4,
        "name": "ICAR-Only",
        "resolution": "village-level",
        "revisit_days": 0
    }
}

class MultiSatelliteFallbackManager:
    """Manages multi-satellite fallback system"""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "sentinel2_success": 0,
            "landsat_success": 0,
            "modis_success": 0,
            "icar_only_success": 0,
            "total_failures": 0,
            "average_response_time": 0.0
        }
    
    def try_sentinel2(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                     end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """
        Try to get data from Sentinel-2 L2A
        
        Args:
            bbox: Bounding box coordinates
            start_date: Start date for data search
            end_date: End date for data search
            crop_type: Type of crop
        
        Returns:
            Result dictionary with success status and data
        """
        try:
            logger.info("🛰️ Trying Sentinel-2 L2A data...")
            start_time = time.time()
            
            result = compute_indices_and_npk_for_bbox(
                bbox, 
                start_date=start_date, 
                end_date=end_date,
                crop_type=crop_type
            )
            
            processing_time = time.time() - start_time
            
            if result and result.get('success'):
                logger.info(f"✅ Sentinel-2 L2A data retrieved successfully in {processing_time:.2f}s")
                result['fallback_metadata'] = {
                    'satelliteSource': 'Sentinel-2 L2A',
                    'fallbackLevel': 1,
                    'dataQuality': 'excellent',
                    'confidenceScore': 0.95,
                    'processingTime': processing_time,
                    'resolution': '10m',
                    'revisitDays': 5
                }
                self.stats["sentinel2_success"] += 1
                return result
            else:
                logger.warning(f"❌ Sentinel-2 L2A failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Sentinel-2 data unavailable')}
                
        except Exception as e:
            logger.error(f"❌ Sentinel-2 L2A error: {e}")
            return {"success": False, "error": f"Sentinel-2 processing error: {str(e)}"}
    
    def try_landsat(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                   end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """
        Try to get data from Landsat-8/9 L2
        
        Args:
            bbox: Bounding box coordinates
            start_date: Start date for data search
            end_date: End date for data search
            crop_type: Type of crop
        
        Returns:
            Result dictionary with success status and data
        """
        try:
            logger.info("🛰️ Trying Landsat-8/9 L2 data...")
            start_time = time.time()
            
            result = compute_indices_and_npk_for_bbox_landsat(
                bbox, 
                start_date=start_date, 
                end_date=end_date,
                crop_type=crop_type
            )
            
            processing_time = time.time() - start_time
            
            if result and result.get('success'):
                logger.info(f"✅ Landsat-8/9 L2 data retrieved successfully in {processing_time:.2f}s")
                result['fallback_metadata'] = {
                    'satelliteSource': 'Landsat-8/9 L2',
                    'fallbackLevel': 2,
                    'dataQuality': 'good',
                    'confidenceScore': 0.90,
                    'processingTime': processing_time,
                    'resolution': '30m',
                    'revisitDays': 16
                }
                self.stats["landsat_success"] += 1
                return result
            else:
                logger.warning(f"❌ Landsat-8/9 L2 failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Landsat data unavailable')}
                
        except Exception as e:
            logger.error(f"❌ Landsat-8/9 L2 error: {e}")
            return {"success": False, "error": f"Landsat processing error: {str(e)}"}
    
    def try_modis(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                 end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """
        Try to get data from MODIS Terra/Aqua
        
        Args:
            bbox: Bounding box coordinates
            start_date: Start date for data search
            end_date: End date for data search
            crop_type: Type of crop
        
        Returns:
            Result dictionary with success status and data
        """
        try:
            logger.info("🛰️ Trying MODIS Terra/Aqua data...")
            start_time = time.time()
            
            result = compute_indices_and_npk_for_bbox_modis(
                bbox, 
                start_date=start_date, 
                end_date=end_date,
                crop_type=crop_type
            )
            
            processing_time = time.time() - start_time
            
            if result and result.get('success'):
                logger.info(f"✅ MODIS Terra/Aqua data retrieved successfully in {processing_time:.2f}s")
                result['fallback_metadata'] = {
                    'satelliteSource': 'MODIS Terra/Aqua',
                    'fallbackLevel': 3,
                    'dataQuality': 'acceptable',
                    'confidenceScore': 0.80,
                    'processingTime': processing_time,
                    'resolution': '250m',
                    'revisitDays': 1
                }
                self.stats["modis_success"] += 1
                return result
            else:
                logger.warning(f"❌ MODIS Terra/Aqua failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'MODIS data unavailable')}
                
        except Exception as e:
            logger.error(f"❌ MODIS Terra/Aqua error: {e}")
            return {"success": False, "error": f"MODIS processing error: {str(e)}"}
    
    def try_icar_only(self, coordinates: Tuple[float, float], crop_type: str, 
                     field_area_ha: float = 1.0, analysis_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Try to get data from ICAR-only analysis (last resort)
        
        Args:
            coordinates: (latitude, longitude)
            crop_type: Type of crop
            field_area_ha: Field area in hectares
            analysis_date: Date of analysis
        
        Returns:
            Result dictionary with success status and data
        """
        try:
            logger.info("🏛️ Trying ICAR-only analysis...")
            start_time = time.time()
            
            result = generate_icar_only_analysis(
                coordinates=coordinates,
                crop_type=crop_type,
                field_area_ha=field_area_ha,
                analysis_date=analysis_date
            )
            
            processing_time = time.time() - start_time
            
            if result and result.get('success'):
                logger.info(f"✅ ICAR-only analysis completed successfully in {processing_time:.2f}s")
                result['fallback_metadata'] = {
                    'satelliteSource': 'ICAR-Only',
                    'fallbackLevel': 4,
                    'dataQuality': 'basic',
                    'confidenceScore': result.get('confidenceScore', 0.70),
                    'processingTime': processing_time,
                    'resolution': 'village-level',
                    'revisitDays': 0
                }
                self.stats["icar_only_success"] += 1
                return result
            else:
                logger.error(f"❌ ICAR-only analysis failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'ICAR analysis failed')}
                
        except Exception as e:
            logger.error(f"❌ ICAR-only analysis error: {e}")
            return {"success": False, "error": f"ICAR analysis error: {str(e)}"}
    
    async def _try_sentinel2_async(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                                  end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Async wrapper for Sentinel-2 data retrieval with retry logic"""
        return await self._try_satellite_with_retry(
            'sentinel2', 
            lambda: self._execute_sentinel2(bbox, start_date, end_date, crop_type)
        )
    
    async def _execute_sentinel2(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                                end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Execute Sentinel-2 data retrieval"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            compute_indices_and_npk_for_bbox,
            bbox, start_date, end_date, crop_type
        )
        
        if result and result.get('success'):
            result['fallback_metadata'] = {
                'satelliteSource': 'Sentinel-2 L2A',
                'fallbackLevel': 1,
                'dataQuality': 'excellent',
                'confidenceScore': 0.95,
                'resolution': '10m',
                'revisitDays': 5
            }
            self.stats["sentinel2_success"] += 1
            return result
        else:
            return {"success": False, "error": result.get('error', 'Sentinel-2 data unavailable')}
    
    async def _try_landsat_async(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                                end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Async wrapper for Landsat data retrieval with retry logic"""
        return await self._try_satellite_with_retry(
            'landsat', 
            lambda: self._execute_landsat(bbox, start_date, end_date, crop_type)
        )
    
    async def _execute_landsat(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                              end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Execute Landsat data retrieval"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            compute_indices_and_npk_for_bbox_landsat,
            bbox, start_date, end_date, crop_type
        )
        
        if result and result.get('success'):
            result['fallback_metadata'] = {
                'satelliteSource': 'Landsat-8/9 L2',
                'fallbackLevel': 2,
                'dataQuality': 'good',
                'confidenceScore': 0.90,
                'resolution': '30m',
                'revisitDays': 16
            }
            self.stats["landsat_success"] += 1
            return result
        else:
            return {"success": False, "error": result.get('error', 'Landsat data unavailable')}
    
    async def _try_modis_async(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                              end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Async wrapper for MODIS data retrieval with retry logic"""
        return await self._try_satellite_with_retry(
            'modis', 
            lambda: self._execute_modis(bbox, start_date, end_date, crop_type)
        )
    
    async def _execute_modis(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                            end_date: Optional[datetime], crop_type: str) -> Dict[str, Any]:
        """Execute MODIS data retrieval"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            compute_indices_and_npk_for_bbox_modis,
            bbox, start_date, end_date, crop_type
        )
        
        if result and result.get('success'):
            result['fallback_metadata'] = {
                'satelliteSource': 'MODIS Terra/Aqua',
                'fallbackLevel': 3,
                'dataQuality': 'acceptable',
                'confidenceScore': 0.80,
                'resolution': '250m',
                'revisitDays': 1
            }
            self.stats["modis_success"] += 1
            return result
        else:
            return {"success": False, "error": result.get('error', 'MODIS data unavailable')}
    
    async def _try_satellite_with_retry(self, satellite_name: str, satellite_func, 
                                       max_retries: int = 3) -> Dict[str, Any]:
        """
        Try satellite with automatic retry on failure
        
        Args:
            satellite_name: Name of the satellite
            satellite_func: Async function to execute
            max_retries: Maximum number of retries
        
        Returns:
            Result dictionary
        """
        for attempt in range(max_retries):
            try:
                result = await satellite_func()
                if result.get('success'):
                    if attempt > 0:
                        logger.info(f"✅ {satellite_name} succeeded on attempt {attempt + 1}")
                    return result
                else:
                    logger.warning(f"⚠️ {satellite_name} attempt {attempt + 1} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ {satellite_name} attempt {attempt + 1} error: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                logger.info(f"⏳ Retrying {satellite_name} in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"❌ {satellite_name} failed after {max_retries} attempts")
        return {"success": False, "error": f"{satellite_name} failed after {max_retries} attempts"}
    
    async def get_npk_with_parallel_fallback(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                                           end_date: Optional[datetime], crop_type: str, 
                                           coordinates: Tuple[float, float], field_area_ha: float = 1.0) -> Dict[str, Any]:
        """
        Parallel fallback system - checks all satellites simultaneously
        
        Args:
            bbox: Bounding box coordinates
            start_date: Start date for data search
            end_date: End date for data search
            crop_type: Type of crop
            coordinates: (latitude, longitude)
            field_area_ha: Field area in hectares
        
        Returns:
            Result dictionary with data from the first successful source
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        logger.info(f"🚀 Starting parallel multi-satellite fallback for {crop_type} at {coordinates}")
        
        # Check cache first
        date_str = start_date.strftime('%Y-%m-%d') if start_date else datetime.now().strftime('%Y-%m-%d')
        
        # Try to get cached data for any satellite
        cached_result = get_cached_satellite_data(coordinates, date_str, crop_type, "any")
        if cached_result:
            total_time = time.time() - start_time
            cached_result['fallback_metadata']['processingTime'] = total_time
            cached_result['fallback_metadata']['cached'] = True
            logger.info(f"⚡ Cache hit! Returning cached data in {total_time:.2f}s")
            return cached_result
        
        # Get optimal satellite order based on conditions
        optimal_order = get_optimal_satellite_order(coordinates, start_date or datetime.now(), crop_type)
        selection_reason = get_selection_reason(coordinates, start_date or datetime.now(), crop_type, optimal_order)
        logger.info(f"🧠 Smart selection: {selection_reason}")
        
        # Create async tasks for satellites in optimal order
        tasks = {}
        if 'sentinel2' in optimal_order:
            tasks['sentinel2'] = asyncio.create_task(self._try_sentinel2_async(bbox, start_date, end_date, crop_type))
        if 'landsat' in optimal_order:
            tasks['landsat'] = asyncio.create_task(self._try_landsat_async(bbox, start_date, end_date, crop_type))
        if 'modis' in optimal_order:
            tasks['modis'] = asyncio.create_task(self._try_modis_async(bbox, start_date, end_date, crop_type))
        
        # Wait for first successful result with timeout
        try:
            for task_name, task in tasks.items():
                try:
                    result = await asyncio.wait_for(task, timeout=15.0)
                    if result.get('success'):
                        # Cancel other tasks
                        for other_task in tasks.values():
                            if other_task != task:
                                other_task.cancel()
                        
                        total_time = time.time() - start_time
                        result['fallback_metadata']['processingTime'] = total_time
                        result['fallback_metadata']['cached'] = False
                        self.stats["average_response_time"] = (
                            (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                            / self.stats["total_requests"]
                        )
                        
                        # Cache the successful result
                        cache_satellite_data(coordinates, date_str, result, crop_type, task_name)
                        
                        logger.info(f"🎯 Parallel fallback successful with {task_name} in {total_time:.2f}s")
                        return result
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ {task_name} timed out")
                    continue
        except Exception as e:
            logger.error(f"❌ Parallel fallback error: {e}")
        
        # If all satellites fail, try ICAR-only
        logger.info("🔄 All satellites failed, trying ICAR-only analysis...")
        result = self.try_icar_only(coordinates, crop_type, field_area_ha, start_date)
        if result.get('success'):
            total_time = time.time() - start_time
            result['fallback_metadata']['processingTime'] = total_time
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                / self.stats["total_requests"]
            )
            logger.info(f"🎯 Fallback successful at Level 4 (ICAR-Only) in {total_time:.2f}s")
            return result
        
        # If all sources fail
        self.stats["total_failures"] += 1
        total_time = time.time() - start_time
        logger.error(f"❌ All fallback levels failed after {total_time:.2f}s")
        
        return {
            "success": False,
            "error": "All satellite sources and ICAR analysis failed",
            "fallback_metadata": {
                'satelliteSource': 'None',
                'fallbackLevel': 0,
                'dataQuality': 'none',
                'confidenceScore': 0.0,
                'processingTime': total_time,
                'resolution': 'none',
                'revisitDays': 0
            }
        }

    def get_npk_with_fallback(self, bbox: Dict[str, float], start_date: Optional[datetime], 
                            end_date: Optional[datetime], crop_type: str, 
                            coordinates: Tuple[float, float], field_area_ha: float = 1.0) -> Dict[str, Any]:
        """
        Main orchestrator function that tries all satellite sources in order
        
        Args:
            bbox: Bounding box coordinates
            start_date: Start date for data search
            end_date: End date for data search
            crop_type: Type of crop
            coordinates: (latitude, longitude)
            field_area_ha: Field area in hectares
        
        Returns:
            Result dictionary with data from the first successful source
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        logger.info(f"🚀 Starting multi-satellite fallback for {crop_type} at {coordinates}")
        
        # Try Sentinel-2 L2A (Level 1)
        result = self.try_sentinel2(bbox, start_date, end_date, crop_type)
        if result.get('success'):
            total_time = time.time() - start_time
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                / self.stats["total_requests"]
            )
            logger.info(f"🎯 Fallback successful at Level 1 (Sentinel-2 L2A) in {total_time:.2f}s")
            return result
        
        # Try Landsat-8/9 L2 (Level 2)
        result = self.try_landsat(bbox, start_date, end_date, crop_type)
        if result.get('success'):
            total_time = time.time() - start_time
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                / self.stats["total_requests"]
            )
            logger.info(f"🎯 Fallback successful at Level 2 (Landsat-8/9 L2) in {total_time:.2f}s")
            return result
        
        # Try MODIS Terra/Aqua (Level 3)
        result = self.try_modis(bbox, start_date, end_date, crop_type)
        if result.get('success'):
            total_time = time.time() - start_time
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                / self.stats["total_requests"]
            )
            logger.info(f"🎯 Fallback successful at Level 3 (MODIS Terra/Aqua) in {total_time:.2f}s")
            return result
        
        # Try ICAR-only analysis (Level 4 - Last resort)
        result = self.try_icar_only(coordinates, crop_type, field_area_ha, start_date)
        if result.get('success'):
            total_time = time.time() - start_time
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + total_time) 
                / self.stats["total_requests"]
            )
            logger.info(f"🎯 Fallback successful at Level 4 (ICAR-Only) in {total_time:.2f}s")
            return result
        
        # If all sources fail (should never happen with ICAR-only)
        self.stats["total_failures"] += 1
        total_time = time.time() - start_time
        logger.error(f"❌ All fallback levels failed after {total_time:.2f}s")
        
        return {
            "success": False,
            "error": "All satellite sources and ICAR analysis failed",
            "fallback_metadata": {
                'satelliteSource': 'None',
                'fallbackLevel': 0,
                'dataQuality': 'none',
                'confidenceScore': 0.0,
                'processingTime': total_time,
                'resolution': 'none',
                'revisitDays': 0
            }
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the fallback system"""
        total_success = (
            self.stats["sentinel2_success"] + 
            self.stats["landsat_success"] + 
            self.stats["modis_success"] + 
            self.stats["icar_only_success"]
        )
        
        success_rate = (total_success / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            "total_requests": self.stats["total_requests"],
            "success_rate_percent": round(success_rate, 2),
            "average_response_time_seconds": round(self.stats["average_response_time"], 2),
            "satellite_usage": {
                "sentinel2": {
                    "success_count": self.stats["sentinel2_success"],
                    "success_rate_percent": round(self.stats["sentinel2_success"] / self.stats["total_requests"] * 100, 2) if self.stats["total_requests"] > 0 else 0
                },
                "landsat": {
                    "success_count": self.stats["landsat_success"],
                    "success_rate_percent": round(self.stats["landsat_success"] / self.stats["total_requests"] * 100, 2) if self.stats["total_requests"] > 0 else 0
                },
                "modis": {
                    "success_count": self.stats["modis_success"],
                    "success_rate_percent": round(self.stats["modis_success"] / self.stats["total_requests"] * 100, 2) if self.stats["total_requests"] > 0 else 0
                },
                "icar_only": {
                    "success_count": self.stats["icar_only_success"],
                    "success_rate_percent": round(self.stats["icar_only_success"] / self.stats["total_requests"] * 100, 2) if self.stats["total_requests"] > 0 else 0
                }
            },
            "total_failures": self.stats["total_failures"],
            "fallback_config": FALLBACK_CONFIG
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.stats = {
            "total_requests": 0,
            "sentinel2_success": 0,
            "landsat_success": 0,
            "modis_success": 0,
            "icar_only_success": 0,
            "total_failures": 0,
            "average_response_time": 0.0
        }
        logger.info("📊 Fallback statistics reset")

# Global instance for use across the application
fallback_manager = MultiSatelliteFallbackManager()
