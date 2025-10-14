"""
ICAR-Only Analysis Module
Generates NPK analysis using only ICAR data when no satellite data is available
This serves as the last resort fallback in the multi-satellite system
"""

import logging
import math
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np

# Import existing modules
from .kanker_data_loader import kanker_loader
from .recommendation_engine_kanker import generate_kanker_based_recommendations
from .npk_config import get_npk_coefficients, detect_region_from_coordinates, get_crop_type_from_string, Region, CropType

logger = logging.getLogger(__name__)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_villages(coordinates: Tuple[float, float], max_distance_km: float = 50.0) -> list:
    """
    Find nearest villages within specified distance from coordinates
    
    Args:
        coordinates: (latitude, longitude)
        max_distance_km: Maximum distance to search for villages
    
    Returns:
        List of village data sorted by distance
    """
    if not kanker_loader.is_data_loaded():
        logger.error("Kanker data not loaded")
        return []
    
    lat, lon = coordinates
    villages = []
    
    for village_data in kanker_loader.data.get('villages', []):
        village_lat = village_data.get('latitude', 0)
        village_lon = village_data.get('longitude', 0)
        
        if village_lat == 0 or village_lon == 0:
            continue
            
        distance = calculate_distance(lat, lon, village_lat, village_lon)
        
        if distance <= max_distance_km:
            village_data['distance_km'] = distance
            villages.append(village_data)
    
    # Sort by distance
    villages.sort(key=lambda x: x['distance_km'])
    return villages

def calculate_weighted_average_npk(villages: list, max_villages: int = 5) -> Dict[str, float]:
    """
    Calculate weighted average NPK values from nearest villages
    
    Args:
        villages: List of village data with distance
        max_villages: Maximum number of villages to consider
    
    Returns:
        Dictionary with average NPK values
    """
    if not villages:
        # Return default values if no villages found
        return {
            'Nitrogen': 200.0,  # kg/ha
            'Phosphorus': 25.0,  # kg/ha
            'Potassium': 150.0,  # kg/ha
            'Soc': 1.5  # %
        }
    
    # Take closest villages (up to max_villages)
    selected_villages = villages[:max_villages]
    
    # Calculate weights (inverse distance)
    weights = []
    for village in selected_villages:
        distance = village['distance_km']
        # Avoid division by zero, minimum weight for very close villages
        weight = 1.0 / max(distance, 0.1)
        weights.append(weight)
    
    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    
    # Calculate weighted averages
    npk_values = {
        'Nitrogen': 0.0,
        'Phosphorus': 0.0,
        'Potassium': 0.0,
        'Soc': 0.0
    }
    
    for i, village in enumerate(selected_villages):
        weight = weights[i]
        
        # Get NPK values from village data
        village_npk = village.get('npk', {})
        
        npk_values['Nitrogen'] += village_npk.get('nitrogen', 200.0) * weight
        npk_values['Phosphorus'] += village_npk.get('phosphorus', 25.0) * weight
        npk_values['Potassium'] += village_npk.get('potassium', 150.0) * weight
        npk_values['Soc'] += village_npk.get('soc', 1.5) * weight
    
    return npk_values

def generate_vegetation_indices_from_icar(npk_values: Dict[str, float]) -> Dict[str, Any]:
    """
    Generate synthetic vegetation indices based on ICAR NPK values
    This provides compatibility with satellite-based response format
    
    Args:
        npk_values: NPK values from ICAR data
    
    Returns:
        Dictionary with synthetic vegetation indices
    """
    # Use NPK values to estimate vegetation health
    nitrogen = npk_values.get('Nitrogen', 200.0)
    phosphorus = npk_values.get('Phosphorus', 25.0)
    potassium = npk_values.get('Potassium', 150.0)
    soc = npk_values.get('Soc', 1.5)
    
    # Estimate NDVI based on nitrogen and SOC
    # Higher nitrogen and SOC typically indicate better vegetation
    ndvi_estimate = min(0.8, max(0.1, (nitrogen / 300.0) * 0.6 + (soc / 2.0) * 0.4))
    
    # Estimate NDMI based on SOC (organic matter content)
    ndmi_estimate = min(0.6, max(-0.2, (soc / 2.0) * 0.8 - 0.1))
    
    # Estimate SAVI (similar to NDVI but soil-adjusted)
    savi_estimate = ndvi_estimate * 0.9
    
    # Estimate NDWI based on potassium (water retention)
    ndwi_estimate = min(0.4, max(-0.3, (potassium / 200.0) * 0.5 - 0.2))
    
    return {
        "NDVI": {
            "mean": round(ndvi_estimate, 4),
            "median": round(ndvi_estimate, 4),
            "count": 1,
            "interpretation": "healthy_vegetation" if ndvi_estimate > 0.5 else "sparse_vegetation",
            "status": "healthy" if ndvi_estimate > 0.5 else "needs_attention"
        },
        "NDMI": {
            "mean": round(ndmi_estimate, 4),
            "median": round(ndmi_estimate, 4),
            "count": 1,
            "interpretation": "adequate_moisture" if ndmi_estimate > 0.2 else "low_moisture_or_dry_soil",
            "status": "adequate" if ndmi_estimate > 0.2 else "needs_irrigation"
        },
        "SAVI": {
            "mean": round(savi_estimate, 4),
            "median": round(savi_estimate, 4),
            "count": 1
        },
        "NDWI": {
            "mean": round(ndwi_estimate, 4),
            "median": round(ndwi_estimate, 4),
            "count": 1
        }
    }

def generate_icar_only_analysis(coordinates: Tuple[float, float], 
                               crop_type: str = "GENERIC", 
                               field_area_ha: float = 1.0,
                               analysis_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Generate complete NPK analysis using only ICAR data
    
    Args:
        coordinates: (latitude, longitude)
        crop_type: Type of crop
        field_area_ha: Field area in hectares
        analysis_date: Date of analysis (optional)
    
    Returns:
        Complete analysis response matching satellite format
    """
    try:
        lat, lon = coordinates
        
        # Find nearest villages
        villages = find_nearest_villages(coordinates)
        
        if not villages:
            logger.warning(f"No ICAR villages found near coordinates {coordinates}")
            # Use default values
            npk_values = {
                'Nitrogen': 200.0,
                'Phosphorus': 25.0,
                'Potassium': 150.0,
                'Soc': 1.5
            }
            nearest_village = None
            confidence_score = 0.3
        else:
            # Calculate weighted average NPK
            npk_values = calculate_weighted_average_npk(villages)
            nearest_village = villages[0]
            confidence_score = min(0.85, 0.5 + (1.0 / max(villages[0]['distance_km'], 0.1)) * 0.35)
        
        # Generate synthetic vegetation indices
        indices = generate_vegetation_indices_from_icar(npk_values)
        
        # Generate recommendations
        try:
            recommendations = generate_kanker_based_recommendations(
                npk_data=npk_values,
                enhanced_details={},
                crop_type=crop_type,
                coordinates=coordinates,
                field_area_ha=field_area_ha
            )
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = {
                "error": f"Failed to generate recommendations: {str(e)}",
                "dataSource": "ICAR 2024-25 Data Only",
                "fallback": True
            }
        
        # Detect region and crop type
        region = detect_region_from_coordinates(lat, lon)
        crop_enum = get_crop_type_from_string(crop_type)
        
        # Prepare response
        response = {
            "success": True,
            "dataSource": "ICAR 2024-25 Data Only",
            "satelliteSource": "ICAR-Only",
            "fallbackLevel": 4,
            "dataQuality": "basic",
            "confidenceScore": confidence_score,
            "fallbackReason": "No satellite data available, using ICAR village data",
            "region": region.value,
            "cropType": crop_enum.value,
            "analysisDate": analysis_date.isoformat() if analysis_date else datetime.now().isoformat(),
            "nearestVillage": nearest_village.get('village_name', 'Unknown') if nearest_village else None,
            "villageDistance": round(nearest_village['distance_km'], 2) if nearest_village else None,
            "villagesUsed": len(villages),
            "vegetationIndices": indices,
            "soilNutrients": npk_values,
            "recommendations": recommendations,
            "fieldArea": {
                "hectares": round(field_area_ha, 3),
                "acres": round(field_area_ha / 0.404686, 3)
            },
            "data": {
                "indices": indices,
                "npk": npk_values,
                "enhanced_details": {
                    "data_source": "icar_only",
                    "villages_analyzed": len(villages),
                    "weighted_average": True,
                    "synthetic_indices": True
                },
                "icar_enhanced": True
            },
            "indices": indices,  # Also include at root level for compatibility
            "npk": npk_values,  # Also include at root level for compatibility
            "icar_enhanced": True,
            "enhanced_details": {
                "data_source": "icar_only",
                "villages_analyzed": len(villages),
                "weighted_average": True,
                "synthetic_indices": True
            },
            "metadata": {
                "provider": "ICAR 2024-25 Data Only",
                "satellite": "ICAR-Only",
                "resolution": "village-level",
                "region": region.value,
                "cropType": crop_enum.value,
                "confidenceScore": confidence_score,
                "dataQuality": "basic",
                "fallbackLevel": 4,
                "satelliteSource": "ICAR-Only",
                "fallbackReason": "No satellite data available",
                "nearestVillage": nearest_village.get('village_name', 'Unknown') if nearest_village else None,
                "villageDistance": round(nearest_village['distance_km'], 2) if nearest_village else None,
                "villagesUsed": len(villages),
                "processed_at": datetime.utcnow().isoformat(),
                "dataSource": "ICAR 2024-25 Data Only"
            }
        }
        
        logger.info(f"✅ ICAR-only analysis generated successfully for {coordinates}")
        logger.info(f"   Nearest village: {nearest_village.get('village_name', 'Unknown') if nearest_village else 'None'}")
        logger.info(f"   Distance: {nearest_village['distance_km']:.2f} km" if nearest_village else "N/A")
        logger.info(f"   Villages used: {len(villages)}")
        logger.info(f"   Confidence: {confidence_score:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in ICAR-only analysis: {e}")
        return {
            "success": False,
            "error": f"ICAR-only analysis failed: {str(e)}",
            "dataSource": "ICAR 2024-25 Data Only",
            "fallbackLevel": 4,
            "satelliteSource": "ICAR-Only"
        }
