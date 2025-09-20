"""
Crop Health Monitoring Service
Uses Microsoft Planetary Computer satellite data for real-time crop health analysis
Based on scientific research and established agricultural indices
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

# Import our existing satellite processing
from sentinel_indices import compute_indices_and_npk_for_bbox
from weather_service import WeatherService

logger = logging.getLogger(__name__)

@dataclass
class CropHealthMetrics:
    """Crop health metrics based on satellite data"""
    overall_health_score: float  # 0-100
    stress_level: str  # low, medium, high, critical
    growth_stage: str  # germination, vegetative, flowering, fruiting, maturity
    quality_score: float  # 0-100
    disease_risk: str  # low, medium, high
    pest_risk: str  # low, medium, high
    water_stress: str  # low, medium, high, critical
    nutrient_stress: str  # low, medium, high, critical
    temperature_stress: str  # low, medium, high, critical
    indices: Dict[str, float]
    recommendations: List[str]
    confidence: float  # 0-1

class CropHealthService:
    """Service for monitoring crop health using satellite data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.weather_service = WeatherService()
        
        # Scientific thresholds based on research
        self.health_thresholds = {
            'ndvi': {'excellent': 0.7, 'good': 0.5, 'fair': 0.3, 'poor': 0.1},
            'ndmi': {'excellent': 0.4, 'good': 0.2, 'fair': 0.0, 'poor': -0.2},
            'savi': {'excellent': 0.6, 'good': 0.4, 'fair': 0.2, 'poor': 0.0},
            'ndwi': {'excellent': 0.3, 'good': 0.1, 'fair': -0.1, 'poor': -0.3}
        }
        
        # Growth stage thresholds based on NDVI curves
        self.growth_stages = {
            'germination': {'ndvi_min': 0.0, 'ndvi_max': 0.2, 'description': 'Seed germination and early growth'},
            'vegetative': {'ndvi_min': 0.2, 'ndvi_max': 0.6, 'description': 'Active vegetative growth'},
            'flowering': {'ndvi_min': 0.6, 'ndvi_max': 0.8, 'description': 'Flowering and early fruiting'},
            'fruiting': {'ndvi_min': 0.8, 'ndvi_max': 0.9, 'description': 'Fruit development and maturation'},
            'maturity': {'ndvi_min': 0.9, 'ndvi_max': 1.0, 'description': 'Crop maturity and harvest readiness'}
        }
        
        # Stress indicators based on scientific research
        self.stress_indicators = {
            'water_stress': {
                'ndwi_threshold': -0.2,
                'ndvi_decline': 0.1,
                'description': 'Water stress indicated by low NDWI and declining NDVI'
            },
            'nutrient_stress': {
                'ndvi_threshold': 0.4,
                'savi_threshold': 0.3,
                'description': 'Nutrient stress indicated by low vegetation indices'
            },
            'temperature_stress': {
                'ndvi_threshold': 0.3,
                'ndmi_threshold': 0.1,
                'description': 'Temperature stress indicated by reduced vegetation activity'
            }
        }

    async def get_crop_health_analysis(
        self, 
        field_id: str, 
        coordinates: List[float], 
        crop_type: str = "general"
    ) -> CropHealthMetrics:
        """
        Get comprehensive crop health analysis using satellite data
        
        Args:
            field_id: Unique field identifier
            coordinates: [lat, lon] coordinates
            crop_type: Type of crop (wheat, rice, corn, etc.)
            
        Returns:
            CropHealthMetrics object with health analysis
        """
        try:
            self.logger.info(f"🌱 [CROP-HEALTH] Starting health analysis for field: {field_id}")
            
            # Get satellite data
            satellite_data = await self._get_satellite_data(field_id, coordinates)
            if not satellite_data:
                raise ValueError("No satellite data available")
            
            # Get weather data for context
            weather_data = await self._get_weather_data(coordinates)
            
            # Analyze crop health
            health_metrics = await self._analyze_crop_health(
                satellite_data, weather_data, crop_type
            )
            
            self.logger.info(f"✅ [CROP-HEALTH] Health analysis completed for field: {field_id}")
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error in health analysis: {str(e)}")
            raise

    async def _get_satellite_data(self, field_id: str, coordinates: List[float]) -> Optional[Dict]:
        """Get satellite data for the field"""
        try:
            # Use existing satellite processing
            bbox = self._create_bbox(coordinates)
            satellite_data = compute_indices_and_npk_for_bbox(bbox)
            
            if satellite_data and 'indices' in satellite_data:
                return satellite_data
            return None
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error getting satellite data: {str(e)}")
            return None

    async def _get_weather_data(self, coordinates: List[float]) -> Optional[Dict]:
        """Get weather data for context"""
        try:
            weather_data = await self.weather_service.get_current_weather(
                coordinates[0], coordinates[1]
            )
            return weather_data
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error getting weather data: {str(e)}")
            return None

    def _create_bbox(self, coordinates: List[float]) -> Dict[str, float]:
        """Create bounding box from coordinates"""
        lat, lon = coordinates[0], coordinates[1]
        # Small area around the point
        offset = 0.001  # ~100m
        return {
            'minLon': lon - offset,
            'maxLon': lon + offset,
            'minLat': lat - offset,
            'maxLat': lat + offset
        }

    async def _analyze_crop_health(
        self, 
        satellite_data: Dict, 
        weather_data: Optional[Dict], 
        crop_type: str
    ) -> CropHealthMetrics:
        """Analyze crop health using satellite indices and weather data"""
        
        indices = satellite_data.get('indices', {})
        
        # Calculate health score
        health_score = self._calculate_health_score(indices)
        
        # Determine stress levels
        stress_level = self._assess_stress_level(indices, weather_data)
        
        # Determine growth stage
        growth_stage = self._determine_growth_stage(indices)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(indices)
        
        # Assess disease and pest risks
        disease_risk = self._assess_disease_risk(indices, weather_data)
        pest_risk = self._assess_pest_risk(indices, weather_data)
        
        # Assess specific stress types
        water_stress = self._assess_water_stress(indices, weather_data)
        nutrient_stress = self._assess_nutrient_stress(indices)
        temperature_stress = self._assess_temperature_stress(indices, weather_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            health_score, stress_level, growth_stage, 
            water_stress, nutrient_stress, temperature_stress
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(indices, weather_data)
        
        return CropHealthMetrics(
            overall_health_score=health_score,
            stress_level=stress_level,
            growth_stage=growth_stage,
            quality_score=quality_score,
            disease_risk=disease_risk,
            pest_risk=pest_risk,
            water_stress=water_stress,
            nutrient_stress=nutrient_stress,
            temperature_stress=temperature_stress,
            indices=indices,
            recommendations=recommendations,
            confidence=confidence
        )

    def _calculate_health_score(self, indices: Dict[str, float]) -> float:
        """Calculate overall health score based on vegetation indices"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            savi = indices.get('SAVI', {}).get('mean', 0)
            ndwi = indices.get('NDWI', {}).get('mean', 0)
            
            # Weighted health score based on scientific research
            weights = {'ndvi': 0.4, 'ndmi': 0.3, 'savi': 0.2, 'ndwi': 0.1}
            
            # Normalize indices to 0-100 scale
            ndvi_score = min(100, max(0, (ndvi + 1) * 50))  # -1 to 1 -> 0 to 100
            ndmi_score = min(100, max(0, (ndmi + 1) * 50))
            savi_score = min(100, max(0, savi * 100))  # 0 to 1 -> 0 to 100
            ndwi_score = min(100, max(0, (ndwi + 1) * 50))
            
            health_score = (
                ndvi_score * weights['ndvi'] +
                ndmi_score * weights['ndmi'] +
                savi_score * weights['savi'] +
                ndwi_score * weights['ndwi']
            )
            
            return round(health_score, 1)
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error calculating health score: {str(e)}")
            return 0.0

    def _assess_stress_level(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> str:
        """Assess overall stress level"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            
            # Check for critical stress indicators
            if ndvi < 0.1 or ndmi < -0.3:
                return "critical"
            elif ndvi < 0.3 or ndmi < -0.1:
                return "high"
            elif ndvi < 0.5 or ndmi < 0.0:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing stress level: {str(e)}")
            return "unknown"

    def _determine_growth_stage(self, indices: Dict[str, float]) -> str:
        """Determine crop growth stage based on NDVI"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            
            for stage, thresholds in self.growth_stages.items():
                if thresholds['ndvi_min'] <= ndvi <= thresholds['ndvi_max']:
                    return stage
            
            # Default to vegetative if not in any specific range
            return "vegetative"
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error determining growth stage: {str(e)}")
            return "unknown"

    def _calculate_quality_score(self, indices: Dict[str, float]) -> float:
        """Calculate crop quality score"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            savi = indices.get('SAVI', {}).get('mean', 0)
            
            # Quality based on vegetation vigor and health
            quality_factors = [
                min(100, max(0, (ndvi + 1) * 50)),  # NDVI contribution
                min(100, max(0, (ndmi + 1) * 50)),  # NDMI contribution
                min(100, max(0, savi * 100))        # SAVI contribution
            ]
            
            quality_score = np.mean(quality_factors)
            return round(quality_score, 1)
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error calculating quality score: {str(e)}")
            return 0.0

    def _assess_disease_risk(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> str:
        """Assess disease risk based on vegetation indices and weather"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            
            # Disease risk indicators
            risk_factors = []
            
            # Low NDVI can indicate disease
            if ndvi < 0.3:
                risk_factors.append("low_ndvi")
            
            # Low NDMI can indicate moisture stress leading to disease
            if ndmi < -0.1:
                risk_factors.append("low_ndmi")
            
            # Weather factors
            if weather_data:
                humidity = weather_data.get('current', {}).get('humidity', 0)
                if humidity > 80:  # High humidity increases disease risk
                    risk_factors.append("high_humidity")
            
            if len(risk_factors) >= 3:
                return "high"
            elif len(risk_factors) >= 2:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing disease risk: {str(e)}")
            return "unknown"

    def _assess_pest_risk(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> str:
        """Assess pest risk based on vegetation indices and weather"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            
            # Pest risk indicators
            risk_factors = []
            
            # Stressed crops are more susceptible to pests
            if ndvi < 0.4:
                risk_factors.append("stressed_crop")
            
            # Low NDMI indicates moisture stress
            if ndmi < -0.1:
                risk_factors.append("moisture_stress")
            
            # Weather factors
            if weather_data:
                temp = weather_data.get('current', {}).get('temp_c', 0)
                if 20 <= temp <= 30:  # Optimal temperature range for many pests
                    risk_factors.append("optimal_temp")
            
            if len(risk_factors) >= 2:
                return "high"
            elif len(risk_factors) >= 1:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing pest risk: {str(e)}")
            return "unknown"

    def _assess_water_stress(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> str:
        """Assess water stress using NDWI and weather data"""
        try:
            ndwi = indices.get('NDWI', {}).get('mean', 0)
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            
            # Water stress indicators
            if ndwi < -0.3 or ndvi < 0.2:
                return "critical"
            elif ndwi < -0.1 or ndvi < 0.4:
                return "high"
            elif ndwi < 0.0 or ndvi < 0.6:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing water stress: {str(e)}")
            return "unknown"

    def _assess_nutrient_stress(self, indices: Dict[str, float]) -> str:
        """Assess nutrient stress using vegetation indices"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            savi = indices.get('SAVI', {}).get('mean', 0)
            
            # Nutrient stress indicators
            if ndvi < 0.3 or savi < 0.2:
                return "critical"
            elif ndvi < 0.5 or savi < 0.4:
                return "high"
            elif ndvi < 0.7 or savi < 0.6:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing nutrient stress: {str(e)}")
            return "unknown"

    def _assess_temperature_stress(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> str:
        """Assess temperature stress using vegetation indices and weather"""
        try:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            ndmi = indices.get('NDMI', {}).get('mean', 0)
            
            # Temperature stress indicators
            if ndvi < 0.2 or ndmi < -0.2:
                return "critical"
            elif ndvi < 0.4 or ndmi < -0.1:
                return "high"
            elif ndvi < 0.6 or ndmi < 0.0:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error assessing temperature stress: {str(e)}")
            return "unknown"

    def _generate_recommendations(
        self, 
        health_score: float, 
        stress_level: str, 
        growth_stage: str,
        water_stress: str, 
        nutrient_stress: str, 
        temperature_stress: str
    ) -> List[str]:
        """Generate actionable recommendations based on health analysis"""
        recommendations = []
        
        # Health score recommendations
        if health_score < 30:
            recommendations.append("Critical: Immediate intervention required - consider emergency irrigation and nutrient application")
        elif health_score < 50:
            recommendations.append("High Priority: Field requires urgent attention - schedule irrigation and fertilizer application")
        elif health_score < 70:
            recommendations.append("Medium Priority: Field needs improvement - plan irrigation and nutrient management")
        else:
            recommendations.append("Good: Field is healthy - maintain current management practices")
        
        # Stress-specific recommendations
        if stress_level == "critical":
            recommendations.append("Critical Stress: Implement emergency measures - check irrigation, apply nutrients, inspect for diseases")
        elif stress_level == "high":
            recommendations.append("High Stress: Increase monitoring frequency - schedule irrigation, apply fertilizer, check for pests")
        
        # Growth stage recommendations
        if growth_stage == "germination":
            recommendations.append("Germination Stage: Ensure adequate soil moisture and temperature for seed establishment")
        elif growth_stage == "vegetative":
            recommendations.append("Vegetative Stage: Focus on nutrient management and pest control for optimal growth")
        elif growth_stage == "flowering":
            recommendations.append("Flowering Stage: Critical period - avoid stress, ensure adequate water and nutrients")
        elif growth_stage == "fruiting":
            recommendations.append("Fruiting Stage: Maintain plant health for optimal fruit development")
        elif growth_stage == "maturity":
            recommendations.append("Maturity Stage: Prepare for harvest - monitor for over-ripening and quality")
        
        # Specific stress recommendations
        if water_stress in ["critical", "high"]:
            recommendations.append("Water Stress: Schedule immediate irrigation - check soil moisture and irrigation system")
        
        if nutrient_stress in ["critical", "high"]:
            recommendations.append("Nutrient Stress: Apply fertilizer - consider soil testing and targeted nutrient application")
        
        if temperature_stress in ["critical", "high"]:
            recommendations.append("Temperature Stress: Monitor weather conditions - consider shade or protective measures")
        
        return recommendations

    def _calculate_confidence(self, indices: Dict[str, float], weather_data: Optional[Dict]) -> float:
        """Calculate confidence in the health analysis"""
        try:
            confidence_factors = []
            
            # Data availability
            if indices:
                confidence_factors.append(0.8)  # Satellite data available
            else:
                confidence_factors.append(0.2)  # No satellite data
            
            # Weather data availability
            if weather_data:
                confidence_factors.append(0.2)  # Weather data available
            else:
                confidence_factors.append(0.0)  # No weather data
            
            # Data quality (based on index values)
            if indices:
                ndvi = indices.get('NDVI', {}).get('mean', 0)
                if 0.1 <= ndvi <= 0.9:  # Reasonable NDVI range
                    confidence_factors.append(0.3)
                else:
                    confidence_factors.append(0.1)
            
            confidence = sum(confidence_factors)
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error calculating confidence: {str(e)}")
            return 0.0

    async def get_crop_stress_analysis(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """Get detailed stress analysis for the field"""
        try:
            health_metrics = await self.get_crop_health_analysis(field_id, coordinates)
            
            return {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "stressAnalysis": {
                    "overallStress": health_metrics.stress_level,
                    "waterStress": health_metrics.water_stress,
                    "nutrientStress": health_metrics.nutrient_stress,
                    "temperatureStress": health_metrics.temperature_stress,
                    "diseaseRisk": health_metrics.disease_risk,
                    "pestRisk": health_metrics.pest_risk
                },
                "indices": health_metrics.indices,
                "recommendations": health_metrics.recommendations,
                "confidence": health_metrics.confidence
            }
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error in stress analysis: {str(e)}")
            raise

    async def get_growth_stage_analysis(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """Get growth stage analysis for the field"""
        try:
            health_metrics = await self.get_crop_health_analysis(field_id, coordinates)
            
            return {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "growthStage": {
                    "currentStage": health_metrics.growth_stage,
                    "description": self.growth_stages.get(health_metrics.growth_stage, {}).get('description', ''),
                    "healthScore": health_metrics.overall_health_score,
                    "qualityScore": health_metrics.quality_score
                },
                "indices": health_metrics.indices,
                "recommendations": health_metrics.recommendations,
                "confidence": health_metrics.confidence
            }
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error in growth stage analysis: {str(e)}")
            raise

    async def get_crop_quality_analysis(
        self, 
        field_id: str, 
        coordinates: List[float]
    ) -> Dict[str, Any]:
        """Get crop quality analysis for the field"""
        try:
            health_metrics = await self.get_crop_health_analysis(field_id, coordinates)
            
            return {
                "fieldId": field_id,
                "timestamp": datetime.now().isoformat(),
                "qualityAnalysis": {
                    "overallQuality": health_metrics.quality_score,
                    "healthScore": health_metrics.overall_health_score,
                    "stressLevel": health_metrics.stress_level,
                    "growthStage": health_metrics.growth_stage
                },
                "indices": health_metrics.indices,
                "recommendations": health_metrics.recommendations,
                "confidence": health_metrics.confidence
            }
            
        except Exception as e:
            self.logger.error(f"❌ [CROP-HEALTH] Error in quality analysis: {str(e)}")
            raise
