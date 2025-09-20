"""
Clean FastAPI Application - Only Working APIs
Agricultural Intelligence Platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import sys
import os
from datetime import datetime

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Import only working handlers
import importlib.util

def load_handler(module_name, file_path):
    """Load handler from a Python file"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.handler

# Load only working handlers
b2b_npk_handler = load_handler("b2b_npk_analysis", "api/b2b_npk_analysis.py")
weather_handler = load_handler("weather_handler", "api/weather_handler.py")
recommendations_handler = load_handler("recommendations_handler", "api/recommendations_handler.py")
trends_handler = load_handler("trends_handler", "api/trends_handler.py")
crop_health_handler = load_handler("crop_health_handler", "api/crop_health_handler.py")
terrain_handler = load_handler("terrain_handler", "api/terrain_handler.py")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ZumAgro Python API",
    description="Clean Agricultural Intelligence API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class NPKAnalysisRequest(BaseModel):
    fieldId: str
    coordinates: List[List[float]]  # Simplified: [[lon, lat], [lon, lat], ...]
    metric: str = "npk"

class WeatherRequest(BaseModel):
    fieldId: str
    coordinates: List[float]  # [lat, lon]
    days: int = 7

class RecommendationsRequest(BaseModel):
    fieldId: str
    coordinates: List[float]  # [lat, lon]
    fieldMetrics: Optional[Dict[str, Any]] = None
    weatherData: Optional[Dict[str, Any]] = None

class TrendsRequest(BaseModel):
    fieldId: str
    coordinates: List[float]  # [lat, lon]
    timePeriod: str = "30d"  # "7d", "30d", "90d", "1y"
    analysisType: str = "comprehensive"  # "comprehensive", "vegetation", "weather", "yield"

class CropHealthRequest(BaseModel):
    fieldId: str
    coordinates: List[float]  # [lat, lon]
    cropType: str = "general"  # "wheat", "rice", "corn", "soybean", "general"

class TerrainRequest(BaseModel):
    fieldId: str
    coordinates: List[float]  # [lat, lon]

# Mock request class for compatibility
class MockRequest:
    def __init__(self, method: str, json_data: Dict[str, Any]):
        self.method = method
        self._json_data = json_data
    
    def get_json(self):
        return self._json_data

# API Routes
@app.get("/")
async def root():
    """API Documentation and Health Check"""
    return {
        "message": "ZumAgro Python API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
                "/api/field-metrics",
                "/api/weather",
                "/api/weather/alerts",
                "/api/weather/historical",
                "/api/recommendations",
                "/api/recommendations/fertilizer",
                "/api/recommendations/irrigation",
                "/api/recommendations/crop-health",
                "/api/recommendations/risk-alerts",
                "/api/trends",
                "/api/trends/vegetation",
                "/api/trends/weather",
                "/api/trends/performance",
                "/api/trends/seasonal",
                "/api/trends/anomalies",
                "/api/crop-health",
                "/api/crop-health/stress",
                "/api/crop-health/growth-stage",
                "/api/crop-health/quality",
                "/api/terrain/elevation",
                "/api/terrain/land-cover",
                "/api/terrain/comprehensive"
            ],
        "description": "Clean, minimal API for agricultural intelligence",
        "features": [
            "Complete Field Metrics Analysis",
            "NPK + SOC + Health + Indices",
            "Complete Weather Integration",
            "Actionable Recommendations",
            "Fertilizer & Irrigation Advice",
            "Advanced Crop Health Monitoring",
            "Real-time Stress Detection",
            "Growth Stage Analysis",
            "Crop Quality Assessment",
            "Disease & Pest Risk Analysis",
            "Risk Alerts & Warnings",
            "Historical Trends Analysis",
            "Seasonal Pattern Recognition",
            "Anomaly Detection",
            "Performance Tracking",
            "Real-time Processing",
            "Intelligent Caching",
            "Terrain Elevation Analysis",
            "Land Cover Classification",
            "Agricultural Suitability Assessment",
            "Drainage Analysis",
            "Slope Analysis"
        ]
    }

@app.post("/api/field-metrics")
async def field_metrics(request: NPKAnalysisRequest):
    """Complete Field Metrics Analysis - NPK + SOC + Health + Indices with satellite data"""
    try:
        logger.info(f"🚀 [FASTAPI] Field Metrics Request - Field: {request.fieldId}")
        logger.info(f"🚀 [FASTAPI] Coordinates: {len(request.coordinates)} coordinate arrays")
        
        # Convert coordinates to the format expected by B2B handler
        coordinates = request.coordinates
        if coordinates and len(coordinates) > 0:
            # Take the first coordinate pair [lon, lat]
            coordinates = coordinates[0] if coordinates[0] else [0, 0]
        else:
            coordinates = [0, 0]
        
        mock_request = MockRequest("POST", {
            "fieldId": request.fieldId,
            "coordinates": coordinates,
            "metric": request.metric
        })
        
        response = b2b_npk_handler(mock_request)
        
        if response["statusCode"] == 200:
            logger.info(f"🚀 [FASTAPI] Field Metrics Success - Field: {request.fieldId}")
            return response["body"]
        else:
            logger.error(f"🚀 [FASTAPI] Field Metrics Failed - Field: {request.fieldId}")
            raise HTTPException(status_code=response["statusCode"], detail=response["body"])
            
    except Exception as e:
        logger.error(f"🚀 [FASTAPI] Field Metrics Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Weather API - Complete Implementation
@app.post("/api/weather")
async def weather_data(request: WeatherRequest):
    """Complete Weather Data - Current conditions, forecast, and agricultural insights"""
    try:
        logger.info(f"🌤️ [FASTAPI] Weather Request - Field: {request.fieldId}")
        logger.info(f"🌤️ [FASTAPI] Coordinates: {request.coordinates}, Days: {request.days}")
        
        response = await weather_handler.get_field_weather(
            request.fieldId, 
            request.coordinates, 
            request.days
        )
        
        logger.info(f"🌤️ [FASTAPI] Weather Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌤️ [FASTAPI] Weather Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather/alerts")
async def weather_alerts(request: WeatherRequest):
    """Weather Alerts and Warnings for Field"""
    try:
        logger.info(f"🌤️ [FASTAPI] Weather Alerts Request - Field: {request.fieldId}")
        
        response = await weather_handler.get_weather_alerts(
            request.fieldId, 
            request.coordinates
        )
        
        logger.info(f"🌤️ [FASTAPI] Weather Alerts Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌤️ [FASTAPI] Weather Alerts Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather/historical")
async def historical_weather(request: WeatherRequest, date: str):
    """Historical Weather Data for Field"""
    try:
        logger.info(f"🌤️ [FASTAPI] Historical Weather Request - Field: {request.fieldId}, Date: {date}")
        
        response = await weather_handler.get_historical_weather(
            request.fieldId, 
            request.coordinates, 
            date
        )
        
        logger.info(f"🌤️ [FASTAPI] Historical Weather Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌤️ [FASTAPI] Historical Weather Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Recommendations API - Complete Implementation
@app.post("/api/recommendations")
async def field_recommendations(request: RecommendationsRequest):
    """Complete Field Recommendations - Fertilizer, Irrigation, Crop Health, Timing, and Risk Alerts"""
    try:
        logger.info(f"🌱 [FASTAPI] Recommendations Request - Field: {request.fieldId}")
        logger.info(f"🌱 [FASTAPI] Coordinates: {request.coordinates}")
        
        # If field metrics and weather data not provided, fetch them
        field_metrics = request.fieldMetrics
        weather_data = request.weatherData
        
        if not field_metrics:
            # Fetch field metrics
            mock_request = MockRequest("POST", {
                "fieldId": request.fieldId,
                "coordinates": [request.coordinates[1], request.coordinates[0]],  # Convert [lat,lon] to [lon,lat]
                "metric": "npk"
            })
            field_response = b2b_npk_handler(mock_request)
            if field_response["statusCode"] == 200:
                field_metrics = field_response["body"]
            else:
                field_metrics = {"npk": {}, "indices": {}}
        
        if not weather_data:
            # Fetch weather data
            weather_data = await weather_handler.get_field_weather(
                request.fieldId, 
                request.coordinates, 
                7
            )
        
        response = await recommendations_handler.get_field_recommendations(
            request.fieldId,
            field_metrics,
            weather_data,
            request.coordinates
        )
        
        logger.info(f"🌱 [FASTAPI] Recommendations Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Recommendations Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/fertilizer")
async def fertilizer_recommendations(request: RecommendationsRequest):
    """Fertilizer-specific Recommendations based on NPK analysis"""
    try:
        logger.info(f"🌱 [FASTAPI] Fertilizer Recommendations Request - Field: {request.fieldId}")
        
        # Get field metrics if not provided
        field_metrics = request.fieldMetrics
        if not field_metrics:
            mock_request = MockRequest("POST", {
                "fieldId": request.fieldId,
                "coordinates": [request.coordinates[1], request.coordinates[0]],
                "metric": "npk"
            })
            field_response = b2b_npk_handler(mock_request)
            if field_response["statusCode"] == 200:
                field_metrics = field_response["body"]
            else:
                field_metrics = {"npk": {}, "indices": {}}
        
        npk_data = field_metrics.get("npk", {})
        indices = field_metrics.get("indices", {})
        
        response = await recommendations_handler.get_fertilizer_recommendations(
            request.fieldId,
            npk_data,
            indices
        )
        
        logger.info(f"🌱 [FASTAPI] Fertilizer Recommendations Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Fertilizer Recommendations Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/irrigation")
async def irrigation_recommendations(request: RecommendationsRequest):
    """Irrigation-specific Recommendations based on weather and soil moisture"""
    try:
        logger.info(f"🌱 [FASTAPI] Irrigation Recommendations Request - Field: {request.fieldId}")
        
        # Get weather data if not provided
        weather_data = request.weatherData
        if not weather_data:
            weather_data = await weather_handler.get_field_weather(
                request.fieldId, 
                request.coordinates, 
                7
            )
        
        # Get field metrics for indices
        field_metrics = request.fieldMetrics
        if not field_metrics:
            mock_request = MockRequest("POST", {
                "fieldId": request.fieldId,
                "coordinates": [request.coordinates[1], request.coordinates[0]],
                "metric": "npk"
            })
            field_response = b2b_npk_handler(mock_request)
            if field_response["statusCode"] == 200:
                field_metrics = field_response["body"]
            else:
                field_metrics = {"indices": {}}
        
        indices = field_metrics.get("indices", {})
        
        response = await recommendations_handler.get_irrigation_recommendations(
            request.fieldId,
            weather_data,
            indices
        )
        
        logger.info(f"🌱 [FASTAPI] Irrigation Recommendations Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Irrigation Recommendations Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/crop-health")
async def crop_health_recommendations(request: RecommendationsRequest):
    """Crop Health Recommendations based on vegetation indices and weather"""
    try:
        logger.info(f"🌱 [FASTAPI] Crop Health Recommendations Request - Field: {request.fieldId}")
        
        # Get weather data if not provided
        weather_data = request.weatherData
        if not weather_data:
            weather_data = await weather_handler.get_field_weather(
                request.fieldId, 
                request.coordinates, 
                7
            )
        
        # Get field metrics for indices
        field_metrics = request.fieldMetrics
        if not field_metrics:
            mock_request = MockRequest("POST", {
                "fieldId": request.fieldId,
                "coordinates": [request.coordinates[1], request.coordinates[0]],
                "metric": "npk"
            })
            field_response = b2b_npk_handler(mock_request)
            if field_response["statusCode"] == 200:
                field_metrics = field_response["body"]
            else:
                field_metrics = {"indices": {}}
        
        indices = field_metrics.get("indices", {})
        
        response = await recommendations_handler.get_crop_health_recommendations(
            request.fieldId,
            indices,
            weather_data
        )
        
        logger.info(f"🌱 [FASTAPI] Crop Health Recommendations Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Crop Health Recommendations Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/risk-alerts")
async def risk_alerts(request: RecommendationsRequest):
    """Risk Alerts and Warnings for Field"""
    try:
        logger.info(f"🌱 [FASTAPI] Risk Alerts Request - Field: {request.fieldId}")
        
        # Get weather data if not provided
        weather_data = request.weatherData
        if not weather_data:
            weather_data = await weather_handler.get_field_weather(
                request.fieldId, 
                request.coordinates, 
                7
            )
        
        # Get field metrics for indices
        field_metrics = request.fieldMetrics
        if not field_metrics:
            mock_request = MockRequest("POST", {
                "fieldId": request.fieldId,
                "coordinates": [request.coordinates[1], request.coordinates[0]],
                "metric": "npk"
            })
            field_response = b2b_npk_handler(mock_request)
            if field_response["statusCode"] == 200:
                field_metrics = field_response["body"]
            else:
                field_metrics = {"indices": {}}
        
        indices = field_metrics.get("indices", {})
        
        response = await recommendations_handler.get_risk_alerts(
            request.fieldId,
            weather_data,
            indices
        )
        
        logger.info(f"🌱 [FASTAPI] Risk Alerts Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Risk Alerts Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Trends API - Complete Implementation
@app.post("/api/trends")
async def field_trends(request: TrendsRequest):
    """Complete Field Trends Analysis - Historical data, patterns, and predictive insights"""
    try:
        logger.info(f"📈 [FASTAPI] Trends Request - Field: {request.fieldId}")
        logger.info(f"📈 [FASTAPI] Period: {request.timePeriod}, Type: {request.analysisType}")
        
        response = await trends_handler.get_field_trends(
            request.fieldId,
            request.coordinates,
            request.timePeriod,
            request.analysisType
        )
        
        logger.info(f"📈 [FASTAPI] Trends Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Trends Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/vegetation")
async def vegetation_trends(request: TrendsRequest):
    """Vegetation-specific Trends Analysis - NDVI, NDMI, SAVI, NDWI over time"""
    try:
        logger.info(f"📈 [FASTAPI] Vegetation Trends Request - Field: {request.fieldId}")
        
        response = await trends_handler.get_vegetation_trends(
            request.fieldId,
            request.coordinates,
            request.timePeriod
        )
        
        logger.info(f"📈 [FASTAPI] Vegetation Trends Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Vegetation Trends Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/weather")
async def weather_trends(request: TrendsRequest):
    """Weather-specific Trends Analysis - Temperature, humidity, precipitation patterns"""
    try:
        logger.info(f"📈 [FASTAPI] Weather Trends Request - Field: {request.fieldId}")
        
        response = await trends_handler.get_weather_trends(
            request.fieldId,
            request.coordinates,
            request.timePeriod
        )
        
        logger.info(f"📈 [FASTAPI] Weather Trends Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Weather Trends Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/performance")
async def performance_trends(request: TrendsRequest):
    """Performance-specific Trends Analysis - Yield, health, efficiency over time"""
    try:
        logger.info(f"📈 [FASTAPI] Performance Trends Request - Field: {request.fieldId}")
        
        response = await trends_handler.get_performance_trends(
            request.fieldId,
            request.coordinates,
            request.timePeriod
        )
        
        logger.info(f"📈 [FASTAPI] Performance Trends Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Performance Trends Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/seasonal")
async def seasonal_analysis(request: TrendsRequest):
    """Seasonal Analysis - Compare current season with historical patterns"""
    try:
        logger.info(f"📈 [FASTAPI] Seasonal Analysis Request - Field: {request.fieldId}")
        
        response = await trends_handler.get_seasonal_analysis(
            request.fieldId,
            request.coordinates,
            request.timePeriod
        )
        
        logger.info(f"📈 [FASTAPI] Seasonal Analysis Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Seasonal Analysis Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/anomalies")
async def anomaly_detection(request: TrendsRequest):
    """Anomaly Detection - Identify unusual patterns and outliers in field data"""
    try:
        logger.info(f"📈 [FASTAPI] Anomaly Detection Request - Field: {request.fieldId}")
        
        response = await trends_handler.get_anomaly_detection(
            request.fieldId,
            request.coordinates,
            request.timePeriod
        )
        
        logger.info(f"📈 [FASTAPI] Anomaly Detection Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Anomaly Detection Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Crop Health Monitoring API Endpoints
@app.post("/api/crop-health")
async def crop_health_analysis(request: CropHealthRequest):
    """Crop Health Analysis - Comprehensive crop health monitoring using satellite data"""
    try:
        logger.info(f"🌱 [FASTAPI] Crop Health Request - Field: {request.fieldId}")
        logger.info(f"🌱 [FASTAPI] Crop Type: {request.cropType}")
        
        response = await crop_health_handler.get_crop_health(
            request.fieldId,
            request.coordinates,
            request.cropType
        )
        
        logger.info(f"🌱 [FASTAPI] Crop Health Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Crop Health Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crop-health/stress")
async def crop_stress_analysis(request: CropHealthRequest):
    """Crop Stress Analysis - Detailed stress monitoring and risk assessment"""
    try:
        logger.info(f"🌱 [FASTAPI] Crop Stress Request - Field: {request.fieldId}")
        
        response = await crop_health_handler.get_crop_stress(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🌱 [FASTAPI] Crop Stress Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Crop Stress Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crop-health/growth-stage")
async def crop_growth_stage(request: CropHealthRequest):
    """Crop Growth Stage Analysis - Determine current growth stage and development status"""
    try:
        logger.info(f"🌱 [FASTAPI] Growth Stage Request - Field: {request.fieldId}")
        
        response = await crop_health_handler.get_growth_stage(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🌱 [FASTAPI] Growth Stage Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Growth Stage Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crop-health/quality")
async def crop_quality_analysis(request: CropHealthRequest):
    """Crop Quality Analysis - Assess crop quality and harvest readiness"""
    try:
        logger.info(f"🌱 [FASTAPI] Crop Quality Request - Field: {request.fieldId}")
        
        response = await crop_health_handler.get_crop_quality(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🌱 [FASTAPI] Crop Quality Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌱 [FASTAPI] Crop Quality Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Terrain Analysis API Endpoints
@app.post("/api/terrain/elevation")
async def elevation_analysis(request: TerrainRequest):
    """Elevation Analysis - Analyze terrain elevation and characteristics"""
    try:
        logger.info(f"🏔️ [FASTAPI] Elevation Request - Field: {request.fieldId}")
        
        response = await terrain_handler.get_elevation_analysis(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🏔️ [FASTAPI] Elevation Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🏔️ [FASTAPI] Elevation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/terrain/land-cover")
async def land_cover_analysis(request: TerrainRequest):
    """Land Cover Analysis - Analyze land use and cover types"""
    try:
        logger.info(f"🌍 [FASTAPI] Land Cover Request - Field: {request.fieldId}")
        
        response = await terrain_handler.get_land_cover_analysis(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🌍 [FASTAPI] Land Cover Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🌍 [FASTAPI] Land Cover Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/terrain/comprehensive")
async def comprehensive_terrain_analysis(request: TerrainRequest):
    """Comprehensive Terrain Analysis - Complete terrain and land cover analysis"""
    try:
        logger.info(f"🏔️🌍 [FASTAPI] Comprehensive Terrain Request - Field: {request.fieldId}")
        
        response = await terrain_handler.get_comprehensive_terrain_analysis(
            request.fieldId,
            request.coordinates
        )
        
        logger.info(f"🏔️🌍 [FASTAPI] Comprehensive Terrain Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🏔️🌍 [FASTAPI] Comprehensive Terrain Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 Starting ZumAgro Python API...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)