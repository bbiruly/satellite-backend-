"""
Historical Trend Analyzer
Analyzes NPK trends over time for agricultural monitoring
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import sys
import os

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import NPK_BASE_VALUES, SEASONAL_FACTORS, VEGETATION_INDICES_CONFIG, WEATHER_CONFIG
from .weather_integration import get_weather_data
from .sentinel_indices import compute_indices_and_npk_for_bbox
from .icar_only_analysis import generate_icar_only_analysis

logger = logging.getLogger(__name__)

class HistoricalAnalyzer:
    """
    Analyzes historical NPK trends and patterns
    """
    
    def __init__(self):
        self.trend_cache = {}
        self.cache_ttl = 1800  # 30 minutes cache for trend data
    
    def get_historical_trends(self, coordinates: Tuple[float, float], 
                            months: int = 6, crop_type: str = "GENERIC") -> Dict[str, Any]:
        """
        Get NPK trends for past N months
        
        Args:
            coordinates: (latitude, longitude)
            months: Number of months to analyze
            crop_type: Type of crop
        
        Returns:
            Dictionary with historical data and trends
        """
        lat, lon = coordinates
        cache_key = f"{lat:.4f}_{lon:.4f}_{months}_{crop_type}"
        
        # Check cache first
        if cache_key in self.trend_cache:
            cached_data, timestamp = self.trend_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                logger.info(f"📊 Returning cached historical trends for {coordinates}")
                return cached_data
        
        logger.info(f"📊 Analyzing {months}-month historical trends for {coordinates}")
        
        # Generate historical data points
        historical_data = self._generate_historical_data(coordinates, months, crop_type)
        
        if not historical_data:
            return {
                "success": False,
                "error": "No historical data available",
                "coordinates": coordinates,
                "months_analyzed": months
            }
        
        # Calculate trends
        trends = self._calculate_trends(historical_data)
        
        # Generate insights
        insights = self._generate_insights(historical_data, trends)
        
        # Generate recommendations
        recommendations = self._generate_trend_recommendations(trends, historical_data)
        
        result = {
            "success": True,
            "coordinates": coordinates,
            "months_analyzed": months,
            "crop_type": crop_type,
            "data_points": len(historical_data),
            "historical_data": historical_data,
            "trends": trends,
            "insights": insights,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat()
        }
        
        # Cache the result
        self.trend_cache[cache_key] = (result, datetime.now())
        
        return result
    
    def _generate_historical_data(self, coordinates: Tuple[float, float], 
                                months: int, crop_type: str) -> List[Dict[str, Any]]:
        """
        Generate historical data points using real satellite data
        
        Args:
            coordinates: (latitude, longitude)
            months: Number of months
            crop_type: Type of crop
        
        Returns:
            List of historical data points
        """
        historical_data = []
        current_date = datetime.now()
        lat, lon = coordinates
        
        # Create bounding box for satellite data
        bbox = {
            'minLat': lat - 0.01,
            'maxLat': lat + 0.01,
            'minLon': lon - 0.01,
            'maxLon': lon + 0.01
        }
        
        for i in range(months):
            # Go back in time by i months
            analysis_date = current_date - timedelta(days=30 * i)
            
            # Try to get real satellite data
            npk_data, indices_data, satellite_source = self._fetch_real_historical_data(
                bbox, coordinates, analysis_date, crop_type
            )
            
            # Get real weather data
            weather_data = get_weather_data(coordinates, analysis_date)
            
            if npk_data:
                historical_data.append({
                    "date": analysis_date.strftime('%Y-%m-%d'),
                    "month": analysis_date.strftime('%Y-%m'),
                    "npk": npk_data,
                    "indices": indices_data,
                    "weather": weather_data,
                    "satellite_source": satellite_source
                })
        
        return historical_data
    
    def _fetch_real_historical_data(self, bbox: Dict[str, float], 
                                  coordinates: Tuple[float, float],
                                  date: datetime, crop_type: str) -> Tuple[Optional[Dict[str, float]], 
                                                                          Optional[Dict[str, float]], 
                                                                          str]:
        """
        Fetch real historical satellite data
        
        Args:
            bbox: Bounding box for satellite data
            coordinates: (latitude, longitude)
            date: Analysis date
            crop_type: Type of crop
        
        Returns:
            Tuple of (NPK data, indices data, satellite source)
        """
        try:
            # Try to get real satellite data
            result = compute_indices_and_npk_for_bbox(
                bbox=bbox,
                start_date=date,
                end_date=date + timedelta(days=1),
                crop_type=crop_type
            )
            
            if result.get('success') and result.get('soilNutrients'):
                npk_data = {
                    "Nitrogen": result['soilNutrients'].get('Nitrogen', 0),
                    "Phosphorus": result['soilNutrients'].get('Phosphorus', 0),
                    "Potassium": result['soilNutrients'].get('Potassium', 0),
                    "Soc": result['soilNutrients'].get('Soc', 0)
                }
                
                indices_data = {
                    "NDVI": result.get('vegetationIndices', {}).get('NDVI', {}).get('mean', 0),
                    "NDMI": result.get('vegetationIndices', {}).get('NDMI', {}).get('mean', 0),
                    "SAVI": result.get('vegetationIndices', {}).get('SAVI', {}).get('mean', 0)
                }
                
                satellite_source = result.get('metadata', {}).get('satelliteSource', 'Sentinel-2')
                
                return npk_data, indices_data, satellite_source
                
        except Exception as e:
            logger.warning(f"Failed to fetch satellite data for {date}: {e}")
        
        # Fallback to ICAR-only analysis
        try:
            icar_result = generate_icar_only_analysis(
                coordinates=coordinates,
                crop_type=crop_type,
                field_area_ha=1.0
            )
            
            if icar_result.get('success') and icar_result.get('soilNutrients'):
                npk_data = {
                    "Nitrogen": icar_result['soilNutrients'].get('Nitrogen', 0),
                    "Phosphorus": icar_result['soilNutrients'].get('Phosphorus', 0),
                    "Potassium": icar_result['soilNutrients'].get('Potassium', 0),
                    "Soc": icar_result['soilNutrients'].get('Soc', 0)
                }
                
                # Use default indices for ICAR-only
                indices_data = {
                    "NDVI": 0.5,
                    "NDMI": 0.3,
                    "SAVI": 0.4
                }
                
                return npk_data, indices_data, "ICAR-Only"
                
        except Exception as e:
            logger.warning(f"Failed to fetch ICAR data for {date}: {e}")
        
        # Final fallback to intelligent defaults
        return self._get_intelligent_defaults(coordinates, date, crop_type)
    
    def _get_intelligent_defaults(self, coordinates: Tuple[float, float], 
                                date: datetime, crop_type: str) -> Tuple[Dict[str, float], 
                                                                        Dict[str, float], str]:
        """
        Get intelligent default values based on configuration and weather
        
        Args:
            coordinates: (latitude, longitude)
            date: Analysis date
            crop_type: Type of crop
        
        Returns:
            Tuple of (NPK data, indices data, source)
        """
        # Get weather data for seasonal adjustment
        weather_data = get_weather_data(coordinates, date)
        
        # Calculate seasonal factor from weather
        month = date.month
        if month in [6, 7, 8, 9]:  # Monsoon
            seasonal_factor = SEASONAL_FACTORS["monsoon"]["factor"]
        elif month in [10, 11, 12, 1]:  # Winter
            seasonal_factor = SEASONAL_FACTORS["winter"]["factor"]
        else:  # Summer
            seasonal_factor = SEASONAL_FACTORS["summer"]["factor"]
        
        # Adjust based on weather conditions
        if weather_data.get("condition") == "rainy":
            seasonal_factor *= 1.1
        elif weather_data.get("condition") == "clear" and weather_data.get("humidity", 60) < 40:
            seasonal_factor *= 0.95
        
        # Get NPK values from configuration
        npk_data = {
            "Nitrogen": round(NPK_BASE_VALUES["nitrogen"]["default"] * seasonal_factor, 1),
            "Phosphorus": round(NPK_BASE_VALUES["phosphorus"]["default"] * seasonal_factor, 1),
            "Potassium": round(NPK_BASE_VALUES["potassium"]["default"] * seasonal_factor, 1),
            "Soc": round(NPK_BASE_VALUES["soc"]["default"] * seasonal_factor, 2)
        }
        
        # Get vegetation indices from configuration
        if month in [6, 7, 8, 9]:  # Monsoon
            ndvi_base = VEGETATION_INDICES_CONFIG["ndvi"]["monsoon"]
        elif month in [10, 11, 12, 1]:  # Winter
            ndvi_base = VEGETATION_INDICES_CONFIG["ndvi"]["winter"]
        else:  # Summer
            ndvi_base = VEGETATION_INDICES_CONFIG["ndvi"]["summer"]
        
        indices_data = {
            "NDVI": round(ndvi_base, 3),
            "NDMI": round(ndvi_base - VEGETATION_INDICES_CONFIG["ndmi"]["base_offset"], 3),
            "SAVI": round(ndvi_base * VEGETATION_INDICES_CONFIG["savi"]["multiplier"], 3)
        }
        
        return npk_data, indices_data, "Intelligent-Default"
    
    def _calculate_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trends from historical data
        
        Args:
            historical_data: List of historical data points
        
        Returns:
            Dictionary with trend information
        """
        if len(historical_data) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Extract NPK values over time
        nitrogen_values = [point["npk"]["Nitrogen"] for point in historical_data]
        phosphorus_values = [point["npk"]["Phosphorus"] for point in historical_data]
        potassium_values = [point["npk"]["Potassium"] for point in historical_data]
        soc_values = [point["npk"]["Soc"] for point in historical_data]
        
        # Calculate trends
        trends = {
            "nitrogen": self._calculate_single_trend(nitrogen_values, "Nitrogen"),
            "phosphorus": self._calculate_single_trend(phosphorus_values, "Phosphorus"),
            "potassium": self._calculate_single_trend(potassium_values, "Potassium"),
            "soc": self._calculate_single_trend(soc_values, "SOC")
        }
        
        # Calculate overall soil health trend
        trends["overall_health"] = self._calculate_overall_health_trend(trends)
        
        return trends
    
    def _calculate_single_trend(self, values: List[float], nutrient: str) -> Dict[str, Any]:
        """
        Calculate trend for a single nutrient
        
        Args:
            values: List of values over time
            nutrient: Nutrient name
        
        Returns:
            Dictionary with trend information
        """
        if len(values) < 2:
            return {"direction": "stable", "change_percent": 0, "confidence": "low"}
        
        # Calculate linear trend
        n = len(values)
        x = list(range(n))
        
        # Simple linear regression
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Calculate change percentage
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.1:  # Small slope
            direction = "stable"
            confidence = "medium"
        elif slope > 0:
            direction = "increasing"
            confidence = "high" if abs(change_percent) > 10 else "medium"
        else:
            direction = "decreasing"
            confidence = "high" if abs(change_percent) > 10 else "medium"
        
        return {
            "direction": direction,
            "change_percent": round(change_percent, 1),
            "confidence": confidence,
            "slope": round(slope, 3),
            "first_value": round(first_value, 1),
            "last_value": round(last_value, 1),
            "average": round(sum(values) / len(values), 1)
        }
    
    def _calculate_overall_health_trend(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall soil health trend
        
        Args:
            trends: Individual nutrient trends
        
        Returns:
            Overall health trend information
        """
        # Weight different nutrients
        weights = {
            "nitrogen": 0.3,
            "phosphorus": 0.25,
            "potassium": 0.25,
            "soc": 0.2
        }
        
        # Calculate weighted trend score
        trend_scores = []
        for nutrient, trend in trends.items():
            if nutrient == "overall_health":
                continue
            
            if trend["direction"] == "increasing":
                score = 1
            elif trend["direction"] == "stable":
                score = 0
            else:  # decreasing
                score = -1
            
            trend_scores.append(score * weights.get(nutrient, 0.25))
        
        overall_score = sum(trend_scores)
        
        if overall_score > 0.2:
            direction = "improving"
        elif overall_score < -0.2:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "score": round(overall_score, 2),
            "confidence": "high" if abs(overall_score) > 0.5 else "medium"
        }
    
    def _generate_insights(self, historical_data: List[Dict[str, Any]], 
                          trends: Dict[str, Any]) -> List[str]:
        """
        Generate insights from historical data and trends
        
        Args:
            historical_data: Historical data points
            trends: Calculated trends
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Nutrient-specific insights
        for nutrient, trend in trends.items():
            if nutrient == "overall_health":
                continue
            
            if trend["direction"] == "increasing":
                insights.append(f"{nutrient.title()} levels are increasing by {trend['change_percent']:.1f}% over the period")
            elif trend["direction"] == "decreasing":
                insights.append(f"{nutrient.title()} levels are decreasing by {abs(trend['change_percent']):.1f}% over the period")
            else:
                insights.append(f"{nutrient.title()} levels have remained stable")
        
        # Overall health insight
        if "overall_health" in trends:
            health_trend = trends["overall_health"]
            if health_trend["direction"] == "improving":
                insights.append("Overall soil health is improving over time")
            elif health_trend["direction"] == "declining":
                insights.append("Overall soil health is declining and needs attention")
            else:
                insights.append("Overall soil health has remained stable")
        
        # Seasonal insights
        if len(historical_data) >= 6:
            seasonal_variation = self._analyze_seasonal_variation(historical_data)
            if seasonal_variation:
                insights.append(f"Seasonal variation detected: {seasonal_variation}")
        
        return insights
    
    def _analyze_seasonal_variation(self, historical_data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Analyze seasonal variation in the data
        
        Args:
            historical_data: Historical data points
        
        Returns:
            Seasonal variation description or None
        """
        # Group by season
        seasons = {"winter": [], "summer": [], "monsoon": []}
        
        for point in historical_data:
            month = datetime.strptime(point["date"], "%Y-%m-%d").month
            if month in [10, 11, 12, 1]:
                seasons["winter"].append(point)
            elif month in [6, 7, 8, 9]:
                seasons["monsoon"].append(point)
            else:
                seasons["summer"].append(point)
        
        # Check for significant seasonal differences
        if len(seasons["monsoon"]) > 0 and len(seasons["winter"]) > 0:
            monsoon_avg = sum(point["npk"]["Nitrogen"] for point in seasons["monsoon"]) / len(seasons["monsoon"])
            winter_avg = sum(point["npk"]["Nitrogen"] for point in seasons["winter"]) / len(seasons["winter"])
            
            if abs(monsoon_avg - winter_avg) > 20:  # 20% difference
                return "Higher nutrient levels during monsoon season"
        
        return None
    
    def _generate_trend_recommendations(self, trends: Dict[str, Any], 
                                       historical_data: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on trends
        
        Args:
            trends: Calculated trends
            historical_data: Historical data points
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Nutrient-specific recommendations
        for nutrient, trend in trends.items():
            if nutrient == "overall_health":
                continue
            
            if trend["direction"] == "decreasing" and abs(trend["change_percent"]) > 10:
                recommendations.append(f"Consider increasing {nutrient} application - levels declining by {abs(trend['change_percent']):.1f}%")
            elif trend["direction"] == "increasing" and trend["change_percent"] > 20:
                recommendations.append(f"Monitor {nutrient} levels - rapid increase of {trend['change_percent']:.1f}% detected")
        
        # Overall recommendations
        if "overall_health" in trends:
            health_trend = trends["overall_health"]
            if health_trend["direction"] == "declining":
                recommendations.append("Implement soil health improvement practices")
            elif health_trend["direction"] == "improving":
                recommendations.append("Continue current management practices - soil health is improving")
        
        # Seasonal recommendations
        if len(historical_data) >= 3:
            recent_data = historical_data[:3]  # Last 3 months
            avg_nitrogen = sum(point["npk"]["Nitrogen"] for point in recent_data) / len(recent_data)
            
            if avg_nitrogen < 150:
                recommendations.append("Consider nitrogen supplementation for optimal crop growth")
            elif avg_nitrogen > 300:
                recommendations.append("Nitrogen levels are high - reduce application to prevent leaching")
        
        return recommendations

# Global instance
historical_analyzer = HistoricalAnalyzer()

def get_historical_trends(coordinates: Tuple[float, float], 
                         months: int = 6, crop_type: str = "GENERIC") -> Dict[str, Any]:
    """
    Convenience function to get historical trends
    
    Args:
        coordinates: (latitude, longitude)
        months: Number of months to analyze
        crop_type: Type of crop
    
    Returns:
        Dictionary with historical trends data
    """
    return historical_analyzer.get_historical_trends(coordinates, months, crop_type)
