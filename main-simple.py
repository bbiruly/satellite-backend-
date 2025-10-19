#!/usr/bin/env python3
"""
Simple FastAPI Backend - No Geospatial Dependencies
This version runs without geospatial packages for initial deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ZumAgro Simple API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Request(BaseModel):
    fieldId: str
    coordinates: List[float]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    specific_date: Optional[str] = None
    crop_type: Optional[str] = "GENERIC"
    field_area_hectares: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ZumAgro Simple API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "ZumAgro Simple API",
        "version": "1.0.0",
        "timestamp": time.time(),
        "features": {
            "geospatial": "disabled",
            "satellite_data": "disabled",
            "basic_api": "enabled"
        }
    }

@app.post("/api/soc-analysis")
async def soc_analysis(request: Request):
    """Mock SOC Analysis - Returns sample data"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Mock SOC calculation
        soc_percentage = 2.5 + (lat * 0.1) + (lon * 0.05)
        soc_percentage = max(0, min(5, soc_percentage))
        
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
            "data": {
                "soc_percentage": round(soc_percentage, 2),
                "soc_level": soc_level,
                "coordinates": coords,
                "crop_type": request.crop_type,
                "timestamp": time.time(),
                "note": "Mock data - geospatial features disabled"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "SOC analysis failed"
        }

@app.post("/api/npk-analysis")
async def npk_analysis(request: Request):
    """Mock NPK Analysis - Returns sample data"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Mock NPK calculation
        nitrogen = 120 + (lat * 5) + (lon * 3)
        phosphorus = 25 + (lat * 2) + (lon * 1)
        potassium = 150 + (lat * 4) + (lon * 2)
        
        return {
            "success": True,
            "data": {
                "npk": {
                    "nitrogen": round(nitrogen, 2),
                    "phosphorus": round(phosphorus, 2),
                    "potassium": round(potassium, 2)
                },
                "coordinates": coords,
                "crop_type": request.crop_type,
                "timestamp": time.time(),
                "note": "Mock data - geospatial features disabled"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "NPK analysis failed"
        }

@app.post("/api/weather-analysis")
async def weather_analysis(request: Request):
    """Mock Weather Analysis - Returns sample data"""
    try:
        coords = request.coordinates
        lat, lon = coords[0], coords[1]
        
        # Mock weather data
        temperature = 25 + (lat * 0.5) + (lon * 0.3)
        humidity = 60 + (lat * 2) + (lon * 1)
        rainfall = 100 + (lat * 10) + (lon * 5)
        
        return {
            "success": True,
            "data": {
                "weather": {
                    "temperature": round(temperature, 2),
                    "humidity": round(humidity, 2),
                    "rainfall": round(rainfall, 2)
                },
                "coordinates": coords,
                "timestamp": time.time(),
                "note": "Mock data - weather API disabled"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Weather analysis failed"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

