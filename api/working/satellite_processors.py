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
import xarray as xr
import numpy as np
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
            -datetime.fromisoformat(str(it.properties.get('datetime', '2023-01-01'))).timestamp()
        ))
        return items_sorted[0]
    
    def clip_band_to_bbox(self, asset_href: str, bbox: Dict[str, float]) -> xr.DataArray:
        """Clip satellite band to bounding box"""
        try:
            # Use rioxarray for modern xarray compatibility
            import rioxarray as rio
            da = rio.open_rasterio(asset_href)
            clipped = da.sel(
                x=slice(bbox['minLon'], bbox['maxLon']),
                y=slice(bbox['maxLat'], bbox['minLat'])  # Note: y is inverted
            )
            return clipped
        except Exception as e:
            self.logger.error(f"Error clipping band {asset_href}: {str(e)}")
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
        """Compute vegetation indices from Sentinel-2 bands"""
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
            
            # Get required bands
            band_data = {}
            for band_type, possible_names in self.required_bands.items():
                for name in possible_names:
                    if name in assets:
                        asset_href = assets[name].href
                        clipped = self.clip_band_to_bbox(asset_href, bbox)
                        if clipped is not None:
                            band_data[band_type] = clipped.values[0]  # Remove band dimension
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
        super().__init__("landsat-8-c2-l2", "landsat-8-c2-l2", "30m")
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
        """Compute vegetation indices from Landsat-8 bands (same as Sentinel-2)"""
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
        super().__init__("modis-09a1-v061", "modis-09a1-v061", "250m")
        self.required_bands = {
            'red': ['B01'],
            'nir': ['B02'],
            'swir1': ['B06'],
            'swir2': ['B07'],
            'green': ['B04'],
            'blue': ['B03']
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
        "modis-09a1-v061": ModisProcessor,
        "sentinel-1-rtc": Sentinel1Processor
    }
    
    if satellite_id not in processors:
        raise ValueError(f"Unknown satellite ID: {satellite_id}")
    
    return processors[satellite_id]()
