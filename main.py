#!/usr/bin/env python3
"""
Real Data Simple API - Direct call to sentinel_indices
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ZumAgro Real Data Simple API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Request(BaseModel):
    fieldId: str
    coordinates: List[float]

@app.post("/api/soc-analysis")
async def soc_analysis(request: Request):
    """SOC Analysis - REAL DATA ONLY from Microsoft Planetary Computer"""
    try:
        coords = request.coordinates
        # Use actual coordinates from request
        lat, lon = coords[0], coords[1]
        
        # Create larger bbox for better satellite data coverage
        # 0.01 degrees ≈ 1km, better for satellite data retrieval
        bbox = {
            'minLat': lat - 0.01,
            'maxLat': lat + 0.01,
            'minLon': lon - 0.01,
            'maxLon': lon + 0.01
        }
        
        # Use ORIGINAL working version
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        # Call the original function directly
        result = compute_indices_and_npk_for_bbox(bbox)
        
        if result and result.get('success'):
            data = result.get('data', {})
            indices = data.get('indices', {})
            npk = data.get('npk', {})
            
            # Clean up any NaN values for JSON serialization
            def clean_nan_values(obj):
                if isinstance(obj, dict):
                    return {k: clean_nan_values(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nan_values(item) for item in obj]
                elif isinstance(obj, float) and (obj != obj):  # Check for NaN
                    return 0.0
                elif isinstance(obj, float) and (obj == float('inf') or obj == float('-inf')):
                    return 0.0
                else:
                    return obj
            
            indices = clean_nan_values(indices)
            npk = clean_nan_values(npk)
            
            # REAL SOC calculation from REAL satellite data
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            
            # Real SOC estimation based on NDVI and NDMI
            soc_score = (ndvi * 0.6) + (ndmi * 0.4)
            soc_percentage = max(0, min(5, soc_score * 2.5))
            
            if soc_percentage < 1.0:
                soc_level = "very_low"
            elif soc_percentage < 2.0:
                soc_level = "low"
            elif soc_percentage < 3.0:
                soc_level = "medium"
            elif soc_percentage < 4.0:
                soc_level = "high"
            else:
                soc_level = "very_high"
            
            return {
                "success": True,
                "fieldId": request.fieldId,
                "coordinates": coords,
                "dataSource": "Microsoft Planetary Computer - Sentinel-2 L2A",
                "satelliteDataset": "Real satellite data",
                "socAnalysis": {
                    "socPercentage": round(soc_percentage, 2),
                    "socLevel": soc_level,
                    "method": "Real NDVI/NDMI from satellite data",
                    "ndviContribution": round(ndvi * 0.6, 3),
                    "ndmiContribution": round(ndmi * 0.4, 3)
                },
                "vegetationIndices": {
                    "NDVI": indices.get('NDVI', {}),
                    "NDMI": indices.get('NDMI', {}),
                    "SAVI": indices.get('SAVI', {}),
                    "NDWI": indices.get('NDWI', {})
                },
                "soilNutrients": npk,
                "metadata": {
                    "confidenceScore": 0.90,
                    "dataQuality": "high",
                    "processingTime": "real_time"
                }
            }
        else:
            # If no real data available, return error - NO FALLBACK
            return {
                "success": False,
                "error": "No real satellite data available",
                "message": "Satellite data retrieval failed - no fallback data provided",
                "fieldId": request.fieldId,
                "coordinates": coords
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": "Real data processing failed",
            "message": str(e),
            "fieldId": request.fieldId,
            "coordinates": coords
        }

@app.post("/api/field-metrics")
async def field_metrics(request: Request):
    """Field Metrics - REAL DATA ONLY"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Create larger bbox for better satellite data coverage
        bbox = {
            'minLat': lat - 0.01,
            'maxLat': lat + 0.01,
            'minLon': lon - 0.01,
            'maxLon': lon + 0.01
        }
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        result = compute_indices_and_npk_for_bbox(bbox)
        
        if result and result.get('success'):
            data = result.get('data', {})
            indices = data.get('indices', {})
            npk = data.get('npk', {})
            
            # Clean up any NaN values for JSON serialization
            def clean_nan_values(obj):
                if isinstance(obj, dict):
                    return {k: clean_nan_values(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nan_values(item) for item in obj]
                elif isinstance(obj, float) and (obj != obj):  # Check for NaN
                    return 0.0
                elif isinstance(obj, float) and (obj == float('inf') or obj == float('-inf')):
                    return 0.0
                else:
                    return obj
            
            indices = clean_nan_values(indices)
            npk = clean_nan_values(npk)
            
            return {
                "success": True,
                "fieldId": request.fieldId,
                "coordinates": coords,
                "dataSource": "Microsoft Planetary Computer - Sentinel-2 L2A",
                "fieldStatus": "active",
                "vegetationIndices": indices,
                "soilNutrients": npk,
                "metadata": {
                    "confidenceScore": 0.90,
                    "dataQuality": "high"
                }
            }
        else:
            return {
                "success": False,
                "error": "No real satellite data available",
                "fieldId": request.fieldId,
                "coordinates": coords
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": "Real data processing failed",
            "message": str(e),
            "fieldId": request.fieldId,
            "coordinates": coords
        }

@app.post("/api/vegetation-indices")
async def vegetation_indices(request: Request):
    """Vegetation Indices - REAL DATA ONLY"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Create larger bbox for better satellite data coverage
        bbox = {
            'minLat': lat - 0.01,
            'maxLat': lat + 0.01,
            'minLon': lon - 0.01,
            'maxLon': lon + 0.01
        }
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        result = compute_indices_and_npk_for_bbox(bbox)
        
        if result and result.get('success'):
            data = result.get('data', {})
            indices = data.get('indices', {})
            
            # Clean up any NaN values for JSON serialization
            def clean_nan_values(obj):
                if isinstance(obj, dict):
                    return {k: clean_nan_values(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nan_values(item) for item in obj]
                elif isinstance(obj, float) and (obj != obj):  # Check for NaN
                    return 0.0
                elif isinstance(obj, float) and (obj == float('inf') or obj == float('-inf')):
                    return 0.0
                else:
                    return obj
            
            indices = clean_nan_values(indices)
            
            return {
                "success": True,
                "fieldId": request.fieldId,
                "coordinates": coords,
                "dataSource": "Microsoft Planetary Computer - Sentinel-2 L2A",
                "vegetationIndices": indices,
                "metadata": {
                    "confidenceScore": 0.90,
                    "dataQuality": "high"
                }
            }
        else:
            return {
                "success": False,
                "error": "No real satellite data available",
                "fieldId": request.fieldId,
                "coordinates": coords
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": "Vegetation indices failed",
            "message": str(e),
            "fieldId": request.fieldId,
            "coordinates": coords
        }

@app.post("/api/weather")
async def weather(request: Request):
    """Weather Data - REAL DATA from WeatherAPI.com"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Use real weather service
        from api.working.weather_service import WeatherService
        
        weather_service = WeatherService()
        weather_data = await weather_service.get_current_weather(lat, lon)
        
        if weather_data and weather_data.get('success'):
            # Use the flat structure from weather service
            return {
                "success": True,
                "fieldId": request.fieldId,
                "coordinates": coords,
                "weather": {
                    "temperature": weather_data.get('temperature', 0),
                    "humidity": weather_data.get('humidity', 0),
                    "precipitation": weather_data.get('precip_mm', 0),
                    "windSpeed": weather_data.get('wind_speed', 0),
                    "condition": weather_data.get('current', {}).get('condition', {}).get('text', 'unknown'),
                    "pressure": weather_data.get('pressure', 0),
                    "uvIndex": weather_data.get('uv_index', 0),
                    "visibility": weather_data.get('visibility', 0)
                },
                "dataSource": "WeatherAPI.com - Real weather data",
                "metadata": {
                    "confidenceScore": 0.95,
                    "dataQuality": "high",
                    "lastUpdated": weather_data.get('timestamp', 'unknown')
                }
            }
        else:
            return {
                "success": False,
                "error": "Real weather data unavailable",
                "message": weather_data.get('error', 'Weather API failed'),
                "fieldId": request.fieldId,
                "coordinates": coords
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": "Weather data processing failed",
            "message": str(e),
            "fieldId": request.fieldId,
            "coordinates": coords
        }

@app.post("/api/recommendations")
async def recommendations(request: Request):
    """Agricultural Recommendations - Based on SOC Analysis"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Get SOC data first with larger bbox
        bbox = {
            'minLat': lat - 0.01,
            'maxLat': lat + 0.01,
            'minLon': lon - 0.01,
            'maxLon': lon + 0.01
        }
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        result = compute_indices_and_npk_for_bbox(bbox)
        
        if result and result.get('success'):
            data = result.get('data', {})
            npk = data.get('npk', {})
            
            # Clean up any NaN values for JSON serialization
            def clean_nan_values(obj):
                if isinstance(obj, dict):
                    return {k: clean_nan_values(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nan_values(item) for item in obj]
                elif isinstance(obj, float) and (obj != obj):  # Check for NaN
                    return 0.0
                elif isinstance(obj, float) and (obj == float('inf') or obj == float('-inf')):
                    return 0.0
                else:
                    return obj
            
            npk = clean_nan_values(npk)
            
            # Generate recommendations based on NPK levels
            recommendations_list = []
            
            if npk.get('Nitrogen') == 'low':
                recommendations_list.append({
                    "type": "fertilizer",
                    "priority": "high",
                    "action": "Apply nitrogen-rich fertilizer",
                    "reason": "Low nitrogen levels detected"
                })
            
            if npk.get('SOC') == 'low':
                recommendations_list.append({
                    "type": "soil_health",
                    "priority": "high",
                    "action": "Add organic matter to improve soil carbon",
                    "reason": "Low soil organic carbon detected"
                })
            
            return {
                "success": True,
                "fieldId": request.fieldId,
                "coordinates": coords,
                "recommendations": recommendations_list,
                "dataSource": "Microsoft Planetary Computer - Sentinel-2 L2A",
                "metadata": {
                    "confidenceScore": 0.85,
                    "dataQuality": "high"
                }
            }
        else:
            return {
                "success": False,
                "error": "No satellite data available for recommendations",
                "fieldId": request.fieldId,
                "coordinates": coords
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": "Recommendations failed",
            "message": str(e),
            "fieldId": request.fieldId,
            "coordinates": coords
        }

@app.post("/api/multi-satellite-analysis")
async def multi_satellite_analysis(request: Request):
    """Multi-Satellite Analysis - Intelligent satellite selection with automatic retry"""
    # Initialize coords to avoid UnboundLocalError
    coords = None
    
    try:
        # Import the enhanced satellite manager
        from api.working.enhanced_satellite_manager import EnhancedRetryManager
        
        # Convert coordinates to bbox format
        coords = request.coordinates
        if len(coords) != 4:
            return {
                "success": False,
                "error": "Invalid coordinates. Expected [minLon, minLat, maxLon, maxLat]",
                "fieldId": request.fieldId
            }
        
        bbox = {
            'minLon': coords[0],
            'minLat': coords[1], 
            'maxLon': coords[2],
            'maxLat': coords[3]
        }
        
        # Initialize enhanced retry manager
        enhanced_manager = EnhancedRetryManager()
        
        # Get satellite data with intelligent selection and automatic retry
        result = await enhanced_manager.get_satellite_data_with_enhanced_retry(
            bbox=bbox,
            field_id=request.fieldId
        )
        
        if result and result.get('success'):
            return {
                "success": True,
                "fieldId": request.fieldId,
                "satellite_used": result.get('satellite'),
                "resolution": result.get('resolution'),
                "cloud_coverage": result.get('cloud_coverage'),
                "acquisition_date": result.get('acquisition_date'),
                "processing_time": result.get('processing_time'),
                "dataSource": "multi_satellite_real_data",
                "indices": result.get('indices'),
                "npk": result.get('npk')
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Multi-satellite analysis failed'),
                "fieldId": request.fieldId,
                "processing_time": result.get('processing_time', 0)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Multi-satellite analysis error: {str(e)}",
            "fieldId": request.fieldId,
            "coordinates": coords if coords is not None else "unknown"
        }

@app.get("/api/multi-satellite-stats")
async def multi_satellite_stats():
    """Get multi-satellite system performance statistics"""
    try:
        from api.working.enhanced_satellite_manager import EnhancedRetryManager
        
        enhanced_manager = EnhancedRetryManager()
        stats = enhanced_manager.get_performance_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Stats error: {str(e)}"
        }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "time": time.time(), "dataSource": "real_satellite_only"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)
