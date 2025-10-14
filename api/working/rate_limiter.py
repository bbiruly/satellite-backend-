"""
Rate Limiter
Prevents API abuse by limiting requests per client
"""

import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter with configurable limits and time windows
    """
    
    def __init__(self, max_requests_per_minute: int = 60, max_requests_per_hour: int = 1000):
        """
        Initialize rate limiter
        
        Args:
            max_requests_per_minute: Maximum requests per minute per client
            max_requests_per_hour: Maximum requests per hour per client
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        
        # Track requests per client
        self.minute_requests = defaultdict(list)  # client_id -> [timestamps]
        self.hour_requests = defaultdict(list)    # client_id -> [timestamps]
        
        # Thread safety
        self.lock = Lock()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "active_clients": 0
        }
        
        logger.info(f"🚦 Rate limiter initialized: {max_requests_per_minute}/min, {max_requests_per_hour}/hour")
    
    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique client identifier
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            hour_ago = now - 3600
            
            # Clean old requests
            self._cleanup_old_requests(client_id, now)
            
            # Check minute limit
            minute_count = len(self.minute_requests[client_id])
            if minute_count >= self.max_requests_per_minute:
                self.stats["blocked_requests"] += 1
                logger.warning(f"🚫 Rate limit exceeded for {client_id}: {minute_count}/{self.max_requests_per_minute} per minute")
                return False, {
                    "allowed": False,
                    "reason": "minute_limit_exceeded",
                    "limit": self.max_requests_per_minute,
                    "current": minute_count,
                    "reset_in_seconds": 60 - (now - self.minute_requests[client_id][0]) if self.minute_requests[client_id] else 0
                }
            
            # Check hour limit
            hour_count = len(self.hour_requests[client_id])
            if hour_count >= self.max_requests_per_hour:
                self.stats["blocked_requests"] += 1
                logger.warning(f"🚫 Rate limit exceeded for {client_id}: {hour_count}/{self.max_requests_per_hour} per hour")
                return False, {
                    "allowed": False,
                    "reason": "hour_limit_exceeded",
                    "limit": self.max_requests_per_hour,
                    "current": hour_count,
                    "reset_in_seconds": 3600 - (now - self.hour_requests[client_id][0]) if self.hour_requests[client_id] else 0
                }
            
            # Record this request
            self.minute_requests[client_id].append(now)
            self.hour_requests[client_id].append(now)
            self.stats["total_requests"] += 1
            
            # Update active clients count
            self.stats["active_clients"] = len(self.minute_requests)
            
            return True, {
                "allowed": True,
                "minute_remaining": self.max_requests_per_minute - minute_count - 1,
                "hour_remaining": self.max_requests_per_hour - hour_count - 1,
                "reset_in_seconds": 60 - (now - self.minute_requests[client_id][0]) if self.minute_requests[client_id] else 0
            }
    
    def _cleanup_old_requests(self, client_id: str, now: float) -> None:
        """Remove old requests from tracking"""
        # Clean minute requests
        self.minute_requests[client_id] = [
            req_time for req_time in self.minute_requests[client_id] 
            if now - req_time < 60
        ]
        
        # Clean hour requests
        self.hour_requests[client_id] = [
            req_time for req_time in self.hour_requests[client_id] 
            if now - req_time < 3600
        ]
    
    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific client
        
        Args:
            client_id: Client identifier
        
        Returns:
            Client statistics
        """
        with self.lock:
            now = time.time()
            self._cleanup_old_requests(client_id, now)
            
            minute_count = len(self.minute_requests[client_id])
            hour_count = len(self.hour_requests[client_id])
            
            return {
                "client_id": client_id,
                "requests_last_minute": minute_count,
                "requests_last_hour": hour_count,
                "minute_limit": self.max_requests_per_minute,
                "hour_limit": self.max_requests_per_hour,
                "minute_remaining": max(0, self.max_requests_per_minute - minute_count),
                "hour_remaining": max(0, self.max_requests_per_hour - hour_count)
            }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global rate limiter statistics
        
        Returns:
            Global statistics
        """
        with self.lock:
            now = time.time()
            
            # Clean all old requests
            for client_id in list(self.minute_requests.keys()):
                self._cleanup_old_requests(client_id, now)
                if not self.minute_requests[client_id] and not self.hour_requests[client_id]:
                    del self.minute_requests[client_id]
                    del self.hour_requests[client_id]
            
            # Calculate active clients
            active_clients = len(self.minute_requests)
            
            # Calculate total requests in last hour
            total_hour_requests = sum(len(requests) for requests in self.hour_requests.values())
            
            return {
                "total_requests": self.stats["total_requests"],
                "blocked_requests": self.stats["blocked_requests"],
                "active_clients": active_clients,
                "total_hour_requests": total_hour_requests,
                "block_rate_percent": round(
                    (self.stats["blocked_requests"] / max(1, self.stats["total_requests"])) * 100, 2
                ),
                "limits": {
                    "max_requests_per_minute": self.max_requests_per_minute,
                    "max_requests_per_hour": self.max_requests_per_hour
                }
            }
    
    def reset_client(self, client_id: str) -> bool:
        """
        Reset rate limit for a specific client
        
        Args:
            client_id: Client identifier
        
        Returns:
            True if client was found and reset
        """
        with self.lock:
            if client_id in self.minute_requests or client_id in self.hour_requests:
                if client_id in self.minute_requests:
                    del self.minute_requests[client_id]
                if client_id in self.hour_requests:
                    del self.hour_requests[client_id]
                logger.info(f"🔄 Rate limit reset for client: {client_id}")
                return True
            return False
    
    def reset_all(self) -> None:
        """Reset all rate limiting data"""
        with self.lock:
            self.minute_requests.clear()
            self.hour_requests.clear()
            self.stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "active_clients": 0
            }
            logger.info("🔄 All rate limits reset")
    
    def update_limits(self, max_requests_per_minute: int = None, 
                     max_requests_per_hour: int = None) -> None:
        """
        Update rate limiting limits
        
        Args:
            max_requests_per_minute: New minute limit
            max_requests_per_hour: New hour limit
        """
        with self.lock:
            if max_requests_per_minute is not None:
                self.max_requests_per_minute = max_requests_per_minute
            if max_requests_per_hour is not None:
                self.max_requests_per_hour = max_requests_per_hour
            
            logger.info(f"🔄 Rate limits updated: {self.max_requests_per_minute}/min, {self.max_requests_per_hour}/hour")

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests_per_minute=60, max_requests_per_hour=1000)

def check_rate_limit(client_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to check rate limit
    
    Args:
        client_id: Client identifier
    
    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    return rate_limiter.is_allowed(client_id)

def get_rate_limit_stats() -> Dict[str, Any]:
    """
    Convenience function to get rate limit statistics
    
    Returns:
        Global statistics
    """
    return rate_limiter.get_global_stats()

def get_client_rate_limit_stats(client_id: str) -> Dict[str, Any]:
    """
    Convenience function to get client-specific statistics
    
    Args:
        client_id: Client identifier
    
    Returns:
        Client statistics
    """
    return rate_limiter.get_client_stats(client_id)

def reset_client_rate_limit(client_id: str) -> bool:
    """
    Convenience function to reset client rate limit
    
    Args:
        client_id: Client identifier
    
    Returns:
        True if reset successful
    """
    return rate_limiter.reset_client(client_id)
