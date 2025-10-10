# modis_indices.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pystac_client
import planetary_computer as pc
import rioxarray
import xarray as xr
from concurrent.futures import ThreadPoolExecutor, as_completed
from .npk_config import (
    get_npk_coefficients, 
    detect_region_from_coordinates, 
    get_crop_type_from_string,
    Region, 
    CropType
)

logger = logging.getLogger("modis_indices")
logger.setLevel(logging.WARNING)

# MODIS-specific thresholds
MODIS_THRESHOLDS = {
    "NDVI": { "low": 0.3, "medium": 0.55 },
    "NDMI": { "low": 0.15, "medium": 0.4 },
    "SAVI": { "low": 0.2, "medium": 0.5 },
    "NDWI": { "low": 0.0, "medium": 0.2 }
}

def open_signed_raster(url: str):
    """Open a rasterio-supported file via planetary_computer signed URL"""
    signed = pc.sign(url)
    return rioxarray.open_rasterio(signed, masked=True)

def safe_mean(arr: np.ndarray) -> float:
    """Return mean ignoring nan and extreme values"""
    if arr is None or len(arr) == 0:
        return float("nan")
    arr = arr.astype(np.float64)
    mask = np.isfinite(arr)
    if not np.any(mask):
        return float("nan")
    q1, q99 = np.nanpercentile(arr[mask], [1, 99])
    arr_clipped = np.clip(arr, q1, q99)
    return float(np.nanmean(arr_clipped[mask]))

def compute_modis_indices(red: np.ndarray, nir: np.ndarray, swir1: np.ndarray, swir2: np.ndarray, blue: np.ndarray) -> Dict[str, float]:
    """Compute vegetation indices for MODIS data"""
    indices = {}
    
    # NDVI (Normalized Difference Vegetation Index)
    ndvi = (nir - red) / (nir + red + 1e-8)
    indices["NDVI"] = {
        "mean": safe_mean(ndvi),
        "median": float(np.nanmedian(ndvi)),
        "count": int(np.sum(np.isfinite(ndvi))),
        "interpretation": "healthy_vegetation" if safe_mean(ndvi) > 0.5 else "sparse_vegetation",
        "status": "healthy" if safe_mean(ndvi) > 0.5 else "needs_attention"
    }
    
    # NDMI (Normalized Difference Moisture Index)
    ndmi = (nir - swir1) / (nir + swir1 + 1e-8)
    indices["NDMI"] = {
        "mean": safe_mean(ndmi),
        "median": float(np.nanmedian(ndmi)),
        "count": int(np.sum(np.isfinite(ndmi))),
        "interpretation": "adequate_moisture" if safe_mean(ndmi) > 0.2 else "low_moisture_or_dry_soil",
        "status": "adequate" if safe_mean(ndmi) > 0.2 else "needs_irrigation"
    }
    
    # SAVI (Soil Adjusted Vegetation Index)
    savi = ((nir - red) / (nir + red + 0.5)) * 1.5
    indices["SAVI"] = {
        "mean": safe_mean(savi),
        "median": float(np.nanmedian(savi)),
        "count": int(np.sum(np.isfinite(savi)))
    }
    
    # NDWI (Normalized Difference Water Index)
    ndwi = (nir - swir1) / (nir + swir1 + 1e-8)
    indices["NDWI"] = {
        "mean": safe_mean(ndwi),
        "median": float(np.nanmedian(ndwi)),
        "count": int(np.sum(np.isfinite(ndwi)))
    }
    
    return indices

def estimate_npk_from_modis_indices(indices: Dict[str, Any], 
                                   region: Region = Region.GLOBAL,
                                   crop_type: CropType = CropType.GENERIC) -> Dict[str, float]:
    """Estimate NPK values from MODIS vegetation indices using dynamic coefficients"""
    ndvi = indices["NDVI"]["mean"]
    ndmi = indices["NDMI"]["mean"]
    savi = indices["SAVI"]["mean"]
    
    # Get dynamic coefficients
    coeffs = get_npk_coefficients(region, crop_type)
    
    # MODIS-specific NPK estimation with dynamic coefficients
    # These are calibrated for MODIS's 250m resolution and different spectral bands
    
    # Nitrogen estimation (MODIS calibration with dynamic coefficients)
    nitrogen = coeffs.nitrogen_base + (ndvi * coeffs.nitrogen_ndvi * 0.4) + (savi * coeffs.nitrogen_savi * 0.6)
    nitrogen = max(coeffs.nitrogen_min * 0.2, min(coeffs.nitrogen_max * 0.3, nitrogen))  # Adjusted for MODIS resolution
    
    # Phosphorus estimation (MODIS calibration with dynamic coefficients)
    phosphorus = coeffs.phosphorus_base + (ndvi * coeffs.phosphorus_ndvi * 0.5) + (ndmi * coeffs.phosphorus_ndwi * 0.4)
    phosphorus = max(coeffs.phosphorus_min * 0.1, min(coeffs.phosphorus_max * 0.3, phosphorus))  # Adjusted for MODIS resolution
    
    # Potassium estimation (MODIS calibration with dynamic coefficients)
    potassium = coeffs.potassium_base + (ndvi * coeffs.potassium_ndvi * 0.5) + (savi * coeffs.potassium_savi * 0.4)
    potassium = max(coeffs.potassium_min * 0.2, min(coeffs.potassium_max * 0.4, potassium))  # Adjusted for MODIS resolution
    
    # SOC estimation (MODIS calibration with dynamic coefficients)
    soc = coeffs.soc_base + (ndvi * coeffs.soc_ndvi * 0.6) + (ndmi * coeffs.soc_ndmi * 0.5)
    soc = max(coeffs.soc_min * 0.2, min(coeffs.soc_max * 0.6, soc))  # Adjusted for MODIS resolution
    
    return {
        "Nitrogen": nitrogen,
        "Phosphorus": phosphorus,
        "Potassium": potassium,
        "SOC": soc
    }

def compute_indices_and_npk_for_bbox_modis(bbox: Dict[str, float], 
                                         start_date: Optional[datetime] = None, 
                                         end_date: Optional[datetime] = None,
                                         crop_type: str = "GENERIC") -> Dict[str, Any]:
    """Compute MODIS vegetation indices and NPK for bounding box with dynamic coefficients"""
    try:
        # Detect region from coordinates
        center_lat = (bbox['minLat'] + bbox['maxLat']) / 2
        center_lon = (bbox['minLon'] + bbox['maxLon']) / 2
        region = detect_region_from_coordinates(center_lat, center_lon)
        
        # Convert crop type string to enum
        crop_enum = get_crop_type_from_string(crop_type)
        
        logger.info(f"🌍 MODIS Region detected: {region.value}")
        logger.info(f"🌱 MODIS Crop type: {crop_enum.value}")
        
        # Set default date range if not provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Search for MODIS data
        catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
        
        search = catalog.search(
            collections=["modis-09a1-v061"],
            bbox=[bbox["minLon"], bbox["minLat"], bbox["maxLon"], bbox["maxLat"]],
            datetime=f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
            limit=1
        )
        
        items = list(search.items())
        if not items:
            return {"success": False, "error": "No MODIS data found for specified date range"}
        
        item = items[0]
        
        # Get MODIS bands
        red_href = item.assets["sur_refl_b01"].href
        nir_href = item.assets["sur_refl_b02"].href
        swir1_href = item.assets["sur_refl_b06"].href
        swir2_href = item.assets["sur_refl_b07"].href
        blue_href = item.assets["sur_refl_b03"].href
        
        # Load bands
        red = open_signed_raster(red_href)
        nir = open_signed_raster(nir_href)
        swir1 = open_signed_raster(swir1_href)
        swir2 = open_signed_raster(swir2_href)
        blue = open_signed_raster(blue_href)
        
        # Clip to bounding box
        red_clipped = red.rio.clip_box(**bbox)
        nir_clipped = nir.rio.clip_box(**bbox)
        swir1_clipped = swir1.rio.clip_box(**bbox)
        swir2_clipped = swir2.rio.clip_box(**bbox)
        blue_clipped = blue.rio.clip_box(**bbox)
        
        # Convert to numpy arrays
        red_array = red_clipped.values[0]
        nir_array = nir_clipped.values[0]
        swir1_array = swir1_clipped.values[0]
        swir2_array = swir2_clipped.values[0]
        blue_array = blue_clipped.values[0]
        
        # Compute indices
        indices = compute_modis_indices(red_array, nir_array, swir1_array, swir2_array, blue_array)
        
        # Estimate NPK
        npk = estimate_npk_from_modis_indices(indices, region, crop_enum)
        
        return {
            "success": True,
            "data": {
                "indices": indices,
                "npk": npk
            },
            "region": region.value,
            "cropType": crop_enum.value,
            "metadata": {
                "dataSource": "Microsoft Planetary Computer - MODIS Terra/Aqua",
                "resolution": "250m",
                "satellite": "MODIS",
                "region": region.value,
                "cropType": crop_enum.value,
                "processingTime": "unknown"
            }
        }
        
    except Exception as e:
        logger.error(f"MODIS processing error: {str(e)}")
        return {"success": False, "error": f"MODIS processing error: {str(e)}"}
