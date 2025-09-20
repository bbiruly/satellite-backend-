"""
Clean FastAPI Application - Only Working APIs
Agricultural Intelligence Platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
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

# Load optimized handlers
optimized_field_metrics_handler = load_handler("optimized_field_metrics_handler", "api/optimized_field_metrics_handler.py")
weather_handler = load_handler("weather_handler", "api/weather_handler.py")
recommendations_handler = load_handler("recommendations_handler", "api/recommendations_handler.py")
optimized_trends_handler = load_handler("optimized_trends_handler", "api/optimized_trends_handler.py")
crop_health_handler = load_handler("crop_health_handler", "api/crop_health_handler.py")
optimized_terrain_handler = load_handler("optimized_terrain_handler", "api/optimized_terrain_handler.py")
yield_prediction_handler = load_handler("yield_prediction_handler", "api/yield_prediction_handler.py")

# Import simple validator
from api.simple_validator import simple_validator

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
    coordinates: Union[List[float], List[List[float]], str]  # Flexible: [lat, lon] or [[lat, lon], ...] or "lat,lon"
    metric: str = "npk"

class WeatherRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"
    days: Optional[int] = 7

class RecommendationsRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"
    fieldMetrics: Optional[Dict[str, Any]] = None
    weatherData: Optional[Dict[str, Any]] = None

class TrendsRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"
    timePeriod: Optional[str] = "30d"  # "7d", "30d", "90d", "1y"
    analysisType: Optional[str] = "comprehensive"  # "comprehensive", "vegetation", "weather", "yield"

class CropHealthRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"
    cropType: Optional[str] = "general"  # "wheat", "rice", "corn", "soybean", "general"

class TerrainRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"

class YieldPredictionRequest(BaseModel):
    fieldId: str
    coordinates: Union[List[float], str]  # [lat, lon] or "lat,lon"
    cropType: Optional[str] = "general"  # "rice", "wheat", "maize", "sugarcane", "cotton", "soybean", "general"
    predictionPeriod: Optional[str] = "seasonal"  # "weekly", "monthly", "seasonal", "annual"

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
                "/api/terrain/comprehensive",
                "/api/yield/prediction",
                "/api/yield/confidence",
                "/api/yield/factors",
                "/api/yield/recommendations"
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
            "Slope Analysis",
            "Yield Prediction Analysis",
            "Crop Yield Forecasting",
            "Yield Confidence Scoring",
            "Yield Factor Analysis",
            "Yield Optimization Recommendations"
        ]
    }

@app.post("/api/field-metrics")
async def field_metrics(request: NPKAnalysisRequest):
    """Optimized Field Metrics Analysis - NPK + SOC + Health + Indices for B2B"""
    try:
        logger.info(f"🚀 [FASTAPI] Optimized Field Metrics Request - Field: {request.fieldId}")
        logger.info(f"🚀 [FASTAPI] Coordinates: {len(request.coordinates)} coordinate arrays")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates', 'metric']
            )
            
            # Use cleaned coordinates
            coordinates = cleaned_data['coordinates']
            if isinstance(coordinates, list) and len(coordinates) > 0:
                # Take the first coordinate pair [lon, lat]
                coordinates = coordinates[0] if isinstance(coordinates[0], list) else coordinates
            else:
                coordinates = [0, 0]
                
        except ValueError as e:
            logger.error(f"🚀 [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
        # Use optimized handler for better performance
        response = await optimized_field_metrics_handler.get_field_metrics(
            request.fieldId, 
            coordinates
        )
        
        logger.info(f"🚀 [FASTAPI] Optimized Field Metrics Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🚀 [FASTAPI] Optimized Field Metrics Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Weather API - Complete Implementation
@app.post("/api/weather")
async def weather_data(request: WeatherRequest):
    """Complete Weather Data - Current conditions, forecast, and agricultural insights"""
    try:
        logger.info(f"🌤️ [FASTAPI] Weather Request - Field: {request.fieldId}")
        logger.info(f"🌤️ [FASTAPI] Coordinates: {request.coordinates}, Days: {request.days}")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates']
            )
            
            response = await weather_handler.get_field_weather(
                cleaned_data['fieldId'], 
                cleaned_data['coordinates'], 
                cleaned_data.get('days', 7)
            )
            
        except ValueError as e:
            logger.error(f"🌤️ [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
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
async def historical_weather(request: WeatherRequest):
    """Historical Weather Data for Field"""
    try:
        logger.info(f"🌤️ [FASTAPI] Historical Weather Request - Field: {request.fieldId}")
        
        # Use yesterday's date as default
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = await weather_handler.get_historical_weather(
            request.fieldId, 
            request.coordinates, 
            yesterday
        )
        
        logger.info(f"🌤️ [FASTAPI] Historical Weather Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌤️ [FASTAPI] Historical Weather Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather/forecast")
async def weather_forecast(request: WeatherRequest):
    """Weather Forecast for Field"""
    try:
        logger.info(f"🌤️ [FASTAPI] Weather Forecast Request - Field: {request.fieldId}")
        
        response = await weather_handler.get_forecast(
            request.fieldId, 
            request.coordinates, 
            request.days or 14
        )
        
        logger.info(f"🌤️ [FASTAPI] Weather Forecast Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌤️ [FASTAPI] Weather Forecast Error: {str(e)}")
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
            try:
                field_response = await optimized_field_metrics_handler.get_field_metrics(
                    request.fieldId, 
                    request.coordinates
                )
                field_metrics = field_response
            except Exception as e:
                logger.warning(f"⚠️ [RECOMMENDATIONS] Field metrics failed: {str(e)}")
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
            try:
                field_response = await optimized_field_metrics_handler.get_field_metrics(
                    request.fieldId, 
                    request.coordinates
                )
                field_metrics = field_response
            except Exception as e:
                logger.warning(f"⚠️ [RECOMMENDATIONS] Field metrics failed: {str(e)}")
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
            field_response = await optimized_field_metrics_handler.get_field_metrics(
                request.fieldId, 
                request.coordinates
            )
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
            field_response = await optimized_field_metrics_handler.get_field_metrics(
                request.fieldId, 
                request.coordinates
            )
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
            field_response = await optimized_field_metrics_handler.get_field_metrics(
                request.fieldId, 
                request.coordinates
            )
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
    """Optimized Field Trends Analysis - Fast historical data analysis for B2B"""
    try:
        logger.info(f"📈 [FASTAPI] Optimized Trends Request - Field: {request.fieldId}")
        logger.info(f"📈 [FASTAPI] Period: {request.timePeriod}, Type: {request.analysisType}")
        
        response = await optimized_trends_handler.get_field_trends(
            request.fieldId,
            request.coordinates,
            request.timePeriod,
            request.analysisType
        )
        
        logger.info(f"📈 [FASTAPI] Optimized Trends Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"📈 [FASTAPI] Optimized Trends Error: {str(e)}")
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
        
        response = await optimized_terrain_handler.get_elevation_analysis(
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
        
        response = await optimized_terrain_handler.get_land_cover_analysis(
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
        
        response = await optimized_terrain_handler.get_comprehensive_analysis(
            request.coordinates
        )
        
        logger.info(f"🏔️🌍 [FASTAPI] Comprehensive Terrain Success - Field: {request.fieldId}")
        return response
            
    except Exception as e:
        logger.error(f"🏔️🌍 [FASTAPI] Comprehensive Terrain Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Yield Prediction API Endpoints
@app.post("/api/yield/prediction")
async def yield_prediction(request: YieldPredictionRequest):
    """Yield Prediction - Comprehensive crop yield prediction using satellite and weather data"""
    try:
        logger.info(f"🌾 [FASTAPI] Yield Prediction Request - Field: {request.fieldId}")
        logger.info(f"🌾 [FASTAPI] Coordinates: {request.coordinates}, Crop: {request.cropType}, Period: {request.predictionPeriod}")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates']
            )
            
            response = await yield_prediction_handler.get_yield_prediction(
                cleaned_data['fieldId'], 
                cleaned_data['coordinates'], 
                cleaned_data.get('cropType', 'general'),
                cleaned_data.get('predictionPeriod', 'seasonal')
            )
            
        except ValueError as e:
            logger.error(f"🌾 [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
        logger.info(f"🌾 [FASTAPI] Yield Prediction Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌾 [FASTAPI] Yield Prediction Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yield/confidence")
async def yield_confidence(request: YieldPredictionRequest):
    """Yield Confidence - Get confidence score for yield prediction"""
    try:
        logger.info(f"🌾 [FASTAPI] Yield Confidence Request - Field: {request.fieldId}")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates']
            )
            
            response = await yield_prediction_handler.get_yield_confidence(
                cleaned_data['fieldId'], 
                cleaned_data['coordinates'], 
                cleaned_data.get('cropType', 'general')
            )
            
        except ValueError as e:
            logger.error(f"🌾 [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
        logger.info(f"🌾 [FASTAPI] Yield Confidence Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌾 [FASTAPI] Yield Confidence Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yield/factors")
async def yield_factors(request: YieldPredictionRequest):
    """Yield Factors - Identify key factors affecting yield"""
    try:
        logger.info(f"🌾 [FASTAPI] Yield Factors Request - Field: {request.fieldId}")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates']
            )
            
            response = await yield_prediction_handler.get_yield_factors(
                cleaned_data['fieldId'], 
                cleaned_data['coordinates'], 
                cleaned_data.get('cropType', 'general')
            )
            
        except ValueError as e:
            logger.error(f"🌾 [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
        logger.info(f"🌾 [FASTAPI] Yield Factors Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌾 [FASTAPI] Yield Factors Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yield/recommendations")
async def yield_recommendations(request: YieldPredictionRequest):
    """Yield Recommendations - Get yield optimization recommendations"""
    try:
        logger.info(f"🌾 [FASTAPI] Yield Recommendations Request - Field: {request.fieldId}")
        
        # Simple validation and cleaning
        try:
            cleaned_data = simple_validator.validate_request(
                request.dict(), 
                required_fields=['fieldId', 'coordinates']
            )
            
            response = await yield_prediction_handler.get_yield_recommendations(
                cleaned_data['fieldId'], 
                cleaned_data['coordinates'], 
                cleaned_data.get('cropType', 'general')
            )
            
        except ValueError as e:
            logger.error(f"🌾 [FASTAPI] Validation Error - Field: {request.fieldId}, Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
        
        logger.info(f"🌾 [FASTAPI] Yield Recommendations Success - Field: {request.fieldId}")
        return response
        
    except Exception as e:
        logger.error(f"🌾 [FASTAPI] Yield Recommendations Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/field-metrics/stats")
async def get_field_metrics_stats():
    """Get performance statistics for field metrics API"""
    try:
        from api.planetary_computer_retry import retry_manager
        from api.enhanced_planetary_computer import enhanced_pc_manager
        
        # Get stats from both managers
        retry_stats = retry_manager.get_performance_stats()
        enhanced_stats = enhanced_pc_manager.get_performance_stats()
        
        combined_stats = {
            "retry_manager": retry_stats,
            "enhanced_manager": enhanced_stats,
            "comparison": {
                "total_requests": enhanced_stats.get('total_requests', 0),
                "success_rate": enhanced_stats.get('success_rate', '0%'),
                "cache_hit_rate": enhanced_stats.get('cache_hit_rate', '0%'),
                "average_response_time": enhanced_stats.get('average_response_time', '0s')
            }
        }
        
        logger.info("📊 [FASTAPI] Enhanced Performance Stats Retrieved")
        return {
            "success": True,
            "stats": combined_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"📊 [FASTAPI] Performance Stats Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 Starting ZumAgro Python API...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)