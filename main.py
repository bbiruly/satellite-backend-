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
                "/api/weather/historical"
            ],
        "description": "Clean, minimal API for agricultural intelligence",
        "features": [
            "Complete Field Metrics Analysis",
            "NPK + SOC + Health + Indices",
            "Complete Weather Integration",
            "Real-time Processing",
            "Intelligent Caching"
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

if __name__ == "__main__":
    logger.info("🚀 Starting ZumAgro Python API...")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)