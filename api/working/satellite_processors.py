#!/usr/bin/env python3
"""
Multi-Satellite Processing System
Satellite-specific processors for different data sources
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import xarray as xr
import pystac_client
from planetary_computer import sign as pc_sign

logger = logging.getLogger(__name__)

class BaseSatelliteProcessor:
    """Base class for all satellite processors"""
    
    def __init__(self, satellite_id: str, collection: str, resolution: str):
        self.satellite_id = satellite_id
        self.collection = collection
        self.resolution = resolution
        self.logger = logging.getLogger(f"{__name__}.{satellite_id}")
    
    def parse_datetime_safe(self, dt_str: str) -> datetime:
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
            self.logger.warning(f"Failed to parse datetime '{dt_str}': {e}, using fallback")
            return datetime(2023, 1, 1)

    def search_satellite_data(self, bbox: Dict[str, float], 
                             start_date: datetime = None,
                             end_date: datetime = None,
                             max_cloud_cover: int = 80) -> Optional[Any]:
        """Search for satellite data in the specified collection"""
        catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
        
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=90)
        
        search = catalog.search(
            collections=[self.collection],
            bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
            datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
            limit=50
        )
        
        items = list(search.items())
        if not items:
            return None
        
        # Choose lowest cloud cover and most recent
        items_sorted = sorted(items, key=lambda it: (
            it.properties.get('eo:cloud_cover', 100), 
            -self.parse_datetime_safe(str(it.properties.get('datetime', '2023-01-01'))).timestamp()
        ))
        return items_sorted[0]
    
    def clip_band_to_bbox(self, asset_href: str, bbox: Dict[str, float]) -> xr.DataArray:
        """Clip satellite band to bounding box with proper coordinate transformation"""
        try:
            # Use rioxarray for modern xarray compatibility
            import rioxarray as rio
            from pyproj import Transformer
            
            # Open the raster data
            da = rio.open_rasterio(asset_href, masked=True)
            
            # Get data bounds and CRS
            data_bounds = da.rio.bounds()
            data_crs = da.rio.crs
            
            self.logger.info(f"🔍 DEBUG: Data bounds: {data_bounds}")
            self.logger.info(f"🔍 DEBUG: Data CRS: {data_crs}")
            self.logger.info(f"🔍 DEBUG: Requested bbox (geographic): {bbox}")
            
            # Convert geographic bbox to the data's CRS
            transformer = Transformer.from_crs("EPSG:4326", data_crs, always_xy=True)
            
            # Transform the bbox corners
            minx_proj, miny_proj = transformer.transform(bbox['minLon'], bbox['minLat'])
            maxx_proj, maxy_proj = transformer.transform(bbox['maxLon'], bbox['maxLat'])
            
            self.logger.info(f"🔍 DEBUG: Transformed bbox: ({minx_proj}, {miny_proj}, {maxx_proj}, {maxy_proj})")
            
            # Check intersection with tolerance
            tolerance = 1000  # 1km in projected units
            intersects = not (maxx_proj + tolerance < data_bounds[0] or 
                             minx_proj - tolerance > data_bounds[2] or
                             maxy_proj + tolerance < data_bounds[1] or 
                             miny_proj - tolerance > data_bounds[3])
            
            if not intersects:
                self.logger.warning(f"⚠️ Bounding box does not intersect with asset bounds. Data: {data_bounds}, Transformed: ({minx_proj}, {miny_proj}, {maxx_proj}, {maxy_proj})")
                return None
            
            # Clip using projected coordinates
            try:
                clipped = da.rio.clip_box(
                    minx=minx_proj, 
                    miny=miny_proj, 
                    maxx=maxx_proj, 
                    maxy=maxy_proj
                )
                arr = clipped.squeeze(drop=True)  # drop band dim if present
                self.logger.info(f"✅ Successfully clipped band, shape: {arr.shape}")
                
                # Validate the clipped data
                if arr.size == 0:
                    self.logger.warning("⚠️ Clipped array is empty")
                    return None
                
                # Check for valid data (not all NaN or zeros)
                valid_pixels = np.sum(np.isfinite(arr) & (arr != 0))
                if valid_pixels == 0:
                    self.logger.warning("⚠️ No valid pixels found in clipped data")
                    return None
                
                self.logger.info(f"✅ Valid pixels: {valid_pixels}/{arr.size} ({valid_pixels/arr.size*100:.1f}%)")
                return arr
                
            except Exception as clip_error:
                self.logger.warning(f"⚠️ Direct clipping failed: {clip_error}, trying with expanded bbox")
                # Try with slightly expanded bbox
                clipped = da.rio.clip_box(
                    minx=minx_proj - tolerance, 
                    miny=miny_proj - tolerance, 
                    maxx=maxx_proj + tolerance, 
                    maxy=maxy_proj + tolerance
                )
                arr = clipped.squeeze(drop=True)
                
                # Validate the expanded clipped data
                if arr.size == 0:
                    self.logger.warning("⚠️ Expanded clipped array is empty")
                    return None
                
                valid_pixels = np.sum(np.isfinite(arr) & (arr != 0))
                if valid_pixels == 0:
                    self.logger.warning("⚠️ No valid pixels found in expanded clipped data")
                    return None
                
                self.logger.info(f"✅ Successfully clipped with expanded bbox, shape: {arr.shape}, valid pixels: {valid_pixels}")
                return arr
                
        except Exception as e:
            self.logger.error(f"❌ Error clipping band: {e}")
            return None
    
    def compute_indices_from_arrays(self, **kwargs) -> Dict[str, Any]:
        """Compute vegetation indices from band arrays - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement compute_indices_from_arrays")
    
    def map_indices_to_npk_soc(self, indices: Dict[str, Any]) -> Dict[str, str]:
        """Map vegetation indices to NPK/SOC levels - common for all optical satellites"""
        # Use the same mapping logic as current sentinel_indices.py
        thresholds = {
            'ndvi': {'low': 0.3, 'medium': 0.5, 'high': 0.7},
            'ndmi': {'low': 0.2, 'medium': 0.4, 'high': 0.6},
            'ndwi': {'low': 0.1, 'medium': 0.3, 'high': 0.5}
        }
        
        npk_soc = {}
        for index_name, value in indices.items():
            if index_name in thresholds and isinstance(value, (int, float)):
                if value < thresholds[index_name]['low']:
                    npk_soc[index_name] = 'low'
                elif value < thresholds[index_name]['medium']:
                    npk_soc[index_name] = 'medium'
                else:
                    npk_soc[index_name] = 'high'
        
        # Map to NPK/SOC
        nitrogen = npk_soc.get('ndvi', 'medium')
        phosphorus = npk_soc.get('ndmi', 'medium')
        potassium = npk_soc.get('ndvi', 'medium')
        soc = npk_soc.get('ndmi', 'medium')
        
        return {
            'Nitrogen': nitrogen,
            'Phosphorus': phosphorus,
            'Potassium': potassium,
            'SOC': soc
        }
    
    def process_satellite_data(self, bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Main processing method - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_satellite_data")


class Sentinel2Processor(BaseSatelliteProcessor):
    """Sentinel-2 L2A processor (10m resolution, optical)"""
    
    def __init__(self):
        super().__init__("sentinel-2-l2a", "sentinel-2-l2a", "10m")
        self.required_bands = {
            'red': ['B04', 'B04_20m'],
            'nir': ['B08', 'B08_20m'],
            'swir1': ['B11', 'B11_20m'],
            'swir2': ['B12', 'B12_20m'],
            'green': ['B03', 'B03_20m'],
            'blue': ['B02', 'B02_20m']
        }
    
    def compute_indices_from_arrays(self, red_arr: np.ndarray, nir_arr: np.ndarray, 
                                   swir1_arr: np.ndarray = None, green_arr: np.ndarray = None) -> Dict[str, Any]:
        """Compute vegetation indices from Sentinel-2 bands with robust validation"""
        indices = {}
        
        # Helper function to validate array data
        def validate_array(arr, name):
            if arr is None:
                self.logger.warning(f"⚠️ {name} array is None")
                return False
            if arr.size == 0:
                self.logger.warning(f"⚠️ {name} array is empty")
                return False
            
            # Check for valid data (not all NaN or zeros)
            valid_pixels = np.sum(np.isfinite(arr) & (arr != 0))
            if valid_pixels == 0:
                self.logger.warning(f"⚠️ {name} array has no valid pixels")
                return False
            
            # Check for reasonable satellite data values (typically 0-10000 for Sentinel-2)
            if np.nanmax(arr) > 20000 or np.nanmin(arr) < -1000:
                self.logger.warning(f"⚠️ {name} array has suspicious values: min={np.nanmin(arr)}, max={np.nanmax(arr)}")
            
            self.logger.info(f"✅ {name} array: shape={arr.shape}, valid_pixels={valid_pixels}/{arr.size} ({valid_pixels/arr.size*100:.1f}%), range=[{np.nanmin(arr):.1f}, {np.nanmax(arr):.1f}]")
            return True
        
        # NDVI = (NIR - Red) / (NIR + Red)
        if validate_array(red_arr, "Red") and validate_array(nir_arr, "NIR"):
            # Ensure arrays have same shape
            if red_arr.shape != nir_arr.shape:
                self.logger.warning(f"⚠️ Shape mismatch: Red {red_arr.shape} vs NIR {nir_arr.shape}")
                # Use the smaller shape
                min_rows = min(red_arr.shape[0], nir_arr.shape[0])
                min_cols = min(red_arr.shape[1], nir_arr.shape[1])
                red_arr = red_arr[:min_rows, :min_cols]
                nir_arr = nir_arr[:min_rows, :min_cols]
                self.logger.info(f"✅ Resized arrays to: {red_arr.shape}")
            
            # Compute NDVI with proper handling
            epsilon = 1e-8
            denom = nir_arr + red_arr + epsilon
            valid = denom > epsilon
            
            ndvi = np.zeros_like(denom, dtype=np.float64)
            ndvi[valid] = (nir_arr[valid] - red_arr[valid]) / denom[valid]
            
            # Clip NDVI to valid range [-1, 1]
            ndvi = np.clip(ndvi, -1.0, 1.0)
            
            ndvi_mean = float(np.nanmean(ndvi))
            ndvi_median = float(np.nanmedian(ndvi))
            valid_count = int(np.sum(valid))
            
            self.logger.info(f"✅ NDVI: mean={ndvi_mean:.4f}, median={ndvi_median:.4f}, valid_pixels={valid_count}")
            
            indices['ndvi'] = ndvi_mean if not np.isnan(ndvi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDVI: invalid Red or NIR data")
            indices['ndvi'] = 0.0
        
        # NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        if validate_array(nir_arr, "NIR") and validate_array(swir1_arr, "SWIR1"):
            # Ensure arrays have same shape
            if nir_arr.shape != swir1_arr.shape:
                self.logger.warning(f"⚠️ Shape mismatch: NIR {nir_arr.shape} vs SWIR1 {swir1_arr.shape}")
                min_rows = min(nir_arr.shape[0], swir1_arr.shape[0])
                min_cols = min(nir_arr.shape[1], swir1_arr.shape[1])
                nir_arr = nir_arr[:min_rows, :min_cols]
                swir1_arr = swir1_arr[:min_rows, :min_cols]
            
            epsilon = 1e-8
            denom = nir_arr + swir1_arr + epsilon
            valid = denom > epsilon
            
            ndmi = np.zeros_like(denom, dtype=np.float64)
            ndmi[valid] = (nir_arr[valid] - swir1_arr[valid]) / denom[valid]
            
            # Clip NDMI to valid range [-1, 1]
            ndmi = np.clip(ndmi, -1.0, 1.0)
            
            ndmi_mean = float(np.nanmean(ndmi))
            ndmi_median = float(np.nanmedian(ndmi))
            valid_count = int(np.sum(valid))
            
            self.logger.info(f"✅ NDMI: mean={ndmi_mean:.4f}, median={ndmi_median:.4f}, valid_pixels={valid_count}")
            
            indices['ndmi'] = ndmi_mean if not np.isnan(ndmi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDMI: invalid NIR or SWIR1 data")
            indices['ndmi'] = 0.0
        
        # NDWI = (Green - NIR) / (Green + NIR)
        if validate_array(green_arr, "Green") and validate_array(nir_arr, "NIR"):
            # Ensure arrays have same shape
            if green_arr.shape != nir_arr.shape:
                self.logger.warning(f"⚠️ Shape mismatch: Green {green_arr.shape} vs NIR {nir_arr.shape}")
                min_rows = min(green_arr.shape[0], nir_arr.shape[0])
                min_cols = min(green_arr.shape[1], nir_arr.shape[1])
                green_arr = green_arr[:min_rows, :min_cols]
                nir_arr = nir_arr[:min_rows, :min_cols]
            
            epsilon = 1e-8
            denom = green_arr + nir_arr + epsilon
            valid = denom > epsilon
            
            ndwi = np.zeros_like(denom, dtype=np.float64)
            ndwi[valid] = (green_arr[valid] - nir_arr[valid]) / denom[valid]
            
            # Clip NDWI to valid range [-1, 1]
            ndwi = np.clip(ndwi, -1.0, 1.0)
            
            ndwi_mean = float(np.nanmean(ndwi))
            ndwi_median = float(np.nanmedian(ndwi))
            valid_count = int(np.sum(valid))
            
            self.logger.info(f"✅ NDWI: mean={ndwi_mean:.4f}, median={ndwi_median:.4f}, valid_pixels={valid_count}")
            
            indices['ndwi'] = ndwi_mean if not np.isnan(ndwi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDWI: invalid Green or NIR data")
            indices['ndwi'] = 0.0
        
        return indices
    
    def process_satellite_data(self, bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Process Sentinel-2 data"""
        start_time = time.time()
        
        try:
            # Search for satellite data
            item = self.search_satellite_data(bbox, start_date, end_date)
            if item is None:
                return {"success": False, "error": "no_satellite_item_found", "satellite": self.satellite_id}
            
            # Sign the item
            signed_item = pc_sign(item)
            assets = signed_item.assets
            
            # Get required bands with improved validation
            band_data = {}
            self.logger.info(f"🔍 DEBUG: Processing {len(self.required_bands)} band types")
            
            for band_type, possible_names in self.required_bands.items():
                self.logger.info(f"🔍 DEBUG: Looking for {band_type} band in {possible_names}")
                band_found = False
                
                for name in possible_names:
                    if name in assets:
                        self.logger.info(f"🔍 DEBUG: Found {name} asset for {band_type}")
                        asset_href = assets[name].href
                        clipped = self.clip_band_to_bbox(asset_href, bbox)
                        
                        if clipped is not None:
                            # clipped is already a numpy array from our improved clip_band_to_bbox
                            band_data[band_type] = clipped
                            self.logger.info(f"✅ Successfully processed {band_type} band: shape={clipped.shape}")
                            band_found = True
                            break
                        else:
                            self.logger.warning(f"⚠️ Failed to clip {name} for {band_type}")
                    else:
                        self.logger.debug(f"🔍 DEBUG: {name} not found in assets")
                
                if not band_found:
                    self.logger.warning(f"⚠️ No valid {band_type} band found")
            
            self.logger.info(f"🔍 DEBUG: Successfully processed {len(band_data)} bands: {list(band_data.keys())}")
            
            # Compute indices
            indices = self.compute_indices_from_arrays(
                red_arr=band_data.get('red'),
                nir_arr=band_data.get('nir'),
                swir1_arr=band_data.get('swir1'),
                green_arr=band_data.get('green')
            )
            
            # Map to NPK/SOC
            npk_soc = self.map_indices_to_npk_soc(indices)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "satellite": self.satellite_id,
                "resolution": self.resolution,
                "cloud_coverage": item.properties.get("eo:cloud_cover", 0),
                "acquisition_date": str(item.properties.get("datetime", "")),
                "indices": indices,
                "npk": npk_soc,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Sentinel-2 data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "satellite": self.satellite_id,
                "processing_time": time.time() - start_time
            }


class Landsat8Processor(BaseSatelliteProcessor):
    """Landsat-8 C2 L2 processor (30m resolution, optical)"""
    
    def __init__(self):
        super().__init__("landsat-8-c2-l2", "landsat-c2-l2", "30m")
        self.required_bands = {
            'red': ['B04'],
            'nir': ['B05'],
            'swir1': ['B06'],
            'swir2': ['B07'],
            'green': ['B03'],
            'blue': ['B02']
        }
    
    def compute_indices_from_arrays(self, red_arr: np.ndarray, nir_arr: np.ndarray, 
                                   swir1_arr: np.ndarray = None, green_arr: np.ndarray = None) -> Dict[str, Any]:
        """Compute vegetation indices from Landsat-8 bands with robust validation"""
        indices = {}
        
        # Helper function to validate array data
        def validate_array(arr, name):
            if arr is None:
                self.logger.warning(f"⚠️ {name} array is None")
                return False
            if arr.size == 0:
                self.logger.warning(f"⚠️ {name} array is empty")
                return False
            
            # Check for valid data (not all NaN or zeros)
            valid_pixels = np.sum(np.isfinite(arr) & (arr != 0))
            if valid_pixels == 0:
                self.logger.warning(f"⚠️ {name} array has no valid pixels")
                return False
            
            # Check for reasonable satellite data values (typically 0-10000 for Landsat-8)
            if np.nanmax(arr) > 20000 or np.nanmin(arr) < -1000:
                self.logger.warning(f"⚠️ {name} array has suspicious values: min={np.nanmin(arr)}, max={np.nanmax(arr)}")
            
            self.logger.info(f"✅ {name} array: shape={arr.shape}, valid_pixels={valid_pixels}/{arr.size} ({valid_pixels/arr.size*100:.1f}%), range=[{np.nanmin(arr):.1f}, {np.nanmax(arr):.1f}]")
            return True
        
        # NDVI = (NIR - Red) / (NIR + Red)
        if validate_array(red_arr, "Red") and validate_array(nir_arr, "NIR"):
            # Ensure arrays have same shape
            if red_arr.shape != nir_arr.shape:
                self.logger.warning(f"⚠️ Shape mismatch: Red {red_arr.shape} vs NIR {nir_arr.shape}")
                min_rows = min(red_arr.shape[0], nir_arr.shape[0])
                min_cols = min(red_arr.shape[1], nir_arr.shape[1])
                red_arr = red_arr[:min_rows, :min_cols]
                nir_arr = nir_arr[:min_rows, :min_cols]
            
            epsilon = 1e-8
            denom = nir_arr + red_arr + epsilon
            valid = denom > epsilon
            
            ndvi = np.zeros_like(denom, dtype=np.float64)
            ndvi[valid] = (nir_arr[valid] - red_arr[valid]) / denom[valid]
            ndvi = np.clip(ndvi, -1.0, 1.0)
            
            ndvi_mean = float(np.nanmean(ndvi))
            self.logger.info(f"✅ NDVI: mean={ndvi_mean:.4f}, valid_pixels={int(np.sum(valid))}")
            indices['ndvi'] = ndvi_mean if not np.isnan(ndvi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDVI: invalid Red or NIR data")
            indices['ndvi'] = 0.0
        
        # NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        if validate_array(nir_arr, "NIR") and validate_array(swir1_arr, "SWIR1"):
            if nir_arr.shape != swir1_arr.shape:
                min_rows = min(nir_arr.shape[0], swir1_arr.shape[0])
                min_cols = min(nir_arr.shape[1], swir1_arr.shape[1])
                nir_arr = nir_arr[:min_rows, :min_cols]
                swir1_arr = swir1_arr[:min_rows, :min_cols]
            
            epsilon = 1e-8
            denom = nir_arr + swir1_arr + epsilon
            valid = denom > epsilon
            
            ndmi = np.zeros_like(denom, dtype=np.float64)
            ndmi[valid] = (nir_arr[valid] - swir1_arr[valid]) / denom[valid]
            ndmi = np.clip(ndmi, -1.0, 1.0)
            
            ndmi_mean = float(np.nanmean(ndmi))
            self.logger.info(f"✅ NDMI: mean={ndmi_mean:.4f}, valid_pixels={int(np.sum(valid))}")
            indices['ndmi'] = ndmi_mean if not np.isnan(ndmi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDMI: invalid NIR or SWIR1 data")
            indices['ndmi'] = 0.0
        
        # NDWI = (Green - NIR) / (Green + NIR)
        if validate_array(green_arr, "Green") and validate_array(nir_arr, "NIR"):
            if green_arr.shape != nir_arr.shape:
                min_rows = min(green_arr.shape[0], nir_arr.shape[0])
                min_cols = min(green_arr.shape[1], nir_arr.shape[1])
                green_arr = green_arr[:min_rows, :min_cols]
                nir_arr = nir_arr[:min_rows, :min_cols]
            
            epsilon = 1e-8
            denom = green_arr + nir_arr + epsilon
            valid = denom > epsilon
            
            ndwi = np.zeros_like(denom, dtype=np.float64)
            ndwi[valid] = (green_arr[valid] - nir_arr[valid]) / denom[valid]
            ndwi = np.clip(ndwi, -1.0, 1.0)
            
            ndwi_mean = float(np.nanmean(ndwi))
            self.logger.info(f"✅ NDWI: mean={ndwi_mean:.4f}, valid_pixels={int(np.sum(valid))}")
            indices['ndwi'] = ndwi_mean if not np.isnan(ndwi_mean) else 0.0
        else:
            self.logger.warning("❌ Cannot compute NDWI: invalid Green or NIR data")
            indices['ndwi'] = 0.0
        
        return indices
    
    def process_satellite_data(self, bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Process Landsat-8 data"""
        start_time = time.time()
        
        try:
            # Search for satellite data
            item = self.search_satellite_data(bbox, start_date, end_date)
            if item is None:
                return {"success": False, "error": "no_satellite_item_found", "satellite": self.satellite_id}
            
            # Sign the item
            signed_item = pc_sign(item)
            assets = signed_item.assets
            
            # Get required bands
            band_data = {}
            for band_type, possible_names in self.required_bands.items():
                for name in possible_names:
                    if name in assets:
                        asset_href = assets[name].href
                        clipped = self.clip_band_to_bbox(asset_href, bbox)
                        if clipped is not None:
                            band_data[band_type] = clipped.values[0]
                            break
            
            # Compute indices
            indices = self.compute_indices_from_arrays(
                red_arr=band_data.get('red'),
                nir_arr=band_data.get('nir'),
                swir1_arr=band_data.get('swir1'),
                green_arr=band_data.get('green')
            )
            
            # Map to NPK/SOC
            npk_soc = self.map_indices_to_npk_soc(indices)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "satellite": self.satellite_id,
                "resolution": self.resolution,
                "cloud_coverage": item.properties.get("eo:cloud_cover", 0),
                "acquisition_date": str(item.properties.get("datetime", "")),
                "indices": indices,
                "npk": npk_soc,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Landsat-8 data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "satellite": self.satellite_id,
                "processing_time": time.time() - start_time
            }


class ModisProcessor(BaseSatelliteProcessor):
    """MODIS 09A1 processor (250m resolution, optical)"""
    
    def __init__(self):
        super().__init__("modis-09A1-061", "modis-09A1-061", "250m")
        self.required_bands = {
            'red': ['sur_refl_b01'],
            'nir': ['sur_refl_b02'],
            'swir1': ['sur_refl_b06'],
            'swir2': ['sur_refl_b07'],
            'green': ['sur_refl_b04'],
            'blue': ['sur_refl_b03']
        }
    
    def compute_indices_from_arrays(self, red_arr: np.ndarray, nir_arr: np.ndarray, 
                                   swir1_arr: np.ndarray = None, green_arr: np.ndarray = None) -> Dict[str, Any]:
        """Compute vegetation indices from MODIS bands"""
        indices = {}
        
        # NDVI = (NIR - Red) / (NIR + Red)
        if red_arr is not None and nir_arr is not None and len(red_arr) > 0 and len(nir_arr) > 0:
            ndvi_val = np.nanmean((nir_arr - red_arr) / (nir_arr + red_arr + 1e-8))
            indices['ndvi'] = float(ndvi_val) if not np.isnan(ndvi_val) else 0.0
        else:
            indices['ndvi'] = 0.0
        
        # NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        if nir_arr is not None and swir1_arr is not None and len(nir_arr) > 0 and len(swir1_arr) > 0:
            ndmi_val = np.nanmean((nir_arr - swir1_arr) / (nir_arr + swir1_arr + 1e-8))
            indices['ndmi'] = float(ndmi_val) if not np.isnan(ndmi_val) else 0.0
        else:
            indices['ndmi'] = 0.0
        
        # NDWI = (Green - NIR) / (Green + NIR)
        if green_arr is not None and nir_arr is not None and len(green_arr) > 0 and len(nir_arr) > 0:
            ndwi_val = np.nanmean((green_arr - nir_arr) / (green_arr + nir_arr + 1e-8))
            indices['ndwi'] = float(ndwi_val) if not np.isnan(ndwi_val) else 0.0
        else:
            indices['ndwi'] = 0.0
        
        return indices
    
    def process_satellite_data(self, bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Process MODIS data"""
        start_time = time.time()
        
        try:
            # Search for satellite data
            item = self.search_satellite_data(bbox, start_date, end_date)
            if item is None:
                return {"success": False, "error": "no_satellite_item_found", "satellite": self.satellite_id}
            
            # Sign the item
            signed_item = pc_sign(item)
            assets = signed_item.assets
            
            # Get required bands
            band_data = {}
            for band_type, possible_names in self.required_bands.items():
                for name in possible_names:
                    if name in assets:
                        asset_href = assets[name].href
                        clipped = self.clip_band_to_bbox(asset_href, bbox)
                        if clipped is not None:
                            band_data[band_type] = clipped.values[0]
                            break
            
            # Compute indices
            indices = self.compute_indices_from_arrays(
                red_arr=band_data.get('red'),
                nir_arr=band_data.get('nir'),
                swir1_arr=band_data.get('swir1'),
                green_arr=band_data.get('green')
            )
            
            # Map to NPK/SOC
            npk_soc = self.map_indices_to_npk_soc(indices)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "satellite": self.satellite_id,
                "resolution": self.resolution,
                "cloud_coverage": item.properties.get("eo:cloud_cover", 0),
                "acquisition_date": str(item.properties.get("datetime", "")),
                "indices": indices,
                "npk": npk_soc,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error processing MODIS data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "satellite": self.satellite_id,
                "processing_time": time.time() - start_time
            }


class Sentinel1Processor(BaseSatelliteProcessor):
    """Sentinel-1 RTC processor (10m resolution, SAR radar)"""
    
    def __init__(self):
        super().__init__("sentinel-1-rtc", "sentinel-1-rtc", "10m")
        self.required_bands = {
            'vv': ['VV'],
            'vh': ['VH']
        }
    
    def compute_indices_from_arrays(self, vv_arr: np.ndarray = None, vh_arr: np.ndarray = None, **kwargs) -> Dict[str, Any]:
        """Compute vegetation indices from Sentinel-1 SAR radar data"""
        indices = {}
        
        # SAR-specific indices
        if vv_arr is not None and vh_arr is not None:
            # Cross-polarization ratio (VH/VV) - indicates vegetation
            cross_pol_ratio = vh_arr / (vv_arr + 1e-8)
            indices['cross_pol_ratio'] = float(np.nanmean(cross_pol_ratio)) if len(cross_pol_ratio) > 0 else 0.0
            
            # Radar Vegetation Index (RVI) - vegetation indicator
            rvi = 4 * vh_arr / (vv_arr + vh_arr + 1e-8)
            indices['rvi'] = float(np.nanmean(rvi)) if len(rvi) > 0 else 0.0
            
            # Convert SAR to optical-like indices for compatibility
            # This is a simplified conversion - real SAR processing is more complex
            indices['ndvi'] = min(max(indices['rvi'] * 0.8, 0), 1)  # Scale RVI to NDVI range
            indices['ndmi'] = min(max(indices['cross_pol_ratio'] * 0.6, 0), 1)  # Scale to NDMI range
        
        return indices
    
    def map_indices_to_npk_soc(self, indices: Dict[str, Any]) -> Dict[str, str]:
        """Map SAR indices to NPK/SOC levels"""
        # SAR-specific thresholds
        npk_soc = {}
        
        # Use RVI for vegetation assessment
        rvi = indices.get('rvi', 0.3)
        if rvi < 0.2:
            nitrogen = 'low'
            potassium = 'low'
        elif rvi < 0.4:
            nitrogen = 'medium'
            potassium = 'medium'
        else:
            nitrogen = 'high'
            potassium = 'high'
        
        # Use cross-polarization ratio for moisture/phosphorus
        cross_pol = indices.get('cross_pol_ratio', 0.3)
        if cross_pol < 0.2:
            phosphorus = 'low'
            soc = 'low'
        elif cross_pol < 0.4:
            phosphorus = 'medium'
            soc = 'medium'
        else:
            phosphorus = 'high'
            soc = 'high'
        
        return {
            'Nitrogen': nitrogen,
            'Phosphorus': phosphorus,
            'Potassium': potassium,
            'SOC': soc
        }
    
    def process_satellite_data(self, bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Process Sentinel-1 SAR data"""
        start_time = time.time()
        
        try:
            # Search for satellite data (SAR doesn't have cloud cover)
            item = self.search_satellite_data(bbox, start_date, end_date, max_cloud_cover=100)
            if item is None:
                return {"success": False, "error": "no_satellite_item_found", "satellite": self.satellite_id}
            
            # Sign the item
            signed_item = pc_sign(item)
            assets = signed_item.assets
            
            # Get required bands
            band_data = {}
            for band_type, possible_names in self.required_bands.items():
                for name in possible_names:
                    if name in assets:
                        asset_href = assets[name].href
                        clipped = self.clip_band_to_bbox(asset_href, bbox)
                        if clipped is not None:
                            band_data[band_type] = clipped.values[0]
                            break
            
            # Compute SAR indices
            indices = self.compute_indices_from_arrays(
                vv_arr=band_data.get('vv'),
                vh_arr=band_data.get('vh')
            )
            
            # Map to NPK/SOC
            npk_soc = self.map_indices_to_npk_soc(indices)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "satellite": self.satellite_id,
                "resolution": self.resolution,
                "cloud_coverage": 0,  # SAR penetrates clouds
                "acquisition_date": str(item.properties.get("datetime", "")),
                "indices": indices,
                "npk": npk_soc,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error processing Sentinel-1 data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "satellite": self.satellite_id,
                "processing_time": time.time() - start_time
            }


# Factory function to get the appropriate processor
def get_satellite_processor(satellite_id: str) -> BaseSatelliteProcessor:
    """Factory function to get the appropriate satellite processor"""
    processors = {
        "sentinel-2-l2a": Sentinel2Processor,
        "landsat-8-c2-l2": Landsat8Processor,
        "modis-09A1-061": ModisProcessor,
        "modis-09a1-v061": ModisProcessor,  # Keep both for compatibility
        "sentinel-1-rtc": Sentinel1Processor
    }
    
    if satellite_id not in processors:
        raise ValueError(f"Unknown satellite ID: {satellite_id}")
    
    return processors[satellite_id]()
