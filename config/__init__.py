"""
Configuration module for the multi-satellite system
"""

from .historical_config import (
    NPK_BASE_VALUES,
    SEASONAL_FACTORS,
    VEGETATION_INDICES_CONFIG,
    WEATHER_CONFIG,
    CACHE_CONFIG
)

__all__ = [
    'NPK_BASE_VALUES',
    'SEASONAL_FACTORS', 
    'VEGETATION_INDICES_CONFIG',
    'WEATHER_CONFIG',
    'CACHE_CONFIG'
]
