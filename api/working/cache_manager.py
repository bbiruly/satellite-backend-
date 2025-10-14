"""
Satellite Data Cache Manager
Provides caching functionality for satellite data to improve response times
Implements 24-hour TTL with LRU eviction policy
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

class SatelliteDataCache:
    """
    Cache manager for satellite data with TTL and LRU eviction
    """
    
    def __init__(self, ttl_hours: int = 24, max_size: int = 1000):
        """
        Initialize cache with TTL and size limits
        
        Args:
            ttl_hours: Time to live in hours (default: 24)
            max_size: Maximum number of cache entries (default: 1000)
        """
        self.cache = {}
        self.ttl_hours = ttl_hours
        self.max_size = max_size
        self.access_times = {}  # Track access times for LRU
        self.lock = Lock()  # Thread safety
        
        logger.info(f"🗄️ Cache initialized: TTL={ttl_hours}h, Max size={max_size}")
    
    def get_cache_key(self, coordinates: Tuple[float, float], date: str, 
                     crop_type: str = "GENERIC", satellite: str = "any") -> str:
        """
        Generate unique cache key for given parameters
        
        Args:
            coordinates: (latitude, longitude)
            date: Date string (YYYY-MM-DD)
            crop_type: Type of crop
            satellite: Satellite type (sentinel2, landsat, modis, any)
        
        Returns:
            MD5 hash string as cache key
        """
        lat, lon = coordinates
        key_str = f"{lat:.6f}_{lon:.6f}_{date}_{crop_type}_{satellite}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, coordinates: Tuple[float, float], date: str, 
            crop_type: str = "GENERIC", satellite: str = "any") -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and not expired
        
        Args:
            coordinates: (latitude, longitude)
            date: Date string (YYYY-MM-DD)
            crop_type: Type of crop
            satellite: Satellite type
        
        Returns:
            Cached data if available and valid, None otherwise
        """
        with self.lock:
            key = self.get_cache_key(coordinates, date, crop_type, satellite)
            
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                
                # Check if data is still valid
                if datetime.now() - timestamp < timedelta(hours=self.ttl_hours):
                    # Update access time for LRU
                    self.access_times[key] = datetime.now()
                    logger.debug(f"✅ Cache hit for key: {key[:8]}...")
                    return cached_data
                else:
                    # Remove expired data
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
                    logger.debug(f"⏰ Cache expired for key: {key[:8]}...")
            
            logger.debug(f"❌ Cache miss for key: {key[:8]}...")
            return None
    
    def set(self, coordinates: Tuple[float, float], date: str, 
            data: Dict[str, Any], crop_type: str = "GENERIC", 
            satellite: str = "any") -> None:
        """
        Cache satellite data
        
        Args:
            coordinates: (latitude, longitude)
            date: Date string (YYYY-MM-DD)
            data: Data to cache
            crop_type: Type of crop
            satellite: Satellite type
        """
        with self.lock:
            key = self.get_cache_key(coordinates, date, crop_type, satellite)
            
            # Check if we need to evict entries
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Store data with timestamp
            self.cache[key] = (data, datetime.now())
            self.access_times[key] = datetime.now()
            
            logger.debug(f"💾 Cached data for key: {key[:8]}...")
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times, key=self.access_times.get)
        
        # Remove from both dictionaries
        if lru_key in self.cache:
            del self.cache[lru_key]
        if lru_key in self.access_times:
            del self.access_times[lru_key]
        
        logger.debug(f"🗑️ Evicted LRU entry: {lru_key[:8]}...")
    
    def invalidate(self, coordinates: Tuple[float, float], date: str, 
                   crop_type: str = "GENERIC", satellite: str = "any") -> bool:
        """
        Invalidate specific cache entry
        
        Args:
            coordinates: (latitude, longitude)
            date: Date string (YYYY-MM-DD)
            crop_type: Type of crop
            satellite: Satellite type
        
        Returns:
            True if entry was found and removed, False otherwise
        """
        with self.lock:
            key = self.get_cache_key(coordinates, date, crop_type, satellite)
            
            if key in self.cache:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                logger.debug(f"🗑️ Invalidated cache entry: {key[:8]}...")
                return True
            
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("🗑️ Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            now = datetime.now()
            valid_entries = 0
            expired_entries = 0
            
            for key, (data, timestamp) in self.cache.items():
                if now - timestamp < timedelta(hours=self.ttl_hours):
                    valid_entries += 1
                else:
                    expired_entries += 1
            
            return {
                "total_entries": len(self.cache),
                "valid_entries": valid_entries,
                "expired_entries": expired_entries,
                "max_size": self.max_size,
                "ttl_hours": self.ttl_hours,
                "hit_rate_percent": self._calculate_hit_rate(),
                "memory_usage_mb": self._estimate_memory_usage()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        # This would need to track hits/misses over time
        # For now, return a placeholder
        return 0.0
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            total_size = 0
            for data, timestamp in self.cache.values():
                total_size += len(json.dumps(data).encode('utf-8'))
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        with self.lock:
            now = datetime.now()
            expired_keys = []
            
            for key, (data, timestamp) in self.cache.items():
                if now - timestamp >= timedelta(hours=self.ttl_hours):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)

# Global cache instance
satellite_cache = SatelliteDataCache(ttl_hours=24, max_size=1000)

def get_cached_satellite_data(coordinates: Tuple[float, float], date: str, 
                             crop_type: str = "GENERIC", satellite: str = "any") -> Optional[Dict[str, Any]]:
    """
    Convenience function to get cached satellite data
    
    Args:
        coordinates: (latitude, longitude)
        date: Date string (YYYY-MM-DD)
        crop_type: Type of crop
        satellite: Satellite type
    
    Returns:
        Cached data if available, None otherwise
    """
    return satellite_cache.get(coordinates, date, crop_type, satellite)

def cache_satellite_data(coordinates: Tuple[float, float], date: str, 
                        data: Dict[str, Any], crop_type: str = "GENERIC", 
                        satellite: str = "any") -> None:
    """
    Convenience function to cache satellite data
    
    Args:
        coordinates: (latitude, longitude)
        date: Date string (YYYY-MM-DD)
        data: Data to cache
        crop_type: Type of crop
        satellite: Satellite type
    """
    satellite_cache.set(coordinates, date, data, crop_type, satellite)

def get_cache_stats() -> Dict[str, Any]:
    """
    Convenience function to get cache statistics
    
    Returns:
        Dictionary with cache statistics
    """
    return satellite_cache.get_stats()

def clear_cache() -> None:
    """Convenience function to clear all cache"""
    satellite_cache.clear()

def cleanup_expired_cache() -> int:
    """
    Convenience function to cleanup expired entries
    
    Returns:
        Number of entries removed
    """
    return satellite_cache.cleanup_expired()
