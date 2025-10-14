"""
Historical Analysis Configuration
Contains configurable values for historical trend analysis
"""

# NPK Base Values Configuration
NPK_BASE_VALUES = {
    "nitrogen": {
        "min": 150.0,
        "max": 300.0,
        "default": 200.0,
        "variation_percent": 10.0
    },
    "phosphorus": {
        "min": 15.0,
        "max": 40.0,
        "default": 25.0,
        "variation_percent": 10.0
    },
    "potassium": {
        "min": 100.0,
        "max": 250.0,
        "default": 150.0,
        "variation_percent": 10.0
    },
    "soc": {
        "min": 0.5,
        "max": 3.0,
        "default": 1.5,
        "variation_percent": 10.0
    }
}

# Seasonal Factors Configuration
SEASONAL_FACTORS = {
    "monsoon": {
        "months": [6, 7, 8, 9],
        "factor": 1.2,
        "description": "June-September (Monsoon)"
    },
    "winter": {
        "months": [10, 11, 12, 1],
        "factor": 0.8,
        "description": "October-January (Winter)"
    },
    "summer": {
        "months": [2, 3, 4, 5],
        "factor": 1.0,
        "description": "February-May (Summer)"
    }
}

# Vegetation Indices Configuration
VEGETATION_INDICES_CONFIG = {
    "ndvi": {
        "monsoon": 0.6,
        "winter": 0.3,
        "summer": 0.4,
        "variation_percent": 10.0
    },
    "ndmi": {
        "base_offset": 0.2,
        "variation_percent": 10.0
    },
    "savi": {
        "multiplier": 0.8,
        "variation_percent": 10.0
    }
}

# Weather Configuration
WEATHER_CONFIG = {
    "default_condition": "clear",
    "default_temperature": 25.0,
    "default_humidity": 60.0,
    "default_cloud_cover": 0
}

# Cache Configuration
CACHE_CONFIG = {
    "ttl_hours": 24,
    "max_entries": 1000
}
