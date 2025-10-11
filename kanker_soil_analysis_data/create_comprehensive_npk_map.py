#!/usr/bin/env python3
"""
Create comprehensive NPK map showing all three nutrients
"""

import json
import folium
from folium import plugins

def create_comprehensive_npk_map():
    """Create interactive map with Nitrogen, Phosphorus, and Potassium zones"""
    
    # Load village data
    with open('kanker_complete_soil_analysis_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Center point for map
    center_lat = 20.4
    center_lon = 81.5
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
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
    
    # Add Nitrogen zones
    for zone_name, zone_info in nitrogen_zones.items():
        folium.Rectangle(
            bounds=[[zone_info["lat_range"][0], zone_info["lon_range"][0]], 
                   [zone_info["lat_range"][1], zone_info["lon_range"][1]]],
            color=zone_info["color"],
            weight=2,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.1,
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
            fillOpacity=0.15,
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
            fillOpacity=0.1,
            popup=f"<b>{zone_name}</b><br>{zone_info['description']}"
        ).add_to(m)
    
    # Process villages and categorize by zones
    village_stats = {
        "nitrogen": {"yellow": 0, "red": 0},
        "phosphorus": {"yellow": 0, "green": 0, "low": 0},
        "potassium": {"green": 0, "yellow": 0, "low": 0}
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
            
            # Create comprehensive popup
            popup_content = f"""
            <div style="width: 250px;">
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
                
                <hr style="margin: 8px 0;">
                <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
            </div>
            """
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_content, max_width=280),
                icon=folium.Icon(color=marker_color, icon='info-sign', prefix='glyphicon'),
                tooltip=f"{village['village_name']} - N:{nitrogen_level}, P:{village.get('phosphorus_level', 'N/A')}, K:{village.get('potassium_level', 'N/A')}"
            ).add_to(m)
    
    # Add comprehensive legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 400px; height: 350px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:13px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; color: #333; text-align: center;">Kanker District NPK Zones</h4>
        
        <div style="margin: 5px 0;">
            <h5 style="color: #2E8B57; margin: 3px 0;">🌱 Nitrogen Zones:</h5>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: yellow;">■</span> Yellow Zone (Low-Medium): {village_stats["nitrogen"]["yellow"]} villages
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: red;">■</span> Red Zone (High/Very High): {village_stats["nitrogen"]["red"]} villages
            </div>
        </div>
        
        <div style="margin: 5px 0;">
            <h5 style="color: #FFD700; margin: 3px 0;">🧪 Phosphorus Zones:</h5>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: orange;">●</span> Yellow Zone (Medium): {village_stats["phosphorus"]["yellow"]} villages
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: purple;">●</span> Green Zone (High): {village_stats["phosphorus"]["green"]} villages
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: gray;">●</span> Low Phosphorus: {village_stats["phosphorus"]["low"]} villages
            </div>
        </div>
        
        <div style="margin: 5px 0;">
            <h5 style="color: #228B22; margin: 3px 0;">🌿 Potassium Zones:</h5>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: green;">■</span> Green (Forest): {village_stats["potassium"]["green"]} villages
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: lightgreen;">■</span> Yellow (Plain): {village_stats["potassium"]["yellow"]} villages
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: gray;">■</span> Low Potassium: {village_stats["potassium"]["low"]} villages
            </div>
        </div>
        
        <hr style="margin: 8px 0;">
        
        <div style="margin: 5px 0;">
            <h5 style="color: #333; margin: 3px 0;">Village Markers:</h5>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: lightblue;">●</span> Low N
                <span style="color: blue; margin-left: 10px;">●</span> Low-Medium N
                <span style="color: orange; margin-left: 10px;">●</span> Medium N
            </div>
            <div style="margin: 3px 0; font-size: 11px;">
                <span style="color: red;">●</span> High N
                <span style="color: darkred; margin-left: 10px;">●</span> Very High N
            </div>
        </div>
        
        <div style="margin: 10px 0 0 0; padding: 8px; background-color: #f0f0f0; border-radius: 3px;">
            <p style="margin: 0; font-size: 11px; color: #666; text-align: center;">
                <b>Total Villages:</b> {len(data['village_wise_data']['villages'])} | 
                <b>Complete NPK Data</b>
            </p>
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    map_filename = "kanker_comprehensive_npk_map.html"
    m.save(map_filename)
    
    print(f"✅ Comprehensive NPK Map Created: {map_filename}")
    print(f"   - Nitrogen Zones: {village_stats['nitrogen']['yellow']} Yellow + {village_stats['nitrogen']['red']} Red")
    print(f"   - Phosphorus Zones: {village_stats['phosphorus']['yellow']} Yellow + {village_stats['phosphorus']['green']} Green + {village_stats['phosphorus']['low']} Low")
    print(f"   - Potassium Zones: {village_stats['potassium']['green']} Green + {village_stats['potassium']['yellow']} Yellow + {village_stats['potassium']['low']} Low")
    print(f"   - Total Villages: {len(data['village_wise_data']['villages'])}")
    
    return map_filename

if __name__ == "__main__":
    create_comprehensive_npk_map()
