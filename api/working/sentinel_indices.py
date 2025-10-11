# sentinel_indices.py
import logging
import json
import os
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

# Set up logger first
logger = logging.getLogger("sentinel_indices")
logger.setLevel(logging.WARNING)  # Reduce log noise for performance

# Import Phase 1 modules for ICAR integration
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'kanker_soil_analysis_data', 'modules'))
    from range_processor import RangeProcessor, NutrientType, VillageContext
    from coordinate_matcher import CoordinateMatcher, ZoneType
    from data_validator import DataValidator, ValidationLevel
    from calibration_system import CalibrationSystem, CalibrationMethod
    ICAR_MODULES_AVAILABLE = True
    logger.info("✅ ICAR Phase 1 modules imported successfully!")
except ImportError as e:
    ICAR_MODULES_AVAILABLE = False
    logger.warning(f"⚠️ ICAR modules not available: {e}")

# ICAR Data Integration
class ICARDataManager:
    """Manages ICAR 2024-25 data for enhanced NPK calculations"""
    
    def __init__(self):
        self.icar_data = None
        self.range_processor = None
        self.coordinate_matcher = None
        self.data_validator = None
        self.calibration_system = None
        
        if ICAR_MODULES_AVAILABLE:
            self._initialize_icar_modules()
    
    def _initialize_icar_modules(self):
        """Initialize ICAR modules"""
        try:
            icar_data_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'kanker_soil_analysis_data', 
                'kanker_complete_soil_analysis_data.json'
            )
            
            self.range_processor = RangeProcessor()
            self.coordinate_matcher = CoordinateMatcher(icar_data_path)
            self.data_validator = DataValidator()
            self.calibration_system = CalibrationSystem(icar_data_path)
            
            # Load ICAR data
            self.icar_data = self._load_icar_data(icar_data_path)
            
            logger.info("✅ ICAR modules initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing ICAR modules: {e}")
            self.icar_data = None
    
    def _load_icar_data(self, path: str) -> Optional[Dict]:
        """Load ICAR data from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ICAR data: {e}")
            return None
    
    def get_enhanced_npk_values(
        self, 
        lat: float, 
        lon: float, 
        base_npk: Dict[str, float],
        crop_type: str = "GENERIC"
    ) -> Dict[str, Any]:
        """Get enhanced NPK values using ICAR data"""
        try:
            if not self.icar_data or not ICAR_MODULES_AVAILABLE:
                return {
                    'enhanced': False,
                    'npk': base_npk,
                    'confidence': 0.5,
                    'reason': 'ICAR data not available'
                }
            
            # Find closest village
            village_data = self._find_closest_village(lat, lon)
            if not village_data:
                return {
                    'enhanced': False,
                    'npk': base_npk,
                    'confidence': 0.6,
                    'reason': 'No ICAR village data found'
                }
            
            # Apply range processing
            enhanced_npk = self._apply_range_processing(
                base_npk, village_data, lat, lon, crop_type
            )
            
            # Apply calibration
            calibrated_npk = self._apply_calibration(
                enhanced_npk, village_data, lat, lon, crop_type
            )
            
            return {
                'enhanced': True,
                'npk': calibrated_npk,
                'confidence': 0.85,
                'village': village_data['village_name'],
                'reason': 'ICAR data applied successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced NPK calculation: {e}")
            return {
                'enhanced': False,
                'npk': base_npk,
                'confidence': 0.5,
                'reason': f'Error: {str(e)}'
            }
    
    def _find_closest_village(self, lat: float, lon: float) -> Optional[Dict]:
        """Find closest village in ICAR data"""
        try:
            if not self.icar_data or 'village_data' not in self.icar_data:
                return None
            
            villages = self.icar_data['village_data'].get('villages', [])
            if not villages:
                return None
            
            closest_village = None
            min_distance = float('inf')
            
            for village in villages:
                village_coords = village.get('coordinates', [])
                if len(village_coords) == 2:
                    village_lat, village_lon = village_coords
                    distance = self._calculate_distance(lat, lon, village_lat, village_lon)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_village = village
            
            if closest_village and min_distance <= 10.0:  # Within 10km
                return closest_village
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding closest village: {e}")
            return None
    
    def _apply_range_processing(
        self, 
        base_npk: Dict[str, float], 
        village_data: Dict, 
        lat: float, 
        lon: float, 
        crop_type: str
    ) -> Dict[str, float]:
        """Apply range processing to NPK values"""
        try:
            if not self.range_processor:
                return base_npk
            
            enhanced_npk = {}
            
            # Create village context
            village_context = VillageContext(
                village_name=village_data.get('village_name', 'Unknown'),
                coordinates=(lat, lon),
                soil_type='clay',
                crop_type=crop_type.lower(),
                season='kharif',
                rainfall='normal',
                zone=village_data.get('nitrogen_zone', 'yellow'),
                tehsil='kanker'
            )
            
            # Process each nutrient
            nutrients = ['nitrogen', 'phosphorus', 'potassium', 'soc', 'boron', 'iron', 'zinc', 'soil_ph']
            
            for nutrient in nutrients:
                base_value = base_npk.get(nutrient.capitalize(), 0)
                icar_value_str = village_data.get(f'estimated_{nutrient}', '0')
                
                # Handle range values (e.g., "453-523 kg/ha")
                if '-' in str(icar_value_str) and 'kg/ha' in str(icar_value_str):
                    # Extract numeric range
                    range_part = str(icar_value_str).split(' kg/ha')[0]
                    if '-' in range_part:
                        min_val, max_val = map(float, range_part.split('-'))
                        icar_value = (min_val + max_val) / 2  # Use average
                    else:
                        icar_value = float(range_part)
                else:
                    try:
                        # Handle values with units (e.g., "0.137 ppm", "4.25")
                        icar_value_str_clean = str(icar_value_str).split()[0]  # Remove units
                        icar_value = float(icar_value_str_clean) if icar_value_str_clean != '0' else 0
                    except (ValueError, TypeError):
                        icar_value = 0
                
                if base_value > 0 and icar_value > 0:
                    # Apply range processing
                    nutrient_type = getattr(NutrientType, nutrient.upper(), NutrientType.NITROGEN)
                    
                    result = self.range_processor.ai_powered_range_processing(
                        str(icar_value), base_value, village_context, nutrient_type
                    )
                    
                    enhanced_npk[nutrient.capitalize()] = result['value']
                elif icar_value > 0:
                    # Use ICAR value directly if satellite value is 0
                    enhanced_npk[nutrient.capitalize()] = icar_value
                    logger.info(f"🔬 {nutrient.capitalize()}: Using ICAR value {icar_value} (direct)")
                else:
                    enhanced_npk[nutrient.capitalize()] = base_value
            
            return enhanced_npk
            
        except Exception as e:
            logger.error(f"Error applying range processing: {e}")
            return base_npk
    
    def _apply_calibration(
        self, 
        npk_data: Dict[str, float], 
        village_data: Dict, 
        lat: float, 
        lon: float, 
        crop_type: str
    ) -> Dict[str, float]:
        """Apply calibration to NPK data"""
        try:
            if not self.calibration_system:
                return npk_data
            
            calibrated_npk = {}
            
            for nutrient, value in npk_data.items():
                if value > 0:
                    # Apply calibration
                    calibration_result = self.calibration_system.dynamic_calibration(
                        {nutrient: value},
                        village_data,
                        {'village_name': village_data['village_name'], 'coordinates': (lat, lon), 'soil_type': 'clay', 'crop_type': crop_type},
                        nutrient.lower()
                    )
                    
                    calibrated_npk[nutrient] = value * calibration_result.adjustment_factor
                else:
                    calibrated_npk[nutrient] = value
            
            return calibrated_npk
            
        except Exception as e:
            logger.error(f"Error applying calibration: {e}")
            return npk_data
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points"""
        try:
            import math
            
            R = 6371  # Earth's radius in kilometers
            
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = (math.sin(dlat/2) * math.sin(dlat/2) +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon/2) * math.sin(dlon/2))
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return distance
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')

# Initialize ICAR data manager
icar_manager = ICARDataManager()

# Default thresholds — configurable per region/crop via external config
THRESHOLDS = {
    "NDVI": { "low": 0.3, "medium": 0.55 },   # <0.3 low, 0.3-0.55 medium, >0.55 high
    "NDMI": { "low": 0.15, "medium": 0.4 },   # normalized moisture thresholds
    "SAVI": { "low": 0.2, "medium": 0.5 },
    "NDWI": { "low": 0.0, "medium": 0.2 }
}

def open_signed_raster(url: str):
    """Open a rasterio-supported file via planetary_computer signed URL, return xarray.DataArray"""
    signed = pc.sign(url)
    # rioxarray can open cloud-optimized GeoTIFFs from signed urls
    return rioxarray.open_rasterio(signed, masked=True)

def safe_mean(arr: np.ndarray) -> float:
    """Return mean ignoring nan and extreme values"""
    if arr is None or len(arr) == 0:
        return float("nan")
    arr = arr.astype(np.float64)
    mask = np.isfinite(arr)
    if not np.any(mask):
        return float("nan")
    # Clip outliers (optional) before mean
    q1, q99 = np.nanpercentile(arr[mask], [1, 99])
    arr_clipped = np.clip(arr, q1, q99)
    return float(np.nanmean(arr_clipped[mask]))

def clip_bands_parallel(asset_hrefs: List[str], bbox: Dict[str, float], max_workers: int = 4) -> Dict[str, Optional[xr.DataArray]]:
    """
    Process multiple bands in parallel for better performance
    Returns a dictionary mapping band names to DataArrays
    """
    results = {}
    
    def process_band(band_name: str, href: str) -> Tuple[str, Optional[xr.DataArray]]:
        try:
            logger.info(f"🚀 Processing band {band_name} in parallel")
            start_time = datetime.utcnow()
            data_array = clip_band_to_bbox(href, bbox)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Band {band_name} processed in {processing_time:.2f}s")
            return band_name, data_array
        except Exception as e:
            logger.error(f"❌ Error processing band {band_name}: {str(e)}")
            return band_name, None
    
    # Process bands in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all band processing tasks
        future_to_band = {
            executor.submit(process_band, band_name, href): band_name 
            for band_name, href in asset_hrefs.items() if href
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_band):
            band_name, data_array = future.result()
            results[band_name] = data_array
    
    logger.info(f"🎯 Parallel processing completed for {len(results)} bands")
    return results

def parse_datetime_safe(dt_str: str) -> datetime:
    """Safely parse datetime string, handling various formats including Z suffix"""
    try:
        # Remove Z suffix and replace with +00:00 for UTC
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        
        # Handle microseconds - ensure consistent format
        if '.' in dt_str:
            # Split on the decimal point
            base_part, microsecond_part = dt_str.split('.')
            # Find where timezone starts
            if '+' in microsecond_part:
                microsecond_str, tz_part = microsecond_part.split('+')
                tz_part = '+' + tz_part
            elif '-' in microsecond_part and microsecond_part.count('-') > 1:
                # Handle negative timezone
                parts = microsecond_part.split('-')
                microsecond_str = parts[0]
                tz_part = '-' + '-'.join(parts[1:])
            else:
                microsecond_str = microsecond_part
                tz_part = ''
            
            # Ensure microseconds are exactly 6 digits
            microsecond_str = microsecond_str[:6].ljust(6, '0')
            dt_str = f"{base_part}.{microsecond_str}{tz_part}"
        
        return datetime.fromisoformat(dt_str)
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{dt_str}': {e}, using fallback")
        return datetime(2023, 1, 1)

def fetch_best_sentinel_item(bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None,
                             max_cloud_cover: int = 80):
    """Search Planetary Computer STAC for the best sentinel-2 L2A item (lowest cloud)"""
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=180)  # Increased to 180 days for better data availability

    # Try different date ranges if no data found
    date_ranges = [
        (start_date, end_date),  # Original range
        (end_date - timedelta(days=365), end_date),  # 1 year
        (end_date - timedelta(days=730), end_date),  # 2 years
    ]
    
    for start_dt, end_dt in date_ranges:
        logger.info(f"🔍 DEBUG: Searching satellite data from {start_dt.date()} to {end_dt.date()}")
        
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
            datetime=f"{start_dt.isoformat()}/{end_dt.isoformat()}",
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
            limit=50
        )
        items = list(search.items())
        
        if items:
            logger.info(f"✅ Found {len(items)} satellite items in date range {start_dt.date()} to {end_dt.date()}")
            # choose lowest cloud cover and most recent preference
            items_sorted = sorted(items, key=lambda it: (it.properties.get('eo:cloud_cover', 100), -parse_datetime_safe(str(it.properties.get('datetime', '2023-01-01'))).timestamp()))
            return items_sorted[0]
        else:
            logger.info(f"❌ No satellite data found in date range {start_dt.date()} to {end_dt.date()}")
    
    logger.warning("❌ No satellite data found in any date range")
    return None

def clip_band_to_bbox(asset_href: str, bbox: Dict[str, float]) -> xr.DataArray:
    """
    Open and clip the band asset using rioxarray.clip_box
    Returns a 2D DataArray (band, y, x) -> squeeze to 2D
    """
    try:
        # asset_href is already a signed URL from the item
        with rioxarray.open_rasterio(asset_href, masked=True) as ds:
            # ds: (band, y, x) where band=1 for single-band tiff
            # Get data bounds and CRS
            data_bounds = ds.rio.bounds()
            data_crs = ds.rio.crs
            logger.info(f"Data bounds: {data_bounds}")
            logger.info(f"Data CRS: {data_crs}")
            logger.info(f"Requested bbox (geographic): {bbox}")
            
            # Convert geographic bbox to the data's CRS
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", data_crs, always_xy=True)
            
            # Transform the bbox corners
            minx_proj, miny_proj = transformer.transform(bbox['minLon'], bbox['minLat'])
            maxx_proj, maxy_proj = transformer.transform(bbox['maxLon'], bbox['maxLat'])
            
            logger.info(f"Transformed bbox: ({minx_proj}, {miny_proj}, {maxx_proj}, {maxy_proj})")
            
            # Check intersection with tolerance
            tolerance = 1000  # 1km in projected units
            intersects = not (maxx_proj + tolerance < data_bounds[0] or 
                             minx_proj - tolerance > data_bounds[2] or
                             maxy_proj + tolerance < data_bounds[1] or 
                             miny_proj - tolerance > data_bounds[3])
            
            if not intersects:
                logger.warning(f"Bounding box does not intersect with asset bounds. Data: {data_bounds}, Transformed: ({minx_proj}, {miny_proj}, {maxx_proj}, {maxy_proj})")
                return None
            
            # Clip using projected coordinates
            try:
                clipped = ds.rio.clip_box(
                    minx=minx_proj, 
                    miny=miny_proj, 
                    maxx=maxx_proj, 
                    maxy=maxy_proj
                )
                arr = clipped.squeeze(drop=True)  # drop band dim if present
                logger.info(f"Successfully clipped band, shape: {arr.shape}")
                return arr
            except Exception as clip_error:
                logger.warning(f"Direct clipping failed: {clip_error}, trying with expanded bbox")
                # Try with slightly expanded bbox
                clipped = ds.rio.clip_box(
                    minx=minx_proj - tolerance, 
                    miny=miny_proj - tolerance, 
                    maxx=maxx_proj + tolerance, 
                    maxy=maxy_proj + tolerance
                )
                arr = clipped.squeeze(drop=True)
                logger.info(f"Successfully clipped with expanded bbox, shape: {arr.shape}")
                return arr
                
    except Exception as e:
        logger.error(f"Error clipping band: {e}")
        return None

def compute_indices_from_arrays(red_arr: np.ndarray, nir_arr: np.ndarray, swir1_arr: np.ndarray = None, green_arr: np.ndarray = None) -> Dict[str, Any]:
    """
    Compute NDVI, NDMI, SAVI, NDWI statistics (mean, median, count).
    Arrays expected as 2D numpy arrays (same shape). Already handle flattening/masking.
    """
    out = {}
    try:
        # Prepare arrays - keep 2D structure for proper index calculation
        def _prep(a):
            if a is None:
                return None
            a = np.asarray(a).astype(np.float64)
            # Don't flatten - keep 2D structure
            return a
        
        # Get all arrays first
        red = _prep(red_arr)
        nir = _prep(nir_arr)
        swir1 = _prep(swir1_arr)
        green = _prep(green_arr)
        
        # Check if we have valid arrays
        valid_arrays = [arr for arr in [red, nir, swir1, green] if arr is not None and arr.size > 0]
        if not valid_arrays:
            logger.warning("🔍 DEBUG: No valid arrays for index calculation")
            return {}
        
        # Find the minimum shape to ensure all arrays have same dimensions
        shapes = [arr.shape for arr in valid_arrays]
        if not shapes:
            return {}
        
        # Use the smallest shape
        target_shape = min(shapes, key=lambda s: s[0] * s[1])
        logger.info(f"🔍 DEBUG: Target shape for indices: {target_shape}")
        
        # Resize all arrays to the same shape
        def _resize_to_shape(arr, target_shape):
            if arr is None:
                return None
            if arr.shape == target_shape:
                return arr
            # Crop to target shape
            rows = min(target_shape[0], arr.shape[0])
            cols = min(target_shape[1], arr.shape[1])
            return arr[:rows, :cols]
        
        red = _resize_to_shape(red, target_shape)
        nir = _resize_to_shape(nir, target_shape)
        swir1 = _resize_to_shape(swir1, target_shape)
        green = _resize_to_shape(green, target_shape)

        # NDVI with improved handling for bare soil/post-harvest
        if red is not None and nir is not None and red.size > 0 and nir.size > 0:
            logger.info(f"🔍 DEBUG: Red array shape: {red.shape}, NIR array shape: {nir.shape}")
            logger.info(f"🔍 DEBUG: Red min/max: {np.nanmin(red)}/{np.nanmax(red)}, NIR min/max: {np.nanmin(nir)}/{np.nanmax(nir)}")
            
            # Add small epsilon to avoid division by zero
            epsilon = 1e-8
            denom = nir + red + epsilon
            valid = denom > epsilon
            
            ndvi = np.zeros_like(denom, dtype=np.float64)
            ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
            
            # Clip NDVI to valid range [-1, 1]
            ndvi = np.clip(ndvi, -1.0, 1.0)
            
            logger.info(f"🔍 DEBUG: NDVI min/max: {np.nanmin(ndvi)}/{np.nanmax(ndvi)}, valid pixels: {np.sum(valid)}")
            mean_ndvi = float(np.nanmean(ndvi))
            median_ndvi = float(np.nanmedian(ndvi))
            
            # Handle NaN values for JSON serialization
            if np.isnan(mean_ndvi):
                mean_ndvi = 0.0
            if np.isnan(median_ndvi):
                median_ndvi = 0.0
                
            logger.info(f"🔍 DEBUG: NDVI mean: {mean_ndvi}")
            
            # Provide interpretation for negative values
            interpretation = "healthy_vegetation" if mean_ndvi > 0.3 else "sparse_vegetation" if mean_ndvi > 0.1 else "bare_soil_or_post_harvest"
            
            out['NDVI'] = {
                'mean': mean_ndvi,
                'median': median_ndvi,
                'count': int(np.sum(valid)),
                'interpretation': interpretation,
                'status': 'healthy' if mean_ndvi > 0.3 else 'needs_attention' if mean_ndvi > 0.1 else 'post_harvest_or_bare'
            }
        else:
            logger.warning(f"🔍 DEBUG: Red or NIR array is empty - Red: {red.size if red is not None else 'None'}, NIR: {nir.size if nir is not None else 'None'}")
            out['NDVI'] = {
                'mean': 0, 
                'median': 0, 
                'count': 0,
                'interpretation': 'no_data',
                'status': 'no_data'
            }

        # NDMI with improved handling
        if nir.size and swir1.size:
            epsilon = 1e-8
            denom = nir + swir1 + epsilon
            valid = denom > epsilon
            
            ndmi = np.zeros_like(denom, dtype=np.float64)
            ndmi[valid] = (nir[valid] - swir1[valid]) / denom[valid]
            
            # Clip NDMI to valid range [-1, 1]
            ndmi = np.clip(ndmi, -1.0, 1.0)
            
            mean_ndmi = float(np.nanmean(ndmi))
            median_ndmi = float(np.nanmedian(ndmi))
            
            # Handle NaN values for JSON serialization
            if np.isnan(mean_ndmi):
                mean_ndmi = 0.0
            if np.isnan(median_ndmi):
                median_ndmi = 0.0
                
            interpretation = "high_moisture" if mean_ndmi > 0.2 else "moderate_moisture" if mean_ndmi > 0.0 else "low_moisture_or_dry_soil"
            
            out['NDMI'] = {
                'mean': mean_ndmi,
                'median': median_ndmi,
                'count': int(np.sum(valid)),
                'interpretation': interpretation,
                'status': 'adequate' if mean_ndmi > 0.1 else 'needs_irrigation' if mean_ndmi > -0.1 else 'dry_soil'
            }
        else:
            out['NDMI'] = {
                'mean': 0.0, 
                'median': 0.0, 
                'count': 0,
                'interpretation': 'no_data',
                'status': 'no_data'
            }

        # SAVI (L = 0.5)
        L = 0.5
        if red.size and nir.size:
            denom = nir + red + L
            valid = denom != 0
            savi = np.zeros_like(denom, dtype=np.float64)
            savi[valid] = ((nir[valid] - red[valid]) * (1 + L)) / denom[valid]
            
            mean_savi = float(np.nanmean(savi))
            median_savi = float(np.nanmedian(savi))
            
            # Handle NaN values for JSON serialization
            if np.isnan(mean_savi):
                mean_savi = 0.0
            if np.isnan(median_savi):
                median_savi = 0.0
                
            out['SAVI'] = {
                'mean': mean_savi,
                'median': median_savi,
                'count': int(np.sum(valid))
            }
        else:
            out['SAVI'] = {'mean': 0.0, 'median': 0.0, 'count': 0}

        # NDWI (Green - NIR)
        if green.size and nir.size:
            denom = green + nir
            valid = denom != 0
            ndwi = np.zeros_like(denom, dtype=np.float64)
            ndwi[valid] = (green[valid] - nir[valid]) / denom[valid]
            
            mean_ndwi = float(np.nanmean(ndwi))
            median_ndwi = float(np.nanmedian(ndwi))
            
            # Handle NaN values for JSON serialization
            if np.isnan(mean_ndwi):
                mean_ndwi = 0.0
            if np.isnan(median_ndwi):
                median_ndwi = 0.0
                
            out['NDWI'] = {
                'mean': mean_ndwi,
                'median': median_ndwi,
                'count': int(np.sum(valid))
            }
        else:
            out['NDWI'] = {'mean': 0.0, 'median': 0.0, 'count': 0}

        return out

    except Exception as e:
        logger.error(f"Error computing indices: {e}")
        return {}

def qualitative_from_index(value: float, index_name: str, thresholds: Dict[str, Dict[str, float]] = THRESHOLDS) -> str:
    """Map index float to qualitative Low/Medium/High using thresholds"""
    if value is None or not isinstance(value, (int, float)) or np.isnan(value):
        return "unknown"
    t = thresholds.get(index_name, {})
    low = t.get('low')
    med = t.get('medium')
    if low is None or med is None:
        return "unknown"
    if value < low:
        return "low"
    if low <= value <= med:
        return "medium"
    return "high"

def estimate_nitrogen(ndvi: float, ndmi: float, savi: float, 
                     region: Region = Region.GLOBAL, 
                     crop_type: CropType = CropType.GENERIC,
                     lat: float = None, lon: float = None) -> float:
    """
    Estimate nitrogen content using dynamic regional and crop-specific coefficients
    """
    if any(x is None or not isinstance(x, (int, float)) or np.isnan(x) for x in [ndvi, ndmi, savi]):
        return 0.0
    
    # Get dynamic coefficients with local calibration
    coeffs = get_npk_coefficients(region, crop_type, lat, lon)
    
    # Calculate nitrogen using dynamic coefficients
    nitrogen_kg_ha = (ndvi * coeffs.nitrogen_ndvi) + (ndmi * coeffs.nitrogen_ndmi) + (savi * coeffs.nitrogen_savi) + coeffs.nitrogen_base
    
    # Clamp to regional range
    return max(coeffs.nitrogen_min, min(coeffs.nitrogen_max, nitrogen_kg_ha))

def estimate_phosphorus(ndvi: float, ndwi: float, savi: float,
                      region: Region = Region.GLOBAL,
                      crop_type: CropType = CropType.GENERIC,
                      lat: float = None, lon: float = None) -> float:
    """
    Estimate phosphorus content using dynamic regional and crop-specific coefficients
    """
    if any(x is None or not isinstance(x, (int, float)) or np.isnan(x) for x in [ndvi, ndwi, savi]):
        return 0.0
    
    # Get dynamic coefficients with local calibration
    coeffs = get_npk_coefficients(region, crop_type, lat, lon)
    
    # Calculate phosphorus using dynamic coefficients
    phosphorus_kg_ha = (ndvi * coeffs.phosphorus_ndvi) + (ndwi * coeffs.phosphorus_ndwi) + (savi * coeffs.phosphorus_savi) + coeffs.phosphorus_base
    
    # Clamp to regional range
    return max(coeffs.phosphorus_min, min(coeffs.phosphorus_max, phosphorus_kg_ha))

def estimate_potassium(ndvi: float, savi: float, ndmi: float,
                      region: Region = Region.GLOBAL,
                      crop_type: CropType = CropType.GENERIC,
                      lat: float = None, lon: float = None) -> float:
    """
    Estimate potassium content using dynamic regional and crop-specific coefficients
    """
    if any(x is None or not isinstance(x, (int, float)) or np.isnan(x) for x in [ndvi, savi, ndmi]):
        return 0.0
    
    # Get dynamic coefficients with local calibration
    coeffs = get_npk_coefficients(region, crop_type, lat, lon)
    
    # Calculate potassium using dynamic coefficients
    potassium_kg_ha = (ndvi * coeffs.potassium_ndvi) + (savi * coeffs.potassium_savi) + (ndmi * coeffs.potassium_ndmi) + coeffs.potassium_base
    
    # Clamp to regional range
    return max(coeffs.potassium_min, min(coeffs.potassium_max, potassium_kg_ha))

def estimate_soc(ndvi: float, ndmi: float, savi: float,
                 region: Region = Region.GLOBAL,
                 crop_type: CropType = CropType.GENERIC,
                 lat: float = None, lon: float = None) -> float:
    """
    Estimate soil organic carbon using dynamic regional and crop-specific coefficients
    """
    if any(x is None or not isinstance(x, (int, float)) or np.isnan(x) for x in [ndvi, ndmi, savi]):
        return 0.0
    
    # Get dynamic coefficients with local calibration
    coeffs = get_npk_coefficients(region, crop_type, lat, lon)
    
    # Calculate SOC using dynamic coefficients
    soc_percentage = (ndvi * coeffs.soc_ndvi) + (ndmi * coeffs.soc_ndmi) + (savi * coeffs.soc_savi) + coeffs.soc_base
    
    # Clamp to regional range
    return max(coeffs.soc_min, min(coeffs.soc_max, soc_percentage))

def map_indices_to_npk_soc(indices: Dict[str, Any], 
                          region: Region = Region.GLOBAL,
                          crop_type: CropType = CropType.GENERIC,
                          lat: float = None, lon: float = None,
                          cloud_cover: float = 0.0, satellite_type: str = "sentinel_2") -> Dict[str, float]:
    """
    Dynamic regional and crop-specific mapping from satellite indices to NPK/SOC values.
    Uses configurable coefficients based on region and crop type.
    """
    # Extract vegetation indices
    ndvi = indices.get('NDVI', {}).get('mean', 0)
    ndmi = indices.get('NDMI', {}).get('mean', 0)
    savi = indices.get('SAVI', {}).get('mean', 0)
    ndwi = indices.get('NDWI', {}).get('mean', 0)

    # Validate inputs - ensure all values are valid numbers
    if not all(isinstance(x, (int, float)) and not np.isnan(x) for x in [ndvi, ndmi, savi, ndwi]):
        logger.warning("Invalid vegetation indices detected, using default values")
        return {
            "Nitrogen": 0.0,
            "Phosphorus": 0.0,
            "Potassium": 0.0,
            "SOC": 0.0
        }

    # Estimate NPK using dynamic regional and crop-specific formulas with local calibration
    nitrogen_kg_ha = estimate_nitrogen(ndvi, ndmi, savi, region, crop_type, lat, lon)
    phosphorus_kg_ha = estimate_phosphorus(ndvi, ndwi, savi, region, crop_type, lat, lon)
    potassium_kg_ha = estimate_potassium(ndvi, savi, ndmi, region, crop_type, lat, lon)
    soc_percentage = estimate_soc(ndvi, ndmi, savi, region, crop_type, lat, lon)

    # Calculate dynamic accuracy
    from .npk_config import calculate_dynamic_accuracy
    accuracy = calculate_dynamic_accuracy(ndvi, cloud_cover, satellite_type)

    # Get soil type information
    from .npk_config import detect_soil_type_from_coordinates
    soil_type = detect_soil_type_from_coordinates(lat, lon) if lat and lon else "unknown"
    
    # Base NPK values from satellite indices
    base_npk = {
        "Nitrogen": nitrogen_kg_ha,
        "Phosphorus": phosphorus_kg_ha,
        "Potassium": potassium_kg_ha,
        "SOC": soc_percentage,
        "Boron": 0.0,  # Default micronutrient values
        "Iron": 0.0,
        "Zinc": 0.0,
        "Soil_pH": 0.0
    }
    
    # Apply ICAR enhancement if available
    if ICAR_MODULES_AVAILABLE and icar_manager and lat and lon:
        try:
            enhanced_result = icar_manager.get_enhanced_npk_values(
                lat, lon, base_npk, crop_type.value
            )
            
            if enhanced_result['enhanced']:
                logger.info(f"🔬 ICAR ENHANCEMENT APPLIED:")
                logger.info(f"   Village: {enhanced_result.get('village', 'Unknown')}")
                logger.info(f"   Confidence: {enhanced_result['confidence']:.2f}")
                logger.info(f"   Reason: {enhanced_result['reason']}")
                
                # Update NPK values with enhanced data
                enhanced_npk = enhanced_result['npk']
                base_npk.update(enhanced_npk)
                
                # Update accuracy with ICAR confidence
                accuracy = (accuracy + enhanced_result['confidence']) / 2
                
                logger.info(f"   Enhanced Nitrogen: {enhanced_npk.get('Nitrogen', nitrogen_kg_ha):.1f} kg/ha")
                logger.info(f"   Enhanced Phosphorus: {enhanced_npk.get('Phosphorus', phosphorus_kg_ha):.1f} kg/ha")
                logger.info(f"   Enhanced Potassium: {enhanced_npk.get('Potassium', potassium_kg_ha):.1f} kg/ha")
                logger.info(f"   Enhanced SOC: {enhanced_npk.get('SOC', soc_percentage):.2f}%")
                logger.info(f"   Enhanced Boron: {enhanced_npk.get('Boron', 0.0):.2f} ppm")
                logger.info(f"   Enhanced Iron: {enhanced_npk.get('Iron', 0.0):.2f} ppm")
                logger.info(f"   Enhanced Zinc: {enhanced_npk.get('Zinc', 0.0):.2f} ppm")
                logger.info(f"   Enhanced Soil pH: {enhanced_npk.get('Soil_pH', 0.0):.2f} pH")
            else:
                logger.info(f"⚠️ ICAR enhancement not applied: {enhanced_result['reason']}")
                
        except Exception as e:
            logger.error(f"❌ Error applying ICAR enhancement: {e}")
            logger.info("🔄 Falling back to base satellite NPK values")
    
    logger.info(f"🔬 DYNAMIC NPK ESTIMATION WITH LOCAL CALIBRATION:")
    logger.info(f"   Region: {region.value}, Crop: {crop_type.value}")
    logger.info(f"   Coordinates: {lat}, {lon}")
    logger.info(f"   Soil Type: {soil_type}")
    logger.info(f"   NDVI: {ndvi:.3f}, NDMI: {ndmi:.3f}, SAVI: {savi:.3f}, NDWI: {ndwi:.3f}")
    logger.info(f"   Nitrogen: {base_npk['Nitrogen']:.1f} kg/ha")
    logger.info(f"   Phosphorus: {base_npk['Phosphorus']:.1f} kg/ha")
    logger.info(f"   Potassium: {base_npk['Potassium']:.1f} kg/ha")
    logger.info(f"   SOC: {base_npk['SOC']:.2f}%")
    logger.info(f"   Boron: {base_npk.get('Boron', 0.0):.2f} ppm")
    logger.info(f"   Iron: {base_npk.get('Iron', 0.0):.2f} ppm")
    logger.info(f"   Zinc: {base_npk.get('Zinc', 0.0):.2f} ppm")
    logger.info(f"   Soil pH: {base_npk.get('Soil_pH', 0.0):.2f} pH")
    logger.info(f"   Dynamic Accuracy: {accuracy:.2f}")

    return {
        "Nitrogen": round(base_npk['Nitrogen'], 1),
        "Phosphorus": round(base_npk['Phosphorus'], 1),
        "Potassium": round(base_npk['Potassium'], 1),
        "SOC": round(base_npk['SOC'], 2),
        "Boron": round(base_npk.get('Boron', 0), 2),
        "Iron": round(base_npk.get('Iron', 0), 2),
        "Zinc": round(base_npk.get('Zinc', 0), 2),
        "Soil_pH": round(base_npk.get('Soil_pH', 0), 2),
        "Accuracy": round(accuracy, 2),
        "ICAR_Enhanced": ICAR_MODULES_AVAILABLE and icar_manager is not None,
        "Soil_Type": soil_type
    }

def compute_indices_and_npk_for_bbox(bbox: Dict[str, float],
                                     start_date: datetime = None,
                                     end_date: datetime = None,
                                     crop_type: str = "GENERIC") -> Dict[str, Any]:
    """
    End-to-end: find best sentinel item, clip bands, compute indices, map to NPK/SOC.
    Uses dynamic regional and crop-specific coefficients.
    Returns structured payload suitable for B2B API responses.
    """
    # Detect region from coordinates
    center_lat = (bbox['minLat'] + bbox['maxLat']) / 2
    center_lon = (bbox['minLon'] + bbox['maxLon']) / 2
    region = detect_region_from_coordinates(center_lat, center_lon)
    
    # Convert crop type string to enum
    crop_enum = get_crop_type_from_string(crop_type)
    
    logger.info(f"🌍 Region detected: {region.value}")
    logger.info(f"🌱 Crop type: {crop_enum.value}")
    
    # Optimized cloud cover thresholds for faster response
    cloud_thresholds = [40, 60]  # Reduced from 4 to 2 attempts for faster response
    
    for max_cloud_cover in cloud_thresholds:
        logger.info(f"🔍 DEBUG: Trying satellite search with {max_cloud_cover}% cloud cover")
        item = fetch_best_sentinel_item(bbox, start_date=start_date, end_date=end_date, max_cloud_cover=max_cloud_cover)
        if item is not None:
            logger.info(f"✅ Found satellite data with {max_cloud_cover}% cloud cover")
            break
    
    if item is None:
        logger.warning("❌ No satellite data found even with 80% cloud cover")
        return {"success": False, "error": "no_satellite_item_found", "satelliteItem": None}

    try:
        # Re-sign the item to get fresh URLs
        signed_item = pc.sign(item)
        logger.info(f"🔍 DEBUG: Item signed successfully: {signed_item.id}")
        
        # Check cloud cover
        cloud_cover = item.properties.get("eo:cloud_cover", 100)
        logger.info(f"🔍 DEBUG: Cloud cover: {cloud_cover}%")
        
        # Process real satellite data - removed fallback return
        logger.info(f"🛰️ Processing real satellite data from {item.id}")
        
        # Collect assets we need; fallback if some bands missing
        assets = signed_item.assets
        # required: B04 (red), B08 (nir)
        red_asset = assets.get("B04") or assets.get("B04_20m") or assets.get("red")
        nir_asset = assets.get("B08") or assets.get("nir")
        swir1_asset = assets.get("B11")
        green_asset = assets.get("B03")
        
        # Get fresh signed URLs for each asset
        def get_signed_url(asset):
            if asset is None:
                return None
            return pc.sign(asset).href
        
        red_href = get_signed_url(red_asset)
        nir_href = get_signed_url(nir_asset)
        swir1_href = get_signed_url(swir1_asset)
        green_href = get_signed_url(green_asset)
        
        logger.info(f"🔍 DEBUG: Got fresh signed URLs for all bands")

        if not red_asset or not nir_asset:
            return {"success": False, "error": "required_bands_missing", "satelliteItem": item.id}

        # Prepare band assets for parallel processing using fresh signed URLs
        band_assets = {
            'red': red_href,
            'nir': nir_href,
            'swir1': swir1_href,
            'green': green_href
        }
        
        # Process bands in parallel for better performance (optimized workers)
        logger.info("🚀 Starting parallel band processing")
        start_time = datetime.utcnow()
        band_data = clip_bands_parallel(band_assets, bbox, max_workers=2)  # Reduced workers for faster processing
        parallel_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"⚡ Parallel band processing completed in {parallel_time:.2f}s")
        
        # Extract individual bands
        red_da = band_data.get('red')
        nir_da = band_data.get('nir')
        swir1_da = band_data.get('swir1')
        green_da = band_data.get('green')

        # Convert to numpy arrays: ensure all bands have the same shape
        def _to_np(da):
            if da is None:
                return None
            arr = np.asarray(da.values)
            # reduce dims: (band, y, x) or (y, x)
            if arr.ndim == 3:
                arr = arr.squeeze(axis=0)
            return arr

        # Get all arrays first
        red_np = _to_np(red_da)
        nir_np = _to_np(nir_da)
        swir1_np = _to_np(swir1_da)
        green_np = _to_np(green_da)
        
        # Debug: Check if arrays have valid data
        logger.info(f"🔍 DEBUG: Array shapes - Red: {red_np.shape if red_np is not None else None}, NIR: {nir_np.shape if nir_np is not None else None}")
        if red_np is not None:
            logger.info(f"🔍 DEBUG: Red array - min: {np.nanmin(red_np)}, max: {np.nanmax(red_np)}, mean: {np.nanmean(red_np)}")
        if nir_np is not None:
            logger.info(f"🔍 DEBUG: NIR array - min: {np.nanmin(nir_np)}, max: {np.nanmax(nir_np)}, mean: {np.nanmean(nir_np)}")

        # Find the target shape (use the smallest common shape)
        shapes = []
        if red_np is not None:
            shapes.append(red_np.shape)
        if nir_np is not None:
            shapes.append(nir_np.shape)
        if swir1_np is not None:
            shapes.append(swir1_np.shape)
        if green_np is not None:
            shapes.append(green_np.shape)

        if not shapes:
            return {"success": False, "error": "no_valid_bands", "satelliteItem": item.id}

        # Use the smallest shape to ensure all arrays fit
        target_shape = min(shapes, key=lambda s: s[0] * s[1])
        logger.info(f"Target shape for all bands: {target_shape}")

        # Resample all arrays to the same shape
        def _resample_to_shape(arr, target_shape):
            if arr is None:
                logger.warning(f"🔍 DEBUG: Array is None, cannot resample")
                return None
            if arr.shape == target_shape:
                logger.info(f"🔍 DEBUG: Array already correct shape: {arr.shape}")
                return arr
            # Ensure we don't exceed array bounds
            rows_to_take = min(target_shape[0], arr.shape[0])
            cols_to_take = min(target_shape[1], arr.shape[1])
            resampled = arr[:rows_to_take, :cols_to_take]
            logger.info(f"🔍 DEBUG: Resampling {arr.shape} to {resampled.shape}")
            logger.info(f"🔍 DEBUG: Resampled array min/max: {np.nanmin(resampled)}/{np.nanmax(resampled)}")
            return resampled

        red_np = _resample_to_shape(red_np, target_shape)
        nir_np = _resample_to_shape(nir_np, target_shape)
        swir1_np = _resample_to_shape(swir1_np, target_shape)
        green_np = _resample_to_shape(green_np, target_shape)

        logger.info(f"Final shapes - Red: {red_np.shape if red_np is not None else None}, NIR: {nir_np.shape if nir_np is not None else None}, SWIR1: {swir1_np.shape if swir1_np is not None else None}, Green: {green_np.shape if green_np is not None else None}")

        logger.info(f"🔍 DEBUG: About to compute indices with arrays:")
        logger.info(f"   Red: {red_np.shape if red_np is not None else None}")
        logger.info(f"   NIR: {nir_np.shape if nir_np is not None else None}")
        logger.info(f"   SWIR1: {swir1_np.shape if swir1_np is not None else None}")
        logger.info(f"   Green: {green_np.shape if green_np is not None else None}")
        
        indices = compute_indices_from_arrays(red_np, nir_np, swir1_np, green_np)
        logger.info(f"🔍 DEBUG: Computed indices: {indices}")
        
        # Get cloud cover for accuracy calculation
        cloud_cover = item.properties.get("eo:cloud_cover", 0)
        
        npk = map_indices_to_npk_soc(indices, region, crop_enum, center_lat, center_lon, cloud_cover, "sentinel_2")
        logger.info(f"🔍 DEBUG: Mapped NPK with local calibration: {npk}")

        # Get soil type information
        from .npk_config import detect_soil_type_from_coordinates
        soil_type = detect_soil_type_from_coordinates(center_lat, center_lon)
        
        response = {
            "success": True,
            "satelliteItem": item.id,
            "imageDate": item.properties.get("datetime"),
            "cloudCover": item.properties.get("eo:cloud_cover"),
            "region": region.value,
            "cropType": crop_enum.value,
            "coordinates": [center_lat, center_lon],
            "soilType": soil_type,
            "localCalibration": "applied",
            "soilTypeCalibration": "applied",
            "dynamicAccuracy": npk.get("Accuracy", 0.0),
            "data": {
                "indices": indices,
                "npk": npk
            },
            "indices": indices,  # Also include at root level for compatibility
            "npk": npk,  # Also include at root level for compatibility
            "metadata": {
                "provider": "Microsoft Planetary Computer",
                "satellite": "Sentinel-2 L2A",
                "region": region.value,
                "cropType": crop_enum.value,
                "soilType": soil_type,
                "localCalibration": "applied",
                "soilTypeCalibration": "applied",
                "dynamicAccuracy": npk.get("Accuracy", 0.0),
                "fetchedAt": datetime.utcnow().isoformat()
            }
        }
        return response

    except Exception as e:
        logger.exception("Error computing indices and npk")
        return {"success": False, "error": str(e), "satelliteItem": item.id}
