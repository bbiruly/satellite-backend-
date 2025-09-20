#!/usr/bin/env python3
"""
Complete 360-Degree Field Analysis
Uses ALL APIs for comprehensive agricultural insights
Field Coordinates: 21.813113, 82.015848
"""
import asyncio
import time
import sys
import os
from datetime import datetime

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from terrain_service import terrain_service
from sentinel_indices import compute_indices_and_npk_for_bbox
from weather_service import WeatherService

# Import all our API services
try:
    from crop_health_service import CropHealthService
    from recommendations_service import RecommendationsService
    from trends_service import TrendsService
except ImportError as e:
    print(f"Warning: Some services not available: {e}")

async def complete_360_analysis():
    """Complete 360-degree analysis using ALL APIs"""
    
    # Real field coordinates provided by user
    field_coordinates = [21.813113, 82.015848]
    field_id = f"complete-field-{int(time.time())}"
    
    print("🌾 COMPLETE 360-DEGREE FIELD ANALYSIS")
    print("=" * 80)
    print(f"📍 Field Coordinates: {field_coordinates}")
    print(f"🆔 Field ID: {field_id}")
    print(f"🕐 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Using ALL Available APIs for Comprehensive Analysis")
    print()
    
    # Create bounding box for satellite data (larger area for better data availability)
    bbox = {
        'minLat': field_coordinates[0] - 0.01,  # Increased from 0.001 to 0.01
        'maxLat': field_coordinates[0] + 0.01,
        'minLon': field_coordinates[1] - 0.01,
        'maxLon': field_coordinates[1] + 0.01
    }
    
    print("🔍 Starting 360-degree comprehensive analysis...")
    print()
    
    analysis_results = {}
    
    # 1. SATELLITE DATA ANALYSIS (Field Metrics API)
    print("1️⃣ SATELLITE DATA ANALYSIS (Field Metrics API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        satellite_data = compute_indices_and_npk_for_bbox(bbox)
        duration = time.time() - start_time
        
        if satellite_data.get('success'):
            print(f"✅ Satellite Data - SUCCESS ({duration:.2f}s)")
            print()
            
            # Satellite metadata
            print("📡 SATELLITE METADATA:")
            print(f"   • Satellite: {satellite_data.get('satelliteItem', 'Unknown')}")
            print(f"   • Image Date: {satellite_data.get('imageDate', 'Unknown')}")
            print(f"   • Cloud Cover: {satellite_data.get('cloudCover', 0):.1f}%")
            print(f"   • Data Source: Microsoft Planetary Computer")
            print()
            
            # Vegetation indices
            indices = satellite_data.get('indices', {})
            print("🌿 VEGETATION INDICES:")
            for index_name, index_data in indices.items():
                mean_val = index_data.get('mean', 0)
                median_val = index_data.get('median', 0)
                count = index_data.get('count', 0)
                print(f"   • {index_name}: {mean_val:.4f} (median: {median_val:.4f}, {count} pixels)")
            print()
            
            # NPK Analysis
            npk = satellite_data.get('npk', {})
            print("🧪 NPK ANALYSIS:")
            for nutrient, level in npk.items():
                print(f"   • {nutrient}: {level}")
            print()
            
            analysis_results['satellite'] = satellite_data
            
        else:
            print(f"❌ Satellite Data - FAILED ({duration:.2f}s)")
            print(f"   Error: {satellite_data.get('error', 'Unknown error')}")
            print()
            analysis_results['satellite'] = None
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Satellite Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['satellite'] = None
    
    # 2. WEATHER DATA ANALYSIS (Weather API)
    print("2️⃣ WEATHER DATA ANALYSIS (Weather API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        weather_service = WeatherService()
        weather_data = await weather_service.get_current_weather(field_coordinates[0], field_coordinates[1])
        duration = time.time() - start_time
        
        if weather_data and weather_data.get('temperature', 0) != 0:
            print(f"✅ Weather Data - SUCCESS ({duration:.2f}s)")
            print()
            
            print("🌤️ CURRENT WEATHER:")
            print(f"   • Temperature: {weather_data.get('temperature', 0):.1f}°C")
            print(f"   • Humidity: {weather_data.get('humidity', 0)}%")
            print(f"   • Pressure: {weather_data.get('pressure', 0)} hPa")
            print(f"   • Wind Speed: {weather_data.get('wind_speed', 0)} km/h")
            print(f"   • Wind Direction: {weather_data.get('wind_direction', 0)}°")
            print(f"   • Visibility: {weather_data.get('visibility', 0)} km")
            print(f"   • UV Index: {weather_data.get('uv_index', 0)}")
            print(f"   • Cloud Cover: {weather_data.get('cloud_cover', 0)}%")
            print(f"   • Data Source: WeatherAPI.com")
            print()
            
            analysis_results['weather'] = weather_data
            
        else:
            print(f"⚠️ Weather Data - Using fallback ({duration:.2f}s)")
            print(f"   Warning: Weather API returned invalid data (temperature: {weather_data.get('temperature', 0) if weather_data else 'None'})")
            print()
            analysis_results['weather'] = None
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Weather Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['weather'] = None
    
    # 3. ELEVATION ANALYSIS (Terrain API)
    print("3️⃣ ELEVATION ANALYSIS (Terrain API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        elevation_data = await terrain_service.get_elevation_analysis(field_coordinates)
        duration = time.time() - start_time
        
        if elevation_data.get('success'):
            print(f"✅ Elevation Data - SUCCESS ({duration:.2f}s)")
            print()
            
            elevation = elevation_data.get('elevation', {})
            terrain = elevation_data.get('terrainCharacteristics', {})
            
            print("🏔️ ELEVATION DETAILS:")
            print(f"   • Mean Elevation: {elevation.get('mean', 0):.1f}m")
            print(f"   • Elevation Range: {elevation.get('min', 0):.1f}m - {elevation.get('max', 0):.1f}m")
            print(f"   • Elevation Variation: {elevation.get('std', 0):.1f}m")
            print(f"   • Total Range: {elevation.get('range', 0):.1f}m")
            print(f"   • Pixels Analyzed: {elevation.get('count', 0)}")
            print()
            
            print("🌄 TERRAIN CHARACTERISTICS:")
            print(f"   • Terrain Type: {terrain.get('terrainType', 'unknown')}")
            print(f"   • Description: {terrain.get('terrainDescription', 'unknown')}")
            print(f"   • Drainage: {terrain.get('drainage', 'unknown')}")
            print(f"   • Drainage Description: {terrain.get('drainageDescription', 'unknown')}")
            print(f"   • Data Source: {elevation_data.get('dataSource', 'unknown')}")
            print()
            
            analysis_results['elevation'] = elevation_data
            
        else:
            print(f"⚠️ Elevation Data - Using fallback ({duration:.2f}s)")
            print(f"   Warning: {elevation_data.get('warning', 'No warning')}")
            print()
            analysis_results['elevation'] = elevation_data
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Elevation Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['elevation'] = None
    
    # 4. LAND COVER ANALYSIS (Terrain API)
    print("4️⃣ LAND COVER ANALYSIS (Terrain API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        land_cover_data = await terrain_service.get_land_cover_analysis(field_coordinates)
        duration = time.time() - start_time
        
        if land_cover_data.get('success'):
            print(f"✅ Land Cover Data - SUCCESS ({duration:.2f}s)")
            print()
            
            land_cover = land_cover_data.get('landCover', {})
            analysis = land_cover_data.get('landCoverAnalysis', {})
            
            print("🌍 LAND COVER DETAILS:")
            print(f"   • Dominant Land Cover: {analysis.get('dominantLandCover', 'unknown')}")
            print(f"   • Agricultural Suitability: {analysis.get('agriculturalSuitability', 'unknown')}")
            print(f"   • Agricultural Percentage: {analysis.get('agriculturalPercentage', 0):.1f}%")
            print(f"   • Total Pixels: {land_cover.get('totalPixels', 0)}")
            print(f"   • Unique Classes: {land_cover.get('uniqueClasses', 0)}")
            print(f"   • Data Source: {land_cover_data.get('dataSource', 'unknown')}")
            print()
            
            # Land cover distribution
            distribution = land_cover.get('distribution', {})
            if distribution:
                print("📊 LAND COVER DISTRIBUTION:")
                for class_id, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / land_cover.get('totalPixels', 1)) * 100
                    print(f"   • Class {class_id}: {count} pixels ({percentage:.1f}%)")
                print()
            
            analysis_results['land_cover'] = land_cover_data
            
        else:
            print(f"⚠️ Land Cover Data - Using fallback ({duration:.2f}s)")
            print(f"   Warning: {land_cover_data.get('warning', 'No warning')}")
            print()
            analysis_results['land_cover'] = land_cover_data
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Land Cover Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['land_cover'] = None
    
    # 5. CROP HEALTH ANALYSIS (Crop Health API)
    print("5️⃣ CROP HEALTH ANALYSIS (Crop Health API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        crop_health_service = CropHealthService()
        crop_health_data = await crop_health_service.get_crop_health_analysis(field_id, field_coordinates, "general")
        duration = time.time() - start_time
        
        if crop_health_data:
            print(f"✅ Crop Health Data - SUCCESS ({duration:.2f}s)")
            print()
            
            print("🌱 CROP HEALTH METRICS:")
            print(f"   • Overall Health Score: {crop_health_data.overall_health_score:.1f}")
            print(f"   • Stress Level: {crop_health_data.stress_level}")
            print(f"   • Growth Stage: {crop_health_data.growth_stage}")
            print(f"   • Quality Score: {crop_health_data.quality_score:.1f}")
            print(f"   • Disease Risk: {crop_health_data.disease_risk}")
            print(f"   • Pest Risk: {crop_health_data.pest_risk}")
            print()
            
            print("💧 STRESS ANALYSIS:")
            print(f"   • Water Stress: {crop_health_data.water_stress}")
            print(f"   • Nutrient Stress: {crop_health_data.nutrient_stress}")
            print(f"   • Temperature Stress: {crop_health_data.temperature_stress}")
            print()
            
            print("📊 VEGETATION INDICES:")
            indices = crop_health_data.vegetation_indices
            print(f"   • NDVI: {indices.get('NDVI', 0):.4f}")
            print(f"   • NDMI: {indices.get('NDMI', 0):.4f}")
            print(f"   • SAVI: {indices.get('SAVI', 0):.4f}")
            print(f"   • NDWI: {indices.get('NDWI', 0):.4f}")
            print()
            
            analysis_results['crop_health'] = crop_health_data
            
        else:
            print(f"❌ Crop Health Data - FAILED ({duration:.2f}s)")
            print()
            analysis_results['crop_health'] = None
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Crop Health Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['crop_health'] = None
    
    # 6. RECOMMENDATIONS ANALYSIS (Recommendations API)
    print("6️⃣ RECOMMENDATIONS ANALYSIS (Recommendations API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        recommendations_service = RecommendationsService()
        recommendations_data = await recommendations_service.get_field_recommendations(field_id, {}, {}, field_coordinates)
        duration = time.time() - start_time
        
        if recommendations_data:
            print(f"✅ Recommendations Data - SUCCESS ({duration:.2f}s)")
            print()
            
            print("💡 FERTILIZER RECOMMENDATIONS:")
            fertilizer = recommendations_data.get('fertilizer', {})
            if fertilizer:
                print(f"   • Priority: {fertilizer.get('priority', 'unknown')}")
                print(f"   • Recommendation: {fertilizer.get('recommendation', 'unknown')}")
                print(f"   • Reason: {fertilizer.get('reason', 'unknown')}")
            print()
            
            print("💧 IRRIGATION RECOMMENDATIONS:")
            irrigation = recommendations_data.get('irrigation', {})
            if irrigation:
                print(f"   • Priority: {irrigation.get('priority', 'unknown')}")
                print(f"   • Recommendation: {irrigation.get('recommendation', 'unknown')}")
                print(f"   • Reason: {irrigation.get('reason', 'unknown')}")
            print()
            
            print("🌱 CROP HEALTH RECOMMENDATIONS:")
            crop_health_rec = recommendations_data.get('cropHealth', {})
            if crop_health_rec:
                print(f"   • Priority: {crop_health_rec.get('priority', 'unknown')}")
                print(f"   • Recommendation: {crop_health_rec.get('recommendation', 'unknown')}")
                print(f"   • Reason: {crop_health_rec.get('reason', 'unknown')}")
            print()
            
            print("⚠️ RISK ALERTS:")
            risk_alerts = recommendations_data.get('riskAlerts', [])
            if risk_alerts:
                for i, alert in enumerate(risk_alerts, 1):
                    print(f"   {i}. {alert.get('alert', 'Unknown alert')}")
            else:
                print("   • No risk alerts")
            print()
            
            analysis_results['recommendations'] = recommendations_data
            
        else:
            print(f"❌ Recommendations Data - FAILED ({duration:.2f}s)")
            print()
            analysis_results['recommendations'] = None
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Recommendations Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['recommendations'] = None
    
    # 7. TRENDS ANALYSIS (Trends API)
    print("7️⃣ TRENDS ANALYSIS (Trends API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        trends_service = TrendsService()
        trends_data = await trends_service.get_field_trends(field_id, field_coordinates, "30d", "comprehensive")
        duration = time.time() - start_time
        
        if trends_data:
            print(f"✅ Trends Data - SUCCESS ({duration:.2f}s)")
            print()
            
            print("📈 VEGETATION TRENDS:")
            vegetation_trends = trends_data.get('vegetationTrends', {})
            if vegetation_trends:
                print(f"   • NDVI Trend: {vegetation_trends.get('ndviTrend', 'unknown')}")
                print(f"   • NDMI Trend: {vegetation_trends.get('ndmiTrend', 'unknown')}")
                print(f"   • SAVI Trend: {vegetation_trends.get('saviTrend', 'unknown')}")
                print(f"   • NDWI Trend: {vegetation_trends.get('ndwiTrend', 'unknown')}")
            print()
            
            print("🌤️ WEATHER TRENDS:")
            weather_trends = trends_data.get('weatherTrends', {})
            if weather_trends:
                print(f"   • Temperature Trend: {weather_trends.get('temperatureTrend', 'unknown')}")
                print(f"   • Humidity Trend: {weather_trends.get('humidityTrend', 'unknown')}")
                print(f"   • Precipitation Trend: {weather_trends.get('precipitationTrend', 'unknown')}")
            print()
            
            print("📊 PERFORMANCE METRICS:")
            performance = trends_data.get('performanceMetrics', {})
            if performance:
                print(f"   • Health Score Trend: {performance.get('healthScoreTrend', 'unknown')}")
                print(f"   • Stress Level Trend: {performance.get('stressLevelTrend', 'unknown')}")
                print(f"   • Quality Score Trend: {performance.get('qualityScoreTrend', 'unknown')}")
            print()
            
            analysis_results['trends'] = trends_data
            
        else:
            print(f"❌ Trends Data - FAILED ({duration:.2f}s)")
            print()
            analysis_results['trends'] = None
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Trends Data - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['trends'] = None
    
    # 8. COMPREHENSIVE TERRAIN ANALYSIS (Terrain API)
    print("8️⃣ COMPREHENSIVE TERRAIN ANALYSIS (Terrain API)")
    print("-" * 60)
    start_time = time.time()
    
    try:
        terrain_data = await terrain_service.get_comprehensive_terrain_analysis(field_coordinates)
        duration = time.time() - start_time
        
        if terrain_data.get('success'):
            print(f"✅ Comprehensive Terrain - SUCCESS ({duration:.2f}s)")
            print()
            
            terrain_analysis = terrain_data.get('terrainAnalysis', {})
            
            print("🎯 OVERALL FIELD ASSESSMENT:")
            print(f"   • Overall Suitability: {terrain_analysis.get('overallSuitability', 'unknown')}")
            print()
            
            # Recommendations
            recommendations = terrain_analysis.get('recommendations', [])
            if recommendations:
                print("💡 TERRAIN RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
                print()
            
            # Risk factors
            risk_factors = terrain_analysis.get('riskFactors', [])
            if risk_factors:
                print("⚠️ TERRAIN RISK FACTORS:")
                for i, risk in enumerate(risk_factors, 1):
                    print(f"   {i}. {risk}")
                print()
            
            analysis_results['terrain'] = terrain_data
            
        else:
            print(f"❌ Comprehensive Terrain - FAILED ({duration:.2f}s)")
            print(f"   Error: {terrain_data.get('error', 'Unknown error')}")
            print()
            analysis_results['terrain'] = terrain_data
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Comprehensive Terrain - ERROR ({duration:.2f}s)")
        print(f"   Error: {str(e)}")
        print()
        analysis_results['terrain'] = None
    
    # 9. COMPREHENSIVE ANALYSIS SUMMARY
    print("9️⃣ COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 80)
    
    print("📍 FIELD INFORMATION:")
    print(f"   • Coordinates: {field_coordinates}")
    print(f"   • Field ID: {field_id}")
    print(f"   • Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Analysis Type: Complete 360-Degree Analysis")
    print()
    
    print("📊 DATA SOURCES USED:")
    print("   • Satellite Data: Microsoft Planetary Computer (Sentinel-2)")
    print("   • Weather Data: WeatherAPI.com")
    print("   • Elevation Data: Copernicus DEM GLO-30")
    print("   • Land Cover Data: ESA WorldCover")
    print("   • Crop Health: Advanced algorithms + satellite data")
    print("   • Recommendations: AI-powered agricultural advice")
    print("   • Trends: Historical data analysis")
    print("   • Terrain: Comprehensive terrain analysis")
    print()
    
    print("🎯 KEY FINDINGS SUMMARY:")
    
    # Satellite findings
    if analysis_results.get('satellite'):
        print("   ✅ Real satellite data successfully processed")
        indices = analysis_results['satellite'].get('indices', {})
        if indices:
            ndvi = indices.get('NDVI', {}).get('mean', 0)
            print(f"   ✅ Vegetation health (NDVI): {ndvi:.4f}")
    else:
        print("   ❌ Satellite data processing failed")
    
    # Weather findings
    if analysis_results.get('weather'):
        print("   ✅ Current weather conditions retrieved")
        temp = analysis_results['weather'].get('temperature', 0)
        print(f"   ✅ Current temperature: {temp:.1f}°C")
    else:
        print("   ❌ Weather data unavailable")
    
    # Elevation findings
    if analysis_results.get('elevation'):
        elevation = analysis_results['elevation'].get('elevation', {})
        terrain = analysis_results['elevation'].get('terrainCharacteristics', {})
        if elevation.get('mean'):
            print(f"   ✅ Elevation: {elevation.get('mean', 0):.1f}m")
            print(f"   ✅ Terrain type: {terrain.get('terrainType', 'unknown')}")
    
    # Land cover findings
    if analysis_results.get('land_cover'):
        analysis = analysis_results['land_cover'].get('landCoverAnalysis', {})
        print(f"   ✅ Land cover: {analysis.get('dominantLandCover', 'unknown')}")
        print(f"   ✅ Agricultural suitability: {analysis.get('agriculturalSuitability', 'unknown')}")
    
    # Crop health findings
    if analysis_results.get('crop_health'):
        health = analysis_results['crop_health']
        print(f"   ✅ Crop health score: {health.overall_health_score:.1f}")
        print(f"   ✅ Stress level: {health.stress_level}")
        print(f"   ✅ Growth stage: {health.growth_stage}")
    
    # Recommendations findings
    if analysis_results.get('recommendations'):
        print("   ✅ AI-powered recommendations generated")
        fertilizer = analysis_results['recommendations'].get('fertilizer', {})
        if fertilizer:
            print(f"   ✅ Fertilizer priority: {fertilizer.get('priority', 'unknown')}")
    
    # Trends findings
    if analysis_results.get('trends'):
        print("   ✅ Historical trends analysis completed")
    
    # Terrain findings
    if analysis_results.get('terrain'):
        terrain_analysis = analysis_results['terrain'].get('terrainAnalysis', {})
        print(f"   ✅ Overall suitability: {terrain_analysis.get('overallSuitability', 'unknown')}")
    
    print()
    
    # 10. ACTIONABLE INSIGHTS
    print("🔟 ACTIONABLE INSIGHTS & RECOMMENDATIONS")
    print("=" * 80)
    
    print("🌱 IMMEDIATE ACTIONS:")
    
    # Based on elevation analysis
    if analysis_results.get('elevation'):
        terrain = analysis_results['elevation'].get('terrainCharacteristics', {})
        drainage = terrain.get('drainage', 'unknown')
        if drainage == 'poor':
            print("   1. ⚠️ Implement drainage systems - poor drainage detected")
        elif drainage == 'good':
            print("   1. ✅ Drainage is good - no immediate action needed")
    
    # Based on land cover analysis
    if analysis_results.get('land_cover'):
        analysis = analysis_results['land_cover'].get('landCoverAnalysis', {})
        suitability = analysis.get('agriculturalSuitability', 'unknown')
        if suitability == 'high':
            print("   2. ✅ Excellent agricultural land - optimize farming practices")
        elif suitability == 'low':
            print("   2. ⚠️ Low agricultural suitability - consider land improvement")
    
    # Based on crop health analysis
    if analysis_results.get('crop_health'):
        health = analysis_results['crop_health']
        if health.stress_level in ['high', 'critical']:
            print("   3. 🚨 High stress detected - immediate intervention needed")
        elif health.stress_level == 'medium':
            print("   3. ⚠️ Moderate stress - monitor closely")
        else:
            print("   3. ✅ Low stress - maintain current practices")
    
    # Based on recommendations
    if analysis_results.get('recommendations'):
        fertilizer = analysis_results['recommendations'].get('fertilizer', {})
        irrigation = analysis_results['recommendations'].get('irrigation', {})
        if fertilizer and fertilizer.get('priority') == 'high':
            print("   4. 🧪 High priority fertilizer application needed")
        if irrigation and irrigation.get('priority') == 'high':
            print("   4. 💧 High priority irrigation needed")
    
    print()
    
    print("📈 LONG-TERM STRATEGY:")
    print("   1. 📊 Monitor vegetation indices weekly")
    print("   2. 🌤️ Track weather patterns and adjust irrigation")
    print("   3. 🏔️ Consider terrain characteristics in farming decisions")
    print("   4. 🌱 Implement crop health monitoring system")
    print("   5. 💡 Follow AI-powered recommendations")
    print("   6. 📈 Analyze trends for seasonal planning")
    print()
    
    print("🎯 SUCCESS METRICS TO TRACK:")
    print("   • Vegetation health (NDVI)")
    print("   • Crop stress levels")
    print("   • Soil moisture content")
    print("   • Weather impact on crops")
    print("   • Overall field productivity")
    print()
    
    print("🌱 Complete 360-Degree Field Analysis Finished!")
    print("=" * 80)
    
    return analysis_results

if __name__ == "__main__":
    asyncio.run(complete_360_analysis())
