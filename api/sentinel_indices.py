# sentinel_indices.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pystac_client
import planetary_computer as pc
import rioxarray
import xarray as xr
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger("sentinel_indices")
logger.setLevel(logging.INFO)

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

def fetch_best_sentinel_item(bbox: Dict[str, float],
                             start_date: datetime = None,
                             end_date: datetime = None,
                             max_cloud_cover: int = 80):
    """Search Planetary Computer STAC for the best sentinel-2 L2A item (lowest cloud)"""
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=90)  # default 90 days

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
        datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
        query={"eo:cloud_cover": {"lt": max_cloud_cover}},
        limit=50
    )
    items = list(search.items())
    if not items:
        return None
    # choose lowest cloud cover and most recent preference
    items_sorted = sorted(items, key=lambda it: (it.properties.get('eo:cloud_cover', 100), -datetime.fromisoformat(it.properties.get('datetime')).timestamp()))
    return items_sorted[0]

def clip_band_to_bbox(asset_href: str, bbox: Dict[str, float]) -> xr.DataArray:
    """
    Open and clip the band asset using rioxarray.clip_box
    Returns a 2D DataArray (band, y, x) -> squeeze to 2D
    """
    try:
        signed_href = pc.sign(asset_href)
        with rioxarray.open_rasterio(signed_href, masked=True) as ds:
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
        # Flatten and mask invalids - ensure all arrays have same valid pixels
        def _prep(a):
            if a is None:
                return np.array([])
            a = np.asarray(a).astype(np.float64)
            mask = np.isfinite(a)
            return a[mask]
        
        # Get all arrays first
        red = _prep(red_arr)
        nir = _prep(nir_arr)
        swir1 = _prep(swir1_arr)
        green = _prep(green_arr)
        
        # Find the minimum size to ensure all arrays have same length
        sizes = [arr.size for arr in [red, nir, swir1, green] if arr.size > 0]
        if not sizes:
            return {}
        
        min_size = min(sizes)
        
        # Truncate all arrays to the same size
        if red.size > min_size:
            red = red[:min_size]
        if nir.size > min_size:
            nir = nir[:min_size]
        if swir1.size > min_size:
            swir1 = swir1[:min_size]
        if green.size > min_size:
            green = green[:min_size]

        # NDVI
        if red.size and nir.size:
            logger.info(f"🔍 DEBUG: Red array shape: {red.shape}, NIR array shape: {nir.shape}")
            logger.info(f"🔍 DEBUG: Red min/max: {np.nanmin(red)}/{np.nanmax(red)}, NIR min/max: {np.nanmin(nir)}/{np.nanmax(nir)}")
            denom = nir + red
            valid = denom != 0
            ndvi = np.zeros_like(denom, dtype=np.float64)
            ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]
            logger.info(f"🔍 DEBUG: NDVI min/max: {np.nanmin(ndvi)}/{np.nanmax(ndvi)}, valid pixels: {np.sum(valid)}")
            out['NDVI'] = {
                'mean': float(np.nanmean(ndvi)),
                'median': float(np.nanmedian(ndvi)),
                'count': int(np.sum(valid))
            }
        else:
            logger.warning(f"🔍 DEBUG: Red or NIR array is empty - Red: {red.size if red is not None else 'None'}, NIR: {nir.size if nir is not None else 'None'}")
            out['NDVI'] = {'mean': None, 'median': None, 'count': 0}

        # NDMI
        if nir.size and swir1.size:
            denom = nir + swir1
            valid = denom != 0
            ndmi = np.zeros_like(denom, dtype=np.float64)
            ndmi[valid] = (nir[valid] - swir1[valid]) / denom[valid]
            out['NDMI'] = {
                'mean': float(np.nanmean(ndmi)),
                'median': float(np.nanmedian(ndmi)),
                'count': int(np.sum(valid))
            }
        else:
            out['NDMI'] = {'mean': None, 'median': None, 'count': 0}

        # SAVI (L = 0.5)
        L = 0.5
        if red.size and nir.size:
            denom = nir + red + L
            valid = denom != 0
            savi = np.zeros_like(denom, dtype=np.float64)
            savi[valid] = ((nir[valid] - red[valid]) * (1 + L)) / denom[valid]
            out['SAVI'] = {
                'mean': float(np.nanmean(savi)),
                'median': float(np.nanmedian(savi)),
                'count': int(np.sum(valid))
            }
        else:
            out['SAVI'] = {'mean': None, 'median': None, 'count': 0}

        # NDWI (Green - NIR)
        if green.size and nir.size:
            denom = green + nir
            valid = denom != 0
            ndwi = np.zeros_like(denom, dtype=np.float64)
            ndwi[valid] = (green[valid] - nir[valid]) / denom[valid]
            out['NDWI'] = {
                'mean': float(np.nanmean(ndwi)),
                'median': float(np.nanmedian(ndwi)),
                'count': int(np.sum(valid))
            }
        else:
            out['NDWI'] = {'mean': None, 'median': None, 'count': 0}

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

def map_indices_to_npk_soc(indices: Dict[str, Any]) -> Dict[str, str]:
    """
    Basic rule-based mapping from indices to qualitative N/P/K/SOC.
    NOTE: This is a provisional conversion meant for B2B "relative" estimates.
    For production, train ML models using ground truth.
    """
    ndvi = indices.get('NDVI', {}).get('mean')
    ndmi = indices.get('NDMI', {}).get('mean')
    savi = indices.get('SAVI', {}).get('mean')
    ndwi = indices.get('NDWI', {}).get('mean')

    # Nitrogen proxy: NDVI primary
    nitrogen = qualitative_from_index(ndvi, "NDVI")

    # Potassium proxy: combination of NDMI (moisture) and NDVI (vigour)
    if ndmi is None:
        potassium = qualitative_from_index(ndvi, "NDVI")
    else:
        # simple rule: if moisture low and NDVI low -> K low; else combine
        if ndmi < THRESHOLDS['NDMI']['low'] and ndvi < THRESHOLDS['NDVI']['low']:
            potassium = "low"
        else:
            # average-like decision
            potassium = "high" if (ndmi > THRESHOLDS['NDMI']['medium'] and ndvi > THRESHOLDS['NDVI']['medium']) else "medium"

    # Phosphorus proxy: deduced from NDVI trend & moisture stress (weak direct proxy)
    if ndvi is None or ndwi is None:
        phosphorus = qualitative_from_index(ndvi, "NDVI")
    else:
        if ndvi < THRESHOLDS['NDVI']['low'] and ndwi < THRESHOLDS['NDWI']['low']:
            phosphorus = "low"
        else:
            phosphorus = "medium" if ndvi < THRESHOLDS['NDVI']['medium'] else "high"

    # SOC proxy: combine NDVI, SAVI and NDMI. SAVI helps for sparse veget.
    soc_score = 0.0
    components = 0
    if ndvi is not None:
        soc_score += ndvi
        components += 1
    if savi is not None:
        soc_score += savi
        components += 1
    if ndmi is not None:
        soc_score += (ndmi * 0.8)  # moisture less weight
        components += 1
    if components == 0:
        soc_est = "unknown"
    else:
        avg = soc_score / components
        soc_est = qualitative_from_index(avg, "NDVI")  # reuse NDVI thresholds for SOC qualitative bins

    return {
        "Nitrogen": nitrogen,
        "Phosphorus": phosphorus,
        "Potassium": potassium,
        "SOC": soc_est
    }

def compute_indices_and_npk_for_bbox(bbox: Dict[str, float],
                                     start_date: datetime = None,
                                     end_date: datetime = None) -> Dict[str, Any]:
    """
    End-to-end: find best sentinel item, clip bands, compute indices, map to NPK/SOC.
    Returns structured payload suitable for B2B API responses.
    """
    item = fetch_best_sentinel_item(bbox, start_date=start_date, end_date=end_date, max_cloud_cover=80)
    if item is None:
        return {"success": False, "error": "no_satellite_item_found", "satelliteItem": None}

    try:
        signed_item = pc.sign(item)
        # Collect assets we need; fallback if some bands missing
        assets = signed_item.assets
        # required: B04 (red), B08 (nir)
        red_asset = assets.get("B04") or assets.get("B04_20m") or assets.get("red")
        nir_asset = assets.get("B08") or assets.get("nir")
        swir1_asset = assets.get("B11")
        green_asset = assets.get("B03")

        if not red_asset or not nir_asset:
            return {"success": False, "error": "required_bands_missing", "satelliteItem": item.id}

        # Prepare band assets for parallel processing
        band_assets = {
            'red': red_asset.href,
            'nir': nir_asset.href,
            'swir1': swir1_asset.href if swir1_asset else None,
            'green': green_asset.href if green_asset else None
        }
        
        # Process bands in parallel for better performance
        logger.info("🚀 Starting parallel band processing")
        start_time = datetime.utcnow()
        band_data = clip_bands_parallel(band_assets, bbox, max_workers=4)
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
                return None
            if arr.shape == target_shape:
                return arr
            # Ensure we don't exceed array bounds
            rows_to_take = min(target_shape[0], arr.shape[0])
            cols_to_take = min(target_shape[1], arr.shape[1])
            return arr[:rows_to_take, :cols_to_take]

        red_np = _resample_to_shape(red_np, target_shape)
        nir_np = _resample_to_shape(nir_np, target_shape)
        swir1_np = _resample_to_shape(swir1_np, target_shape)
        green_np = _resample_to_shape(green_np, target_shape)

        logger.info(f"Final shapes - Red: {red_np.shape if red_np is not None else None}, NIR: {nir_np.shape if nir_np is not None else None}, SWIR1: {swir1_np.shape if swir1_np is not None else None}, Green: {green_np.shape if green_np is not None else None}")

        indices = compute_indices_from_arrays(red_np, nir_np, swir1_np, green_np)
        npk = map_indices_to_npk_soc(indices)

        response = {
            "success": True,
            "satelliteItem": item.id,
            "imageDate": item.properties.get("datetime"),
            "cloudCover": item.properties.get("eo:cloud_cover"),
            "indices": indices,
            "npk": npk,
            "metadata": {
                "provider": "Microsoft Planetary Computer",
                "satellite": "Sentinel-2 L2A",
                "fetchedAt": datetime.utcnow().isoformat()
            }
        }
        return response

    except Exception as e:
        logger.exception("Error computing indices and npk")
        return {"success": False, "error": str(e), "satelliteItem": item.id}
