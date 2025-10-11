#!/usr/bin/env python3
"""
Restructure kanker_complete_soil_analysis_data.json for better organization
"""

import json
from datetime import datetime

def restructure_soil_analysis_data():
    """
    Restructure the soil analysis data for better organization and clarity
    """
    file_path = 'kanker_complete_soil_analysis_data.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return
    
    # Create new structured data
    restructured_data = {
        "metadata": {
            "district": "Kanker",
            "state": "Chhattisgarh",
            "country": "India",
            "data_source": "Soil & Land Use Survey of India + SHC Cycle-II + Zone Analysis",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "version": "2.0",
            "total_villages": len(data['village_wise_data']['villages']),
            "total_nutrients": 7,
            "nutrients_covered": ["Nitrogen", "Phosphorus", "Potassium", "Boron", "Iron", "Zinc", "Soil pH"]
        },
        
        "geographical_info": {
            "district_coordinates": {
                "center_lat": 20.25,
                "center_lon": 81.35,
                "bounding_box": {
                    "north": 20.33,
                    "south": 20.16,
                    "west": 81.15,
                    "east": 81.49
                }
            },
            "total_area_hectares": data.get('map_analysis', {}).get('total_area_hectares', 718248.64),
            "tehsils": ["Kanker"]
        },
        
        "nutrient_zones": {
            "nitrogen": {
                "yellow_zone": {
                    "name": "Yellow Zone (Low-Medium Nitrogen)",
                    "lat_range": [20.1, 20.58],
                    "lon_range": [80.9, 81.4],
                    "nitrogen_range": "280-420 kg/ha",
                    "villages_count": 45,
                    "description": "Low-Medium Nitrogen areas"
                },
                "red_zone": {
                    "name": "Red Zone (High/Very High Nitrogen)",
                    "lat_range": [20.05, 20.8],
                    "lon_range": [81.25, 82.0],
                    "nitrogen_range": "400-650 kg/ha",
                    "villages_count": 46,
                    "description": "High/Very High Nitrogen areas"
                }
            },
            "phosphorus": {
                "yellow_zone": {
                    "name": "Yellow Zone (Medium Phosphorus)",
                    "center_lat": 20.38,
                    "center_lon": 81.45,
                    "radius_km": 15,
                    "phosphorus_range": "15-25 kg/ha",
                    "villages_count": 10,
                    "description": "Medium Phosphorus areas"
                },
                "green_zone": {
                    "name": "Green Zone (High Phosphorus)",
                    "center_lat": 20.52,
                    "center_lon": 81.62,
                    "radius_km": 12,
                    "phosphorus_range": "25-40 kg/ha",
                    "villages_count": 5,
                    "description": "High Phosphorus areas"
                }
            },
            "potassium": {
                "green_forest": {
                    "name": "Green Zone (Forest - High Potassium)",
                    "lat_range": [20.16, 20.33],
                    "lon_range": [81.27, 81.49],
                    "potassium_range": "180-250 kg/ha",
                    "villages_count": 3,
                    "description": "Forest areas with high potassium"
                },
                "yellow_plain": {
                    "name": "Yellow Zone (Plain - Medium Potassium)",
                    "lat_range": [20.22, 20.30],
                    "lon_range": [81.21, 81.49],
                    "potassium_range": "120-180 kg/ha",
                    "villages_count": 8,
                    "description": "Plain areas with medium potassium"
                }
            },
            "boron": {
                "green_zone": {
                    "name": "Green Zone (Sufficient Boron)",
                    "lat_range": [20.20, 20.33],
                    "lon_range": [81.30, 81.49],
                    "boron_range": "0.5-1.2 ppm",
                    "villages_count": 1,
                    "description": "Sufficient boron areas"
                },
                "red_zone": {
                    "name": "Red Zone (Deficient Boron)",
                    "lat_range": [20.16, 20.25],
                    "lon_range": [81.21, 81.47],
                    "boron_range": "0.1-0.5 ppm",
                    "villages_count": 5,
                    "description": "Deficient boron areas"
                }
            },
            "iron": {
                "green_zone": {
                    "name": "Green Zone (Sufficient Iron)",
                    "lat_range": [20.16, 20.33],
                    "lon_range": [81.15, 81.49],
                    "iron_range": "4.5-15.0 ppm",
                    "villages_count": 11,
                    "description": "Most of Kanker tehsil with sufficient iron"
                },
                "red_spot": {
                    "name": "Red Spot (Deficient Iron)",
                    "lat_range": [20.20, 20.24],
                    "lon_range": [81.14, 81.18],
                    "iron_range": "1.0-4.5 ppm",
                    "villages_count": 0,
                    "description": "Small red spot area with deficient iron"
                }
            },
            "zinc": {
                "green_zone": {
                    "name": "Green Zone (Sufficient Zinc)",
                    "lat_range": [20.16, 20.33],
                    "lon_range": [81.15, 81.49],
                    "zinc_range": "0.6-2.0 ppm",
                    "villages_count": 11,
                    "description": "Majority tehsil forest cover with sufficient zinc"
                },
                "red_zones": {
                    "center_southwest": {
                        "name": "Red Zone Center-Southwest",
                        "lat_range": [20.22, 20.26],
                        "lon_range": [81.17, 81.32],
                        "zinc_range": "0.2-0.6 ppm",
                        "villages_count": 0,
                        "description": "Center-southwest red cluster with deficient zinc"
                    },
                    "northeast": {
                        "name": "Red Zone Northeast",
                        "lat_range": [20.30, 20.33],
                        "lon_range": [81.38, 81.49],
                        "zinc_range": "0.2-0.6 ppm",
                        "villages_count": 0,
                        "description": "Northeast borders red highlights with deficient zinc"
                    },
                    "northwest": {
                        "name": "Red Zone Northwest",
                        "lat_range": [20.30, 20.33],
                        "lon_range": [81.15, 81.21],
                        "zinc_range": "0.2-0.6 ppm",
                        "villages_count": 0,
                        "description": "Northwest border red zone with deficient zinc"
                    }
                }
            },
            "soil_ph": {
                "green_zone": {
                    "name": "Green Zone (Normal pH)",
                    "lat_range": [20.20, 20.32],
                    "lon_range": [81.15, 81.40],
                    "ph_range": "6.5-7.5",
                    "villages_count": 6,
                    "description": "Forest cover, dense vegetation with normal soil pH"
                },
                "orange_zone": {
                    "name": "Orange Zone (Slightly Acidic)",
                    "lat_range": [20.17, 20.30],
                    "lon_range": [81.21, 81.49],
                    "ph_range": "5.5-6.5",
                    "villages_count": 3,
                    "description": "Cultivated land, open area with slightly acidic soil pH"
                },
                "grey_zone": {
                    "name": "Grey Zone (Moderately Acidic)",
                    "lat_range": [20.20, 20.24],
                    "lon_range": [81.35, 81.41],
                    "ph_range": "4.5-5.5",
                    "villages_count": 1,
                    "description": "Special features, mining zone with moderately acidic soil pH"
                }
            }
        },
        
        "village_data": {
            "total_villages": len(data['village_wise_data']['villages']),
            "villages": []
        },
        
        "statistics": {
            "nutrient_distribution": {},
            "zone_summary": {},
            "recommendations": {}
        },
        
        "data_quality": {
            "source": "Soil & Land Use Survey of India + SHC Cycle-II + Zone Analysis",
            "methodology": "Bounding box zone assignment + Realistic nutrient ranges",
            "accuracy": "Zone-based approximation",
            "last_validation": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    # Process village data
    village_stats = {
        "nitrogen": {"yellow": 0, "red": 0},
        "phosphorus": {"yellow": 0, "green": 0, "low": 0},
        "potassium": {"green": 0, "yellow": 0, "low": 0},
        "boron": {"green": 0, "red": 0, "low": 0},
        "iron": {"green": 0, "red": 0, "low": 0},
        "zinc": {"green": 0, "red": 0, "low": 0},
        "soil_ph": {"green": 0, "orange": 0, "grey": 0, "low": 0}
    }
    
    for village in data['village_wise_data']['villages']:
        # Count villages by zones
        nitrogen_zone = village.get('zone', 'unknown')
        phosphorus_zone = village.get('phosphorus_zone', 'Low Phosphorus')
        potassium_zone = village.get('potassium_zone', 'Low Potassium')
        boron_zone = village.get('boron_zone', 'Low Boron')
        iron_zone = village.get('iron_zone', 'Low Iron')
        zinc_zone = village.get('zinc_zone', 'Low Zinc')
        soil_ph_zone = village.get('soil_ph_zone', 'Low pH')
        
        if nitrogen_zone == "Yellow Zone (Low-Medium Nitrogen)":
            village_stats["nitrogen"]["yellow"] += 1
        elif nitrogen_zone == "Red Zone (High/Very High Nitrogen)":
            village_stats["nitrogen"]["red"] += 1
            
        if 'Yellow' in phosphorus_zone:
            village_stats["phosphorus"]["yellow"] += 1
        elif 'Green' in phosphorus_zone:
            village_stats["phosphorus"]["green"] += 1
        else:
            village_stats["phosphorus"]["low"] += 1
            
        if 'Green' in potassium_zone:
            village_stats["potassium"]["green"] += 1
        elif 'Yellow' in potassium_zone:
            village_stats["potassium"]["yellow"] += 1
        else:
            village_stats["potassium"]["low"] += 1
            
        if 'Green' in boron_zone:
            village_stats["boron"]["green"] += 1
        elif 'Red' in boron_zone:
            village_stats["boron"]["red"] += 1
        else:
            village_stats["boron"]["low"] += 1
            
        if 'Green' in iron_zone:
            village_stats["iron"]["green"] += 1
        elif 'Red' in iron_zone:
            village_stats["iron"]["red"] += 1
        else:
            village_stats["iron"]["low"] += 1
            
        if 'Green' in zinc_zone:
            village_stats["zinc"]["green"] += 1
        elif 'Red' in zinc_zone:
            village_stats["zinc"]["red"] += 1
        else:
            village_stats["zinc"]["low"] += 1
            
        if 'Green' in soil_ph_zone:
            village_stats["soil_ph"]["green"] += 1
        elif 'Orange' in soil_ph_zone:
            village_stats["soil_ph"]["orange"] += 1
        elif 'Grey' in soil_ph_zone:
            village_stats["soil_ph"]["grey"] += 1
        else:
            village_stats["soil_ph"]["low"] += 1
        
        # Add village to restructured data
        restructured_data["village_data"]["villages"].append(village)
    
    # Add statistics
    restructured_data["statistics"]["nutrient_distribution"] = village_stats
    restructured_data["statistics"]["zone_summary"] = {
        "total_zones": 15,
        "nutrients_covered": 7,
        "coverage_percentage": "100% of Kanker tehsil"
    }
    
    # Add recommendations from original data
    if 'recommendations' in data:
        restructured_data["statistics"]["recommendations"] = data['recommendations']
    
    # Save restructured data
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(restructured_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully restructured {file_path}")
        print(f"   - Total Villages: {len(restructured_data['village_data']['villages'])}")
        print(f"   - Nutrients Covered: {len(restructured_data['metadata']['nutrients_covered'])}")
        print(f"   - Zones Defined: {restructured_data['statistics']['zone_summary']['total_zones']}")
        print(f"   - Structure: Improved organization with metadata, zones, and statistics")
        
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")

if __name__ == "__main__":
    restructure_soil_analysis_data()
