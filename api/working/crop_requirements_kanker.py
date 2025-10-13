"""
Crop Requirements Module - Kanker District Specific
Based on actual Kanker soil analysis data from 91 villages
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class NutrientRange:
    """Nutrient range data structure"""
    min_value: float
    max_value: float
    status: str
    description: str

@dataclass
class CropRequirement:
    """Crop requirement data structure"""
    crop_name: str
    optimal_npk: Dict[str, Dict[str, float]]
    optimal_micronutrients: Dict[str, Dict[str, float]] = None
    optimal_ph_range: List[float] = None
    kanker_ranges: Dict[str, Dict[str, Tuple[float, float]]] = None
    micronutrient_ranges: Dict[str, Dict[str, Tuple[float, float]]] = None
    ph_ranges: Dict[str, Tuple[float, float]] = None
    deficiency_symptoms: Dict[str, str] = None
    growth_stages: Dict[str, Dict[str, Any]] = None

# Kanker District Crop Requirements (Based on 91 villages data analysis)
KANKER_CROP_REQUIREMENTS = {
    "RICE": CropRequirement(
        crop_name="Rice (Paddy)",
        optimal_npk={
            "N": {"min": 120, "max": 150, "unit": "kg/ha", "status_ranges": {"low": [0, 100], "medium": [101, 140], "high": [141, 200], "excess": [201, 9999]}},
            "P": {"min": 40, "max": 60, "unit": "kg/ha", "status_ranges": {"low": [0, 15], "medium": [16, 35], "high": [36, 60], "excess": [61, 9999]}},  # FIXED: Aligned with ICAR data
            "K": {"min": 40, "max": 60, "unit": "kg/ha", "status_ranges": {"low": [0, 30], "medium": [31, 50], "high": [51, 80], "excess": [81, 9999]}},
            "Soc": {"min": 0.8, "max": 1.5, "unit": "%", "status_ranges": {"low": [0, 0.7], "medium": [0.71, 1.2], "high": [1.21, 2.0], "excess": [2.01, 9999]}}
        },
        optimal_micronutrients={
            "Boron": {"min": 0.5, "max": 1.2, "unit": "ppm", "status_ranges": {"deficient": [0, 0.4], "low": [0.41, 0.7], "sufficient": [0.71, 1.5], "high": [1.51, 9999]}},
            "Iron": {"min": 4.5, "max": 15.0, "unit": "ppm", "status_ranges": {"deficient": [0, 4.0], "low": [4.01, 7.0], "sufficient": [7.01, 20.0], "high": [20.01, 9999]}},
            "Zinc": {"min": 0.6, "max": 2.0, "unit": "ppm", "status_ranges": {"deficient": [0, 0.5], "low": [0.51, 0.8], "sufficient": [0.81, 2.5], "high": [2.51, 9999]}}
        },
        optimal_ph_range=[6.0, 7.5],
        kanker_ranges={
            "N": {
                "red_zone": (100, 280),     # FIXED: ICAR Red Zone (100-280 kg/ha)
                "yellow_zone": (280, 560),  # FIXED: ICAR Yellow Zone (280-560 kg/ha)
                "very_low": (0, 100),       # FIXED: Very Low Zone (<100 kg/ha)
                "excess": (560, 9999)       # FIXED: Above ICAR limits
            },
            "P": {
                "red_zone": (0, 10),        # FIXED: ICAR Red Zone (<10 kg/ha)
                "yellow_zone": (10, 25),    # FIXED: ICAR Yellow Zone (10-25 kg/ha)
                "green_zone": (25, 9999)    # FIXED: ICAR Green Zone (>25 kg/ha)
            },
            "K": {
                "red_zone": (0, 120),       # FIXED: ICAR Red Zone (<120 kg/ha)
                "yellow_zone": (120, 280),  # FIXED: ICAR Yellow Zone (120-280 kg/ha)
                "green_zone": (280, 9999)   # FIXED: ICAR Green Zone (>280 kg/ha)
            }
        },
        micronutrient_ranges={
            "Zn": {
                "deficient": (0, 0.6),
                "sufficient": (0.6, 2.0),
                "excess": (2.0, 10.0)
            },
            "B": {
                "deficient": (0.1, 0.5),
                "sufficient": (0.5, 1.2),
                "excess": (1.2, 5.0)
            },
            "Fe": {
                "low": (0, 4.5),
                "sufficient": (4.5, 15.0),
                "excess": (15.0, 50.0)
            }
        },
        ph_ranges={
            "acidic": (4.5, 5.5),
            "slightly_acidic": (5.5, 6.5),
            "optimal": (6.5, 7.5),
            "alkaline": (7.5, 8.5)
        },
        deficiency_symptoms={
            "N": "Yellowing of older leaves, stunted growth, reduced tillering, early maturity",
            "P": "Dark green/purple leaves, poor tillering, delayed maturity, weak roots",
            "K": "Brown scorching of leaf tips and margins, weak stems, lodging, poor grain filling",
            "Zn": "Interveinal chlorosis in young leaves, stunted growth, bronzing",
            "B": "Cracking of stems, poor flowering, brittle leaves",
            "Fe": "Yellow leaves with green veins, interveinal chlorosis"
        },
        growth_stages={
            "seedling": {"duration_days": 25, "nutrient_needs": "Low"},
            "tillering": {"duration_days": 20, "nutrient_needs": "High N"},
            "panicle_initiation": {"duration_days": 15, "nutrient_needs": "High N, P"},
            "flowering": {"duration_days": 10, "nutrient_needs": "High K"},
            "grain_filling": {"duration_days": 25, "nutrient_needs": "High K"}
        }
    ),
    
    "WHEAT": CropRequirement(
        crop_name="Wheat",
        optimal_npk={
            "N": {"min": 100, "max": 120, "unit": "kg/ha", "status_ranges": {"low": [0, 80], "medium": [81, 120], "high": [121, 180], "excess": [181, 9999]}},
            "P": {"min": 50, "max": 60, "unit": "kg/ha", "status_ranges": {"low": [0, 40], "medium": [41, 60], "high": [61, 100], "excess": [101, 9999]}},
            "K": {"min": 40, "max": 50, "unit": "kg/ha", "status_ranges": {"low": [0, 30], "medium": [31, 50], "high": [51, 80], "excess": [81, 9999]}},
            "Soc": {"min": 0.8, "max": 1.5, "unit": "%", "status_ranges": {"low": [0, 0.7], "medium": [0.71, 1.2], "high": [1.21, 2.0], "excess": [2.01, 9999]}}
        },
        optimal_micronutrients={
            "Boron": {"min": 0.5, "max": 1.2, "unit": "ppm", "status_ranges": {"deficient": [0, 0.4], "low": [0.41, 0.7], "sufficient": [0.71, 1.5], "high": [1.51, 9999]}},
            "Iron": {"min": 4.5, "max": 15.0, "unit": "ppm", "status_ranges": {"deficient": [0, 4.0], "low": [4.01, 7.0], "sufficient": [7.01, 20.0], "high": [20.01, 9999]}},
            "Zinc": {"min": 0.6, "max": 2.0, "unit": "ppm", "status_ranges": {"deficient": [0, 0.5], "low": [0.51, 0.8], "sufficient": [0.81, 2.5], "high": [2.51, 9999]}}
        },
        optimal_ph_range=[6.0, 7.5],
        kanker_ranges={
            "N": {
                "low": (0, 250),
                "medium": (250, 400),
                "high": (400, 550),
                "very_high": (550, 900)
            },
            "P": {
                "low": (0, 12),
                "medium": (12, 28),
                "high": (28, 55)
            },
            "K": {
                "low": (0, 100),
                "medium": (100, 250),
                "high": (250, 380)
            }
        },
        micronutrient_ranges={
            "Zn": {
                "deficient": (0, 0.5),
                "sufficient": (0.5, 1.5),
                "excess": (1.5, 8.0)
            },
            "B": {
                "deficient": (0.2, 0.4),
                "sufficient": (0.4, 1.0),
                "excess": (1.0, 4.0)
            },
            "Fe": {
                "deficient": (0, 3.0),
                "sufficient": (3.0, 12.0),
                "excess": (12.0, 40.0)
            }
        },
        ph_ranges={
            "acidic": (5.0, 6.0),
            "optimal": (6.0, 7.5),
            "alkaline": (7.5, 8.5)
        },
        deficiency_symptoms={
            "N": "Yellowing of older leaves, reduced tillering, small spikes",
            "P": "Purple coloration, poor root development, delayed maturity",
            "K": "Brown leaf margins, weak stems, poor grain quality",
            "Zn": "Interveinal chlorosis, stunted growth, small leaves",
            "B": "Hollow stem, poor grain set, brittle leaves",
            "Fe": "Yellow leaves with green veins, stunted growth"
        },
        growth_stages={
            "germination": {"duration_days": 7, "nutrient_needs": "Low"},
            "crown_root_initiation": {"duration_days": 25, "nutrient_needs": "High N"},
            "tillering": {"duration_days": 20, "nutrient_needs": "High N"},
            "stem_elongation": {"duration_days": 15, "nutrient_needs": "High N, P"},
            "flowering": {"duration_days": 10, "nutrient_needs": "High K"},
            "grain_filling": {"duration_days": 30, "nutrient_needs": "High K"}
        }
    ),
    
    "MAIZE": CropRequirement(
        crop_name="Maize",
        optimal_npk={
            "N": {"min": 120, "max": 150, "unit": "kg/ha"},
            "P": {"min": 60, "max": 80, "unit": "kg/ha"},
            "K": {"min": 60, "max": 80, "unit": "kg/ha"}
        },
        kanker_ranges={
            "N": {
                "low": (0, 200),
                "medium": (200, 350),
                "high": (350, 500),
                "very_high": (500, 700)
            },
            "P": {
                "low": (0, 15),
                "medium": (15, 30),
                "high": (30, 50)
            },
            "K": {
                "low": (0, 150),
                "medium": (150, 250),
                "high": (250, 350)
            }
        },
        micronutrient_ranges={
            "Zn": {
                "deficient": (0, 0.7),
                "sufficient": (0.7, 2.5),
                "excess": (2.5, 12.0)
            },
            "B": {
                "deficient": (0.1, 0.6),
                "sufficient": (0.6, 1.5),
                "excess": (1.5, 6.0)
            },
            "Fe": {
                "low": (0, 5.0),
                "sufficient": (5.0, 18.0),
                "excess": (18.0, 60.0)
            }
        },
        ph_ranges={
            "acidic": (5.0, 6.0),
            "optimal": (6.0, 7.0),
            "alkaline": (7.0, 8.5)
        },
        deficiency_symptoms={
            "N": "Yellowing of older leaves, stunted growth, small ears",
            "P": "Purple leaves, poor root development, delayed maturity",
            "K": "Brown leaf margins, weak stalks, poor grain filling",
            "Zn": "Interveinal chlorosis, stunted growth, white bands on leaves",
            "B": "Hollow stems, poor kernel development",
            "Fe": "Yellow leaves with green veins, stunted growth"
        },
        growth_stages={
            "germination": {"duration_days": 7, "nutrient_needs": "Low"},
            "vegetative": {"duration_days": 35, "nutrient_needs": "High N"},
            "tasseling": {"duration_days": 15, "nutrient_needs": "High N, P"},
            "silking": {"duration_days": 10, "nutrient_needs": "High K"},
            "grain_filling": {"duration_days": 40, "nutrient_needs": "High K"}
        }
    ),
    
    "COTTON": CropRequirement(
        crop_name="Cotton",
        optimal_npk={
            "N": {"min": 80, "max": 100, "unit": "kg/ha"},
            "P": {"min": 40, "max": 50, "unit": "kg/ha"},
            "K": {"min": 50, "max": 60, "unit": "kg/ha"}
        },
        kanker_ranges={
            "N": {
                "low": (0, 150),
                "medium": (150, 300),
                "high": (300, 450),
                "very_high": (450, 600)
            },
            "P": {
                "low": (0, 10),
                "medium": (10, 20),
                "high": (20, 35)
            },
            "K": {
                "low": (0, 100),
                "medium": (100, 200),
                "high": (200, 300)
            }
        },
        micronutrient_ranges={
            "Zn": {
                "deficient": (0, 0.5),
                "sufficient": (0.5, 2.0),
                "excess": (2.0, 10.0)
            },
            "B": {
                "deficient": (0.1, 0.4),
                "sufficient": (0.4, 1.0),
                "excess": (1.0, 4.0)
            },
            "Fe": {
                "low": (0, 3.0),
                "sufficient": (3.0, 10.0),
                "excess": (10.0, 30.0)
            }
        },
        ph_ranges={
            "acidic": (5.5, 6.0),
            "optimal": (6.0, 7.5),
            "alkaline": (7.5, 8.5)
        },
        deficiency_symptoms={
            "N": "Yellowing of older leaves, reduced boll formation",
            "P": "Purple leaves, poor root development, small bolls",
            "K": "Brown leaf margins, weak stems, poor fiber quality",
            "Zn": "Interveinal chlorosis, stunted growth, small leaves",
            "B": "Hollow stems, poor boll development",
            "Fe": "Yellow leaves with green veins, stunted growth"
        },
        growth_stages={
            "germination": {"duration_days": 7, "nutrient_needs": "Low"},
            "vegetative": {"duration_days": 45, "nutrient_needs": "High N"},
            "flowering": {"duration_days": 30, "nutrient_needs": "High N, P"},
            "boll_development": {"duration_days": 40, "nutrient_needs": "High K"},
            "maturity": {"duration_days": 30, "nutrient_needs": "Low"}
        }
    ),
    
    "SOYBEAN": CropRequirement(
        crop_name="Soybean",
        optimal_npk={
            "N": {"min": 20, "max": 30, "unit": "kg/ha"},  # Soybean fixes N
            "P": {"min": 50, "max": 60, "unit": "kg/ha"},
            "K": {"min": 40, "max": 50, "unit": "kg/ha"}
        },
        kanker_ranges={
            "N": {
                "low": (0, 100),
                "medium": (100, 200),
                "high": (200, 350),
                "very_high": (350, 500)
            },
            "P": {
                "low": (0, 15),
                "medium": (15, 25),
                "high": (25, 40)
            },
            "K": {
                "low": (0, 120),
                "medium": (120, 200),
                "high": (200, 300)
            }
        },
        micronutrient_ranges={
            "Zn": {
                "deficient": (0, 0.6),
                "sufficient": (0.6, 2.0),
                "excess": (2.0, 8.0)
            },
            "B": {
                "deficient": (0.1, 0.5),
                "sufficient": (0.5, 1.2),
                "excess": (1.2, 4.0)
            },
            "Fe": {
                "low": (0, 4.0),
                "sufficient": (4.0, 15.0),
                "excess": (15.0, 50.0)
            }
        },
        ph_ranges={
            "acidic": (5.5, 6.0),
            "optimal": (6.0, 7.0),
            "alkaline": (7.0, 8.0)
        },
        deficiency_symptoms={
            "N": "Yellowing of older leaves, poor nodulation",
            "P": "Purple leaves, poor root development, small pods",
            "K": "Brown leaf margins, weak stems, poor seed filling",
            "Zn": "Interveinal chlorosis, stunted growth",
            "B": "Hollow stems, poor pod development",
            "Fe": "Yellow leaves with green veins, stunted growth"
        },
        growth_stages={
            "germination": {"duration_days": 7, "nutrient_needs": "Low"},
            "vegetative": {"duration_days": 30, "nutrient_needs": "High P"},
            "flowering": {"duration_days": 20, "nutrient_needs": "High P, K"},
            "pod_development": {"duration_days": 25, "nutrient_needs": "High K"},
            "seed_filling": {"duration_days": 20, "nutrient_needs": "High K"}
        }
    )
}

# Add aliases for common crop names
KANKER_CROP_REQUIREMENTS["PADDY"] = KANKER_CROP_REQUIREMENTS["RICE"]
KANKER_CROP_REQUIREMENTS["PADDY"].crop_name = "Paddy"

# Rajnandgaon District - Khairagarh Tehsil ICAR Data (2024-25)
RAJNANDGAON_KHAIRAGARH_ZONES = {
    "nitrogen_zones": {
        "red_zone": {
            "description": "Low Nitrogen Zone (ICAR <280 kg/ha)",
            "nitrogen_range": (0, 280),
            "area_hectares": 791980.0,
            "area_percentage": 98.25,
            "characteristics": "Low nitrogen levels, high nitrogen application needed",
            "recommendation": "Apply nitrogen fertilizers at higher rates for optimal crop growth"
        },
        "yellow_zone": {
            "description": "Medium Nitrogen Zone (ICAR 280-560 kg/ha)",
            "nitrogen_range": (280, 560),
            "area_hectares": 14093.53,
            "area_percentage": 1.75,
            "characteristics": "Medium nitrogen levels, balanced fertilization needed",
            "recommendation": "Apply nitrogen based on crop requirement and soil test"
        }
    },
    "phosphorus_zones": {
        "red_zone": {
            "description": "Low Phosphorus Zone (ICAR <10 kg/ha)",
            "phosphorus_range": (0, 10),
            "area_hectares": 155984.06,
            "area_percentage": 19.35,
            "characteristics": "Low phosphorus levels, high phosphorus application needed",
            "recommendation": "Apply DAP or SSP at higher rates for optimal crop growth"
        },
        "yellow_zone": {
            "description": "Medium Phosphorus Zone (ICAR 10-25 kg/ha)",
            "phosphorus_range": (10, 25),
            "area_hectares": 649231.44,
            "area_percentage": 80.55,
            "characteristics": "Medium phosphorus levels, balanced fertilization needed",
            "recommendation": "Apply phosphorus based on crop requirement and soil test"
        },
        "green_zone": {
            "description": "High Phosphorus Zone (ICAR >25 kg/ha)",
            "phosphorus_range": (25, 9999),
            "area_hectares": 738.36,
            "area_percentage": 0.09,
            "characteristics": "High phosphorus levels, low phosphorus application needed",
            "recommendation": "Apply phosphorus at lower rates or skip if sufficient"
        }
    },
    "potassium_zones": {
        "yellow_zone": {
            "description": "Medium Potassium Zone (ICAR 120-280 kg/ha)",
            "potassium_range": (120, 280),
            "area_hectares": 131605.84,
            "area_percentage": 16.33,
            "characteristics": "Medium potassium levels, balanced fertilization needed",
            "recommendation": "Apply potassium based on crop requirement and soil test"
        },
        "green_zone": {
            "description": "High Potassium Zone (ICAR >280 kg/ha)",
            "potassium_range": (280, 9999),
            "area_hectares": 674362.74,
            "area_percentage": 83.67,
            "characteristics": "High potassium levels, low potassium application needed",
            "recommendation": "Apply potassium at lower rates or skip if sufficient"
        }
    }
}

# Kanker Zone Information (Based on ICAR 2024-25 data - FIXED)
KANKER_ZONES = {
    "nitrogen_zones": {
        "red_zone": {
            "description": "Low Nitrogen Zone (ICAR 100-280 kg/ha)",
            "nitrogen_range": (100, 280),
            "villages_count": 46,  # 50.55% of total villages (46 out of 91)
            "characteristics": "Low nitrogen levels, high nitrogen application needed",
            "recommendation": "Apply nitrogen fertilizers at higher rates for optimal crop growth"
        },
        "yellow_zone": {
            "description": "Medium Nitrogen Zone (ICAR 280-560 kg/ha)",
            "nitrogen_range": (280, 560),
            "villages_count": 45,  # 49.45% of total villages (45 out of 91)
            "characteristics": "Medium nitrogen levels, balanced fertilization needed",
            "recommendation": "Apply nitrogen based on crop requirement and soil test"
        }
    },
    "phosphorus_zones": {
        "red_zone": {
            "description": "Low Phosphorus Zone (ICAR <10 kg/ha)",
            "phosphorus_range": (0, 10),
            "villages_count": 60,
            "characteristics": "Low phosphorus levels, high phosphorus application needed",
            "recommendation": "Apply DAP or SSP at higher rates for optimal crop growth"
        },
        "yellow_zone": {
            "description": "Medium Phosphorus Zone (ICAR 10-25 kg/ha)",
            "phosphorus_range": (10, 25),
            "villages_count": 25,
            "characteristics": "Medium phosphorus levels, balanced fertilization needed",
            "recommendation": "Apply phosphorus based on crop requirement and soil test"
        },
        "green_zone": {
            "description": "High Phosphorus Zone (ICAR >25 kg/ha)",
            "phosphorus_range": (25, 9999),
            "villages_count": 6,
            "characteristics": "High phosphorus levels, low phosphorus application needed",
            "recommendation": "Apply phosphorus at lower rates or skip if sufficient"
        }
    },
    "potassium_zones": {
        "red_zone": {
            "description": "Low Potassium Zone (ICAR <120 kg/ha)",
            "potassium_range": (0, 120),
            "villages_count": 35,
            "characteristics": "Low potassium levels, high potassium application needed",
            "recommendation": "Apply MOP at higher rates for optimal crop growth"
        },
        "yellow_zone": {
            "description": "Medium Potassium Zone (ICAR 120-280 kg/ha)",
            "potassium_range": (120, 280),
            "villages_count": 40,
            "characteristics": "Medium potassium levels, balanced fertilization needed",
            "recommendation": "Apply potassium based on crop requirement and soil test"
        },
        "green_zone": {
            "description": "High Potassium Zone (ICAR >280 kg/ha)",
            "potassium_range": (280, 9999),
            "villages_count": 16,
            "characteristics": "High potassium levels, low potassium application needed",
            "recommendation": "Apply potassium at lower rates or skip if sufficient"
        }
    }
}

# Micronutrient Status in Kanker (Based on 91 villages analysis)
KANKER_MICRONUTRIENT_STATUS = {
    "zinc": {
        "deficient_villages": 73,  # 80% of villages
        "deficient_range": (0, 0.6),
        "sufficient_range": (0.6, 2.0),
        "recommendation": "Apply Zinc Sulfate 25-50 kg/ha",
        "priority": "HIGH"
    },
    "boron": {
        "deficient_villages": 77,  # 85% of villages
        "deficient_range": (0.1, 0.5),
        "sufficient_range": (0.5, 1.2),
        "recommendation": "Apply Borax 5-15 kg/ha",
        "priority": "HIGH"
    },
    "iron": {
        "deficient_villages": 45,  # 50% of villages
        "deficient_range": (0, 4.5),
        "sufficient_range": (4.5, 15.0),
        "recommendation": "Apply Ferrous Sulfate 25-75 kg/ha",
        "priority": "MEDIUM"
    }
}

# pH Status in Kanker
KANKER_PH_STATUS = {
    "acidic_soils": {
        "villages_count": 25,
        "ph_range": (4.5, 6.0),
        "recommendation": "Apply lime 2-4 t/ha",
        "priority": "HIGH"
    },
    "slightly_acidic": {
        "villages_count": 40,
        "ph_range": (6.0, 6.5),
        "recommendation": "Apply lime 1-2 t/ha",
        "priority": "MEDIUM"
    },
    "optimal_ph": {
        "villages_count": 20,
        "ph_range": (6.5, 7.5),
        "recommendation": "No lime needed",
        "priority": "LOW"
    },
    "alkaline_soils": {
        "villages_count": 6,
        "ph_range": (7.5, 8.5),
        "recommendation": "Use acidifying fertilizers",
        "priority": "MEDIUM"
    }
}

# Helper Functions
def get_crop_requirement(crop_name: str) -> CropRequirement:
    """Get crop requirement for specific crop"""
    crop_key = crop_name.upper()
    if crop_key in KANKER_CROP_REQUIREMENTS:
        return KANKER_CROP_REQUIREMENTS[crop_key]
    else:
        # Default to rice if crop not found
        return KANKER_CROP_REQUIREMENTS["RICE"]

def get_nutrient_status_level(nutrient_value: float, nutrient_type: str, crop_type: str) -> str:
    """Determines the status level (low, medium, high, excess) for a given nutrient value."""
    crop_req = get_crop_requirement(crop_type)
    if not crop_req:
        return "unknown"

    if nutrient_type in ['N', 'P', 'K', 'Soc']:
        if nutrient_type not in crop_req.optimal_npk:
            return "unknown"
        if 'status_ranges' not in crop_req.optimal_npk[nutrient_type]:
            return "unknown"
        ranges = crop_req.optimal_npk[nutrient_type]['status_ranges']
    elif nutrient_type in ['Boron', 'Iron', 'Zinc']:
        # Map nutrient names to micronutrient_ranges keys
        nutrient_map = {'Boron': 'B', 'Iron': 'Fe', 'Zinc': 'Zn'}
        micronutrient_key = nutrient_map.get(nutrient_type)
        
        if not crop_req.micronutrient_ranges or not micronutrient_key:
            return "sufficient"  # Default fallback
        if micronutrient_key not in crop_req.micronutrient_ranges:
            return "sufficient"  # Default fallback
        
        ranges = crop_req.micronutrient_ranges[micronutrient_key]
    else:
        return "unknown"

    for status, (min_val, max_val) in ranges.items():
        if min_val <= nutrient_value <= max_val:
            return status
    return "unknown"

def get_ph_status_level(ph_value: float, crop_type: str) -> str:
    """Determines the pH status level (acidic, normal, alkaline) for a given pH value."""
    crop_req = get_crop_requirement(crop_type)
    if not crop_req:
        return "unknown"

    optimal_min, optimal_max = crop_req.optimal_ph_range

    if ph_value < optimal_min - 1.0:
        return "very_acidic"
    elif ph_value < optimal_min:
        return "acidic"
    elif optimal_min <= ph_value <= optimal_max:
        return "normal"
    elif ph_value > optimal_max + 1.0:
        return "very_alkaline"
    elif ph_value > optimal_max:
        return "alkaline"
    return "unknown"

def classify_nutrient_status(value: float, nutrient: str, crop_name: str) -> Dict[str, Any]:
    """Classify nutrient status based on Kanker ranges with ICAR compliance"""
    crop_req = get_crop_requirement(crop_name)
    
    if nutrient.upper() not in ["N", "P", "K"]:
        return {"status": "unknown", "description": "Invalid nutrient"}
    
    nutrient_key = nutrient.upper()
    ranges = crop_req.kanker_ranges.get(nutrient_key, {})
    
    status = "unknown"
    description = "Status not determined"
    
    # FIXED: Special handling for Nitrogen with CORRECT ICAR compliance
    if nutrient_key == "N":
        if 100 <= value < 280:
            status = "red_zone"
            description = "Red Zone (ICAR 100-280 kg/ha) - Low nitrogen levels, high N application needed"
        elif 280 <= value < 560:
            status = "yellow_zone"
            description = "Yellow Zone (ICAR 280-560 kg/ha) - Medium nitrogen levels, balanced fertilization"
        elif value < 100:
            status = "very_low"
            description = "Very Low Zone (<100 kg/ha) - Critical nitrogen deficiency, immediate application needed"
        else:
            status = "excess"
            description = "Above ICAR limits (>560 kg/ha) - Excess nitrogen, reduce application"
    elif nutrient_key == "P":
        # FIXED: Special handling for Phosphorus with CORRECT ICAR compliance
        if 0 <= value < 10:
            status = "red_zone"
            description = "Red Zone (ICAR <10 kg/ha) - Low phosphorus levels, high P application needed"
        elif 10 <= value < 25:
            status = "yellow_zone"
            description = "Yellow Zone (ICAR 10-25 kg/ha) - Medium phosphorus levels, balanced fertilization"
        elif value >= 25:
            status = "green_zone"
            description = "Green Zone (ICAR >25 kg/ha) - High phosphorus levels, low P application needed"
        else:
            status = "unknown"
            description = "Invalid phosphorus value"
    elif nutrient_key == "K":
        # FIXED: Special handling for Potassium with CORRECT ICAR compliance
        if 0 <= value < 120:
            status = "red_zone"
            description = "Red Zone (ICAR <120 kg/ha) - Low potassium levels, high K application needed"
        elif 120 <= value < 280:
            status = "yellow_zone"
            description = "Yellow Zone (ICAR 120-280 kg/ha) - Medium potassium levels, balanced fertilization"
        elif value >= 280:
            status = "green_zone"
            description = "Green Zone (ICAR >280 kg/ha) - High potassium levels, low K application needed"
        else:
            status = "unknown"
            description = "Invalid potassium value"
    else:
        # For other nutrients, use existing logic
        for level, (min_val, max_val) in ranges.items():
            if min_val <= value < max_val:
                status = level
                description = f"{level.replace('_', ' ').title()} {nutrient_key} level"
                break
    
    return {
        "status": status,
        "description": description,
        "value": value,
        "range": ranges.get(status, (0, 0))
    }

def get_micronutrient_recommendation(micronutrient: str, value: float) -> Dict[str, Any]:
    """Get micronutrient recommendation based on Kanker data"""
    micronutrient_lower = micronutrient.lower()
    
    if micronutrient_lower not in KANKER_MICRONUTRIENT_STATUS:
        return {"recommendation": "No specific recommendation available"}
    
    micronutrient_data = KANKER_MICRONUTRIENT_STATUS[micronutrient_lower]
    
    if value < micronutrient_data["deficient_range"][1]:
        return {
            "status": "deficient",
            "recommendation": micronutrient_data["recommendation"],
            "priority": micronutrient_data["priority"],
            "villages_affected": micronutrient_data["deficient_villages"]
        }
    elif value < micronutrient_data["sufficient_range"][1]:
        return {
            "status": "sufficient",
            "recommendation": "No application needed",
            "priority": "LOW"
        }
    else:
        return {
            "status": "excess",
            "recommendation": "Reduce application",
            "priority": "MEDIUM"
        }

def get_ph_recommendation(ph_value: float) -> Dict[str, Any]:
    """Get pH recommendation based on Kanker data"""
    for ph_category, data in KANKER_PH_STATUS.items():
        if data["ph_range"][0] <= ph_value < data["ph_range"][1]:
            return {
                "status": ph_category,
                "recommendation": data["recommendation"],
                "priority": data["priority"],
                "villages_count": data["villages_count"]
            }
    
    return {
        "status": "unknown",
        "recommendation": "Soil test recommended",
        "priority": "MEDIUM"
    }

# Export main data structures
__all__ = [
    "KANKER_CROP_REQUIREMENTS",
    "KANKER_ZONES", 
    "RAJNANDGAON_KHAIRAGARH_ZONES",
    "KANKER_MICRONUTRIENT_STATUS",
    "KANKER_PH_STATUS",
    "get_crop_requirement",
    "classify_nutrient_status",
    "get_micronutrient_recommendation",
    "get_ph_recommendation"
]
