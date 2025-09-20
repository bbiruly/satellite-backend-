#!/usr/bin/env python3
"""
Terrain Service - Elevation and Land Cover Analysis
Uses Microsoft Planetary Computer for elevation and land cover data
"""
import logging
from typing import Dict, Any, Optional, List
import pystac_client
import planetary_computer as pc
import rioxarray
import numpy as np
from datetime import datetime

logger = logging.getLogger("terrain_service")
logger.setLevel(logging.INFO)

class TerrainService:
    """Service for terrain and land cover analysis using Planetary Computer"""
    
    def __init__(self):
        self.logger = logger
        self.catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
        
    async def get_elevation_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get elevation analysis for coordinates
        
        Args:
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with elevation analysis
        """
        try:
            self.logger.info(f"🏔️ [TERRAIN] Starting elevation analysis for coordinates: {coordinates}")
            
            lat, lon = coordinates[0], coordinates[1]
            
            # Create bounding box around coordinates
            bbox = self._create_bbox(coordinates, offset=0.01)  # ~1km area
            
            # Search for elevation data
            search = self.catalog.search(
                collections=["cop-dem-glo-30"],  # 30m resolution global elevation
                bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
                limit=1
            )
            
            items = list(search.items())
            if not items:
                self.logger.warning("⚠️ [TERRAIN] No elevation data found")
                return self._get_fallback_elevation()
            
            item = items[0]
            self.logger.info(f"🏔️ [TERRAIN] Found elevation data: {item.id}")
            
            # Get elevation data
            elevation_data = await self._process_elevation_data(item, coordinates)
            
            self.logger.info(f"✅ [TERRAIN] Elevation analysis completed")
            return elevation_data
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error in elevation analysis: {str(e)}")
            return self._get_fallback_elevation()
    
    async def get_land_cover_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get land cover analysis for coordinates
        
        Args:
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with land cover analysis
        """
        try:
            self.logger.info(f"🌍 [TERRAIN] Starting land cover analysis for coordinates: {coordinates}")
            
            lat, lon = coordinates[0], coordinates[1]
            
            # Create bounding box around coordinates
            bbox = self._create_bbox(coordinates, offset=0.01)  # ~1km area
            
            # Search for land cover data (try multiple collections)
            land_cover_data = None
            
            # Try ESA WorldCover first (most recent)
            try:
                search = self.catalog.search(
                    collections=["esa-worldcover"],
                    bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
                    limit=1
                )
                
                items = list(search.items())
                if items:
                    item = items[0]
                    self.logger.info(f"🌍 [TERRAIN] Found ESA WorldCover data: {item.id}")
                    land_cover_data = await self._process_land_cover_data(item, coordinates, "esa-worldcover")
            except Exception as e:
                self.logger.warning(f"⚠️ [TERRAIN] ESA WorldCover failed: {e}")
            
            # Fallback to Esri Land Cover
            if not land_cover_data:
                try:
                    search = self.catalog.search(
                        collections=["io-lulc"],
                        bbox=[bbox['minLon'], bbox['minLat'], bbox['maxLon'], bbox['maxLat']],
                        limit=1
                    )
                    
                    items = list(search.items())
                    if items:
                        item = items[0]
                        self.logger.info(f"🌍 [TERRAIN] Found Esri Land Cover data: {item.id}")
                        land_cover_data = await self._process_land_cover_data(item, coordinates, "esri-lulc")
                except Exception as e:
                    self.logger.warning(f"⚠️ [TERRAIN] Esri Land Cover failed: {e}")
            
            if not land_cover_data:
                self.logger.warning("⚠️ [TERRAIN] No land cover data found")
                return self._get_fallback_land_cover()
            
            self.logger.info(f"✅ [TERRAIN] Land cover analysis completed")
            return land_cover_data
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error in land cover analysis: {str(e)}")
            return self._get_fallback_land_cover()
    
    async def get_comprehensive_terrain_analysis(self, coordinates: List[float]) -> Dict[str, Any]:
        """
        Get comprehensive terrain analysis combining elevation and land cover
        
        Args:
            coordinates: [lat, lon] coordinates
            
        Returns:
            Dictionary with comprehensive terrain analysis
        """
        try:
            self.logger.info(f"🏔️🌍 [TERRAIN] Starting comprehensive terrain analysis for coordinates: {coordinates}")
            
            # Get both elevation and land cover data
            elevation_data = await self.get_elevation_analysis(coordinates)
            land_cover_data = await self.get_land_cover_analysis(coordinates)
            
            # Combine analysis
            comprehensive_analysis = {
                "success": True,
                "coordinates": coordinates,
                "elevation": elevation_data,
                "landCover": land_cover_data,
                "terrainAnalysis": self._analyze_terrain_characteristics(elevation_data, land_cover_data),
                "metadata": {
                    "provider": "Microsoft Planetary Computer",
                    "analysisDate": datetime.utcnow().isoformat(),
                    "dataSources": [
                        "Copernicus DEM GLO-30",
                        "ESA WorldCover / Esri Land Cover"
                    ]
                }
            }
            
            self.logger.info(f"✅ [TERRAIN] Comprehensive terrain analysis completed")
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error in comprehensive terrain analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "coordinates": coordinates
            }
    
    def _create_bbox(self, coordinates: List[float], offset: float = 0.001) -> Dict[str, float]:
        """Create bounding box from coordinates"""
        lat, lon = coordinates[0], coordinates[1]
        return {
            'minLat': lat - offset,
            'maxLat': lat + offset,
            'minLon': lon - offset,
            'maxLon': lon + offset
        }
    
    async def _process_elevation_data(self, item, coordinates: List[float]) -> Dict[str, Any]:
        """Process elevation data from STAC item"""
        try:
            # Get elevation asset
            elevation_asset = item.assets.get('data')
            if not elevation_asset:
                raise ValueError("No elevation data asset found")
            
            # Sign the asset
            signed_url = pc.sign(elevation_asset).href
            self.logger.info(f"🏔️ [TERRAIN] Signed elevation URL: {signed_url[:100]}...")
            
            # Open elevation data
            da = rioxarray.open_rasterio(signed_url, masked=True)
            
            # Extract data around coordinates
            lat, lon = coordinates[0], coordinates[1]
            subset = da.sel(
                x=slice(lon - 0.005, lon + 0.005),  # ~500m area
                y=slice(lat + 0.005, lat - 0.005)   # Note: y is inverted
            )
            
            # Calculate elevation statistics
            elevation_values = subset.values.flatten()
            elevation_values = elevation_values[~np.isnan(elevation_values)]
            
            if len(elevation_values) == 0:
                raise ValueError("No valid elevation data found")
            
            elevation_mean = float(np.mean(elevation_values))
            elevation_min = float(np.min(elevation_values))
            elevation_max = float(np.max(elevation_values))
            elevation_std = float(np.std(elevation_values))
            
            # Analyze terrain characteristics
            terrain_analysis = self._analyze_elevation_characteristics(elevation_values)
            
            return {
                "success": True,
                "elevation": {
                    "mean": elevation_mean,
                    "min": elevation_min,
                    "max": elevation_max,
                    "std": elevation_std,
                    "range": elevation_max - elevation_min,
                    "count": len(elevation_values)
                },
                "terrainCharacteristics": terrain_analysis,
                "dataSource": "Copernicus DEM GLO-30",
                "resolution": "30m"
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error processing elevation data: {str(e)}")
            raise
    
    async def _process_land_cover_data(self, item, coordinates: List[float], source: str) -> Dict[str, Any]:
        """Process land cover data from STAC item"""
        try:
            # Get land cover asset
            land_cover_asset = item.assets.get('data') or item.assets.get('map')
            if not land_cover_asset:
                raise ValueError("No land cover data asset found")
            
            # Sign the asset
            signed_url = pc.sign(land_cover_asset).href
            self.logger.info(f"🌍 [TERRAIN] Signed land cover URL: {signed_url[:100]}...")
            
            # Open land cover data
            da = rioxarray.open_rasterio(signed_url, masked=True)
            
            # Extract data around coordinates
            lat, lon = coordinates[0], coordinates[1]
            subset = da.sel(
                x=slice(lon - 0.005, lon + 0.005),  # ~500m area
                y=slice(lat + 0.005, lat - 0.005)   # Note: y is inverted
            )
            
            # Calculate land cover statistics
            land_cover_values = subset.values.flatten()
            land_cover_values = land_cover_values[~np.isnan(land_cover_values)]
            
            if len(land_cover_values) == 0:
                raise ValueError("No valid land cover data found")
            
            # Get unique values and their counts
            unique_values, counts = np.unique(land_cover_values, return_counts=True)
            land_cover_distribution = dict(zip(unique_values.astype(int), counts))
            
            # Analyze land cover characteristics
            land_cover_analysis = self._analyze_land_cover_characteristics(land_cover_values, source)
            
            return {
                "success": True,
                "landCover": {
                    "distribution": land_cover_distribution,
                    "dominantClass": int(unique_values[int(np.argmax(counts))]),
                    "totalPixels": len(land_cover_values),
                    "uniqueClasses": len(unique_values)
                },
                "landCoverAnalysis": land_cover_analysis,
                "dataSource": source,
                "resolution": "10m"
            }
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error processing land cover data: {str(e)}")
            raise
    
    def _analyze_elevation_characteristics(self, elevation_values: np.ndarray) -> Dict[str, Any]:
        """Analyze elevation characteristics"""
        elevation_range = np.max(elevation_values) - np.min(elevation_values)
        elevation_std = np.std(elevation_values)
        
        # Classify terrain type based on elevation variation
        if elevation_range < 10:
            terrain_type = "flat"
            terrain_description = "Very flat terrain, suitable for agriculture"
        elif elevation_range < 50:
            terrain_type = "gentle"
            terrain_description = "Gentle slopes, good for agriculture"
        elif elevation_range < 100:
            terrain_type = "moderate"
            terrain_description = "Moderate slopes, suitable for agriculture with care"
        else:
            terrain_type = "steep"
            terrain_description = "Steep terrain, limited agricultural suitability"
        
        # Analyze drainage potential
        if elevation_std < 5:
            drainage = "poor"
            drainage_description = "Poor drainage, may need irrigation management"
        elif elevation_std < 15:
            drainage = "moderate"
            drainage_description = "Moderate drainage, generally suitable"
        else:
            drainage = "good"
            drainage_description = "Good drainage, well-suited for agriculture"
        
        return {
            "terrainType": terrain_type,
            "terrainDescription": terrain_description,
            "drainage": drainage,
            "drainageDescription": drainage_description,
            "elevationVariation": {
                "range": float(elevation_range),
                "std": float(elevation_std),
                "classification": terrain_type
            }
        }
    
    def _analyze_land_cover_characteristics(self, land_cover_values: np.ndarray, source: str) -> Dict[str, Any]:
        """Analyze land cover characteristics"""
        unique_values, counts = np.unique(land_cover_values, return_counts=True)
        dominant_class = int(unique_values[int(np.argmax(counts))])
        
        # Map land cover classes based on source
        if source == "esa-worldcover":
            land_cover_map = {
                10: "Tree cover",
                20: "Shrubland",
                30: "Grassland",
                40: "Cropland",
                50: "Built-up",
                60: "Bare/sparse vegetation",
                70: "Snow and ice",
                80: "Permanent water bodies",
                90: "Herbaceous wetland",
                95: "Mangroves",
                100: "Moss and lichen"
            }
        else:  # esri-lulc
            land_cover_map = {
                1: "Water",
                2: "Trees",
                3: "Grass",
                4: "Flooded vegetation",
                5: "Crops",
                6: "Shrub and scrub",
                7: "Built",
                8: "Bare ground",
                9: "Snow and ice",
                10: "Clouds"
            }
        
        dominant_class_name = land_cover_map.get(dominant_class, f"Unknown class {dominant_class}")
        
        # Analyze agricultural suitability
        agricultural_classes = [40, 5] if source == "esa-worldcover" else [5]  # Cropland
        agricultural_pixels = int(sum(counts[np.isin(unique_values, agricultural_classes)]))
        agricultural_percentage = (agricultural_pixels / len(land_cover_values)) * 100
        
        if agricultural_percentage > 50:
            suitability = "high"
            suitability_description = "High agricultural suitability"
        elif agricultural_percentage > 25:
            suitability = "medium"
            suitability_description = "Medium agricultural suitability"
        else:
            suitability = "low"
            suitability_description = "Low agricultural suitability"
        
        return {
            "dominantLandCover": dominant_class_name,
            "agriculturalSuitability": suitability,
            "agriculturalSuitabilityDescription": suitability_description,
            "agriculturalPercentage": float(agricultural_percentage),
            "landCoverClasses": land_cover_map
        }
    
    def _analyze_terrain_characteristics(self, elevation_data: Dict, land_cover_data: Dict) -> Dict[str, Any]:
        """Analyze combined terrain characteristics"""
        try:
            elevation_analysis = elevation_data.get("terrainCharacteristics", {})
            land_cover_analysis = land_cover_data.get("landCoverAnalysis", {})
            
            # Combine analyses
            combined_analysis = {
                "overallSuitability": self._calculate_overall_suitability(elevation_analysis, land_cover_analysis),
                "recommendations": self._generate_terrain_recommendations(elevation_analysis, land_cover_analysis),
                "riskFactors": self._identify_risk_factors(elevation_analysis, land_cover_analysis)
            }
            
            return combined_analysis
            
        except Exception as e:
            self.logger.error(f"❌ [TERRAIN] Error in terrain characteristics analysis: {str(e)}")
            return {
                "overallSuitability": "unknown",
                "recommendations": ["Unable to analyze terrain characteristics"],
                "riskFactors": ["Analysis failed"]
            }
    
    def _calculate_overall_suitability(self, elevation_analysis: Dict, land_cover_analysis: Dict) -> str:
        """Calculate overall agricultural suitability"""
        terrain_type = elevation_analysis.get("terrainType", "unknown")
        drainage = elevation_analysis.get("drainage", "unknown")
        agricultural_suitability = land_cover_analysis.get("agriculturalSuitability", "unknown")
        
        # Simple scoring system
        score = 0
        
        # Terrain scoring
        if terrain_type == "flat":
            score += 3
        elif terrain_type == "gentle":
            score += 2
        elif terrain_type == "moderate":
            score += 1
        
        # Drainage scoring
        if drainage == "good":
            score += 2
        elif drainage == "moderate":
            score += 1
        
        # Land cover scoring
        if agricultural_suitability == "high":
            score += 3
        elif agricultural_suitability == "medium":
            score += 2
        elif agricultural_suitability == "low":
            score += 1
        
        # Overall suitability
        if score >= 7:
            return "excellent"
        elif score >= 5:
            return "good"
        elif score >= 3:
            return "moderate"
        else:
            return "poor"
    
    def _generate_terrain_recommendations(self, elevation_analysis: Dict, land_cover_analysis: Dict) -> List[str]:
        """Generate terrain-based recommendations"""
        recommendations = []
        
        terrain_type = elevation_analysis.get("terrainType", "unknown")
        drainage = elevation_analysis.get("drainage", "unknown")
        agricultural_suitability = land_cover_analysis.get("agriculturalSuitability", "unknown")
        
        # Terrain-based recommendations
        if terrain_type == "flat":
            recommendations.append("Flat terrain - ideal for large-scale agriculture")
        elif terrain_type == "gentle":
            recommendations.append("Gentle slopes - suitable for most crops")
        elif terrain_type == "moderate":
            recommendations.append("Moderate slopes - consider contour farming")
        elif terrain_type == "steep":
            recommendations.append("Steep terrain - limited agricultural potential")
        
        # Drainage-based recommendations
        if drainage == "poor":
            recommendations.append("Poor drainage - implement drainage systems")
        elif drainage == "good":
            recommendations.append("Good drainage - suitable for most crops")
        
        # Land cover-based recommendations
        if agricultural_suitability == "high":
            recommendations.append("High agricultural suitability - excellent for farming")
        elif agricultural_suitability == "low":
            recommendations.append("Low agricultural suitability - consider land conversion")
        
        return recommendations
    
    def _identify_risk_factors(self, elevation_analysis: Dict, land_cover_analysis: Dict) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []
        
        terrain_type = elevation_analysis.get("terrainType", "unknown")
        drainage = elevation_analysis.get("drainage", "unknown")
        agricultural_suitability = land_cover_analysis.get("agriculturalSuitability", "unknown")
        
        # Terrain risks
        if terrain_type == "steep":
            risk_factors.append("Steep terrain - erosion risk")
        
        # Drainage risks
        if drainage == "poor":
            risk_factors.append("Poor drainage - waterlogging risk")
        
        # Land cover risks
        if agricultural_suitability == "low":
            risk_factors.append("Low agricultural suitability - conversion challenges")
        
        return risk_factors
    
    def _get_fallback_elevation(self) -> Dict[str, Any]:
        """Get fallback elevation data"""
        return {
            "success": False,
            "elevation": {
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "range": 0.0,
                "count": 0
            },
            "terrainCharacteristics": {
                "terrainType": "unknown",
                "terrainDescription": "Unable to determine terrain characteristics",
                "drainage": "unknown",
                "drainageDescription": "Unable to determine drainage characteristics"
            },
            "dataSource": "fallback",
            "resolution": "unknown",
            "warning": "Using fallback data - elevation analysis unavailable"
        }
    
    def _get_fallback_land_cover(self) -> Dict[str, Any]:
        """Get fallback land cover data"""
        return {
            "success": False,
            "landCover": {
                "distribution": {},
                "dominantClass": 0,
                "totalPixels": 0,
                "uniqueClasses": 0
            },
            "landCoverAnalysis": {
                "dominantLandCover": "Unknown",
                "agriculturalSuitability": "unknown",
                "agriculturalSuitabilityDescription": "Unable to determine agricultural suitability",
                "agriculturalPercentage": 0.0,
                "landCoverClasses": {}
            },
            "dataSource": "fallback",
            "resolution": "unknown",
            "warning": "Using fallback data - land cover analysis unavailable"
        }

# Create service instance
terrain_service = TerrainService()
