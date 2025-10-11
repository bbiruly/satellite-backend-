#!/usr/bin/env python3
"""
Create comprehensive NPK+Boron map showing all four nutrients
"""

import json
import folium
from folium import plugins

def create_comprehensive_npk_boron_map():
    """Create interactive map with Nitrogen, Phosphorus, Potassium, and Boron zones"""
    
    # Load village data
    with open('kanker_complete_soil_analysis_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Center point for map
    center_lat = 20.25
    center_lon = 81.35
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Define all zones
    nitrogen_zones = {
        "Yellow Zone (Low-Medium Nitrogen)": {
            "lat_range": (20.1, 20.58),
            "lon_range": (80.9, 81.4),
            "color": "yellow",
            "description": "Low-Medium Nitrogen areas"
        },
        "Red Zone (High/Very High Nitrogen)": {
            "lat_range": (20.05, 20.8),
            "lon_range": (81.25, 82.0),
            "color": "red",
            "description": "High/Very High Nitrogen areas"
        }
    }
    
    phosphorus_zones = {
        "Yellow Zone (Medium Phosphorus)": {
            "center_lat": 20.38,
            "center_lon": 81.45,
            "radius": 0.15,
            "color": "orange",
            "description": "Medium Phosphorus areas"
        },
        "Green Zone (High Phosphorus)": {
            "center_lat": 20.52,
            "center_lon": 81.62,
            "radius": 0.12,
            "color": "purple",
            "description": "High Phosphorus areas"
        }
    }
    
    potassium_zones = {
        "Green (Forest)": {
            "lat_range": (20.16, 20.33),
            "lon_range": (81.27, 81.49),
            "color": "green",
            "description": "Forest areas with high potassium"
        },
        "Yellow (Plain)": {
            "lat_range": (20.22, 20.30),
            "lon_range": (81.21, 81.49),
            "color": "lightgreen",
            "description": "Plain areas with medium potassium"
        }
    }
    
    boron_zones = {
        "Green Zone (Sufficient Boron)": {
            "lat_range": (20.20, 20.33),
            "lon_range": (81.30, 81.49),
            "color": "darkgreen",
            "description": "Sufficient boron areas"
        },
        "Red Zone (Deficient Boron)": {
            "lat_range": (20.16, 20.25),
            "lon_range": (81.21, 81.47),
            "color": "darkred",
            "description": "Deficient boron areas"
        }
    }
    
    # Add Nitrogen zones
    for zone_name, zone_info in nitrogen_zones.items():
        folium.Rectangle(
            bounds=[[zone_info["lat_range"][0], zone_info["lon_range"][0]], 
                   [zone_info["lat_range"][1], zone_info["lon_range"][1]]],
            color=zone_info["color"],
            weight=2,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.08,
            popup=f"<b>{zone_name}</b><br>{zone_info['description']}"
        ).add_to(m)
    
    # Add Phosphorus zones (circles)
    for zone_name, zone_info in phosphorus_zones.items():
        folium.Circle(
            location=[zone_info["center_lat"], zone_info["center_lon"]],
            radius=zone_info["radius"] * 111000,
            color=zone_info["color"],
            weight=2,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.12,
            popup=f"<b>{zone_name}</b><br>{zone_info['description']}"
        ).add_to(m)
    
    # Add Potassium zones
    for zone_name, zone_info in potassium_zones.items():
        folium.Rectangle(
            bounds=[[zone_info["lat_range"][0], zone_info["lon_range"][0]], 
                   [zone_info["lat_range"][1], zone_info["lon_range"][1]]],
            color=zone_info["color"],
            weight=2,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.08,
            popup=f"<b>{zone_name}</b><br>{zone_info['description']}"
        ).add_to(m)
    
    # Add Boron zones
    for zone_name, zone_info in boron_zones.items():
        folium.Rectangle(
            bounds=[[zone_info["lat_range"][0], zone_info["lon_range"][0]], 
                   [zone_info["lat_range"][1], zone_info["lon_range"][1]]],
            color=zone_info["color"],
            weight=2,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.08,
            popup=f"<b>{zone_name}</b><br>{zone_info['description']}"
        ).add_to(m)
    
    # Process villages and categorize by zones
    village_stats = {
        "nitrogen": {"yellow": 0, "red": 0},
        "phosphorus": {"yellow": 0, "green": 0, "low": 0},
        "potassium": {"green": 0, "yellow": 0, "low": 0},
        "boron": {"green": 0, "red": 0, "low": 0}
    }
    
    # Add village markers with comprehensive data
    for village in data['village_wise_data']['villages']:
        if 'coordinates' in village and len(village['coordinates']) == 2:
            lat, lon = village['coordinates']
            
            # Determine marker color based on primary nutrient (Nitrogen)
            nitrogen_level = village.get('nitrogen_level', 'Unknown')
            if nitrogen_level == 'Low':
                marker_color = 'lightblue'
            elif nitrogen_level == 'Low-Medium':
                marker_color = 'blue'
            elif nitrogen_level == 'Medium':
                marker_color = 'orange'
            elif nitrogen_level == 'High':
                marker_color = 'red'
            elif nitrogen_level == 'Very High':
                marker_color = 'darkred'
            else:
                marker_color = 'gray'
            
            # Count villages by zones
            nitrogen_zone = village.get('zone', 'unknown')
            phosphorus_zone = village.get('phosphorus_zone', 'Low Phosphorus')
            potassium_zone = village.get('potassium_zone', 'Low Potassium')
            boron_zone = village.get('boron_zone', 'Low Boron')
            
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
            
            # Create comprehensive popup
            popup_content = f"""
            <div style="width: 280px;">
                <h4 style="color: #333; margin: 5px 0;">{village['village_name']}</h4>
                <p><b>Population:</b> {village['population']:,}</p>
                
                <hr style="margin: 8px 0;">
                <h5 style="color: #2E8B57; margin: 5px 0;">🌱 Nitrogen</h5>
                <p><b>Level:</b> {village.get('nitrogen_level', 'N/A')}</p>
                <p><b>Range:</b> {village.get('estimated_nitrogen', 'N/A')}</p>
                <p><b>Zone:</b> {nitrogen_zone.title()}</p>
                
                <h5 style="color: #FFD700; margin: 5px 0;">🧪 Phosphorus</h5>
                <p><b>Level:</b> {village.get('phosphorus_level', 'N/A')}</p>
                <p><b>Range:</b> {village.get('estimated_phosphorus', 'N/A')}</p>
                <p><b>Zone:</b> {phosphorus_zone}</p>
                
                <h5 style="color: #228B22; margin: 5px 0;">🌿 Potassium</h5>
                <p><b>Level:</b> {village.get('potassium_level', 'N/A')}</p>
                <p><b>Range:</b> {village.get('estimated_potassium', 'N/A')}</p>
                <p><b>Zone:</b> {potassium_zone}</p>
                
                <h5 style="color: #8B4513; margin: 5px 0;">🔬 Boron</h5>
                <p><b>Level:</b> {village.get('boron_level', 'N/A')}</p>
                <p><b>Range:</b> {village.get('estimated_boron', 'N/A')}</p>
                <p><b>Zone:</b> {boron_zone}</p>
                
                <hr style="margin: 8px 0;">
                <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
            </div>
            """
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=marker_color, icon='info-sign', prefix='glyphicon'),
                tooltip=f"{village['village_name']} - N:{nitrogen_level}, P:{village.get('phosphorus_level', 'N/A')}, K:{village.get('potassium_level', 'N/A')}, B:{village.get('boron_level', 'N/A')}"
            ).add_to(m)
    
    # Add comprehensive legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 450px; height: 400px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; color: #333; text-align: center;">Kanker District NPK+Boron Zones</h4>
        
        <div style="margin: 4px 0;">
            <h5 style="color: #2E8B57; margin: 2px 0;">🌱 Nitrogen Zones:</h5>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: yellow;">■</span> Yellow Zone: {village_stats["nitrogen"]["yellow"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: red;">■</span> Red Zone: {village_stats["nitrogen"]["red"]} villages
            </div>
        </div>
        
        <div style="margin: 4px 0;">
            <h5 style="color: #FFD700; margin: 2px 0;">🧪 Phosphorus Zones:</h5>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: orange;">●</span> Yellow Zone: {village_stats["phosphorus"]["yellow"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: purple;">●</span> Green Zone: {village_stats["phosphorus"]["green"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: gray;">●</span> Low: {village_stats["phosphorus"]["low"]} villages
            </div>
        </div>
        
        <div style="margin: 4px 0;">
            <h5 style="color: #228B22; margin: 2px 0;">🌿 Potassium Zones:</h5>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: green;">■</span> Green (Forest): {village_stats["potassium"]["green"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: lightgreen;">■</span> Yellow (Plain): {village_stats["potassium"]["yellow"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: gray;">■</span> Low: {village_stats["potassium"]["low"]} villages
            </div>
        </div>
        
        <div style="margin: 4px 0;">
            <h5 style="color: #8B4513; margin: 2px 0;">🔬 Boron Zones:</h5>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: darkgreen;">■</span> Green (Sufficient): {village_stats["boron"]["green"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: darkred;">■</span> Red (Deficient): {village_stats["boron"]["red"]} villages
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: gray;">■</span> Low: {village_stats["boron"]["low"]} villages
            </div>
        </div>
        
        <hr style="margin: 6px 0;">
        
        <div style="margin: 4px 0;">
            <h5 style="color: #333; margin: 2px 0;">Village Markers:</h5>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: lightblue;">●</span> Low N
                <span style="color: blue; margin-left: 8px;">●</span> Low-Medium N
                <span style="color: orange; margin-left: 8px;">●</span> Medium N
            </div>
            <div style="margin: 2px 0; font-size: 10px;">
                <span style="color: red;">●</span> High N
                <span style="color: darkred; margin-left: 8px;">●</span> Very High N
            </div>
        </div>
        
        <div style="margin: 8px 0 0 0; padding: 6px; background-color: #f0f0f0; border-radius: 3px;">
            <p style="margin: 0; font-size: 10px; color: #666; text-align: center;">
                <b>Total Villages:</b> {len(data['village_wise_data']['villages'])} | 
                <b>Complete NPK+Boron Data</b>
            </p>
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    map_filename = "kanker_comprehensive_npk_boron_map.html"
    m.save(map_filename)
    
    print(f"✅ Comprehensive NPK+Boron Map Created: {map_filename}")
    print(f"   - Nitrogen Zones: {village_stats['nitrogen']['yellow']} Yellow + {village_stats['nitrogen']['red']} Red")
    print(f"   - Phosphorus Zones: {village_stats['phosphorus']['yellow']} Yellow + {village_stats['phosphorus']['green']} Green + {village_stats['phosphorus']['low']} Low")
    print(f"   - Potassium Zones: {village_stats['potassium']['green']} Green + {village_stats['potassium']['yellow']} Yellow + {village_stats['potassium']['low']} Low")
    print(f"   - Boron Zones: {village_stats['boron']['green']} Green + {village_stats['boron']['red']} Red + {village_stats['boron']['low']} Low")
    print(f"   - Total Villages: {len(data['village_wise_data']['villages'])}")
    
    return map_filename

if __name__ == "__main__":
    create_comprehensive_npk_boron_map()
