#!/usr/bin/env python3
"""
Create interactive map showing Phosphorus zones and village data
"""

import json
import folium
from folium import plugins

def create_phosphorus_zone_map():
    """Create interactive map with Phosphorus zones and village data"""
    
    # Load village data
    with open('kanker_complete_soil_analysis_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Center point for map
    center_lat = 20.45
    center_lon = 81.5
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Define Phosphorus Zones
    phosphorus_zones = {
        "Yellow Zone (Medium Phosphorus)": {
            "center_lat": 20.38,
            "center_lon": 81.45,
            "radius": 0.15,  # degrees
            "color": "yellow",
            "description": "Southwestern & southern side of Kanker tehsil"
        },
        "Green Zone (High Phosphorus)": {
            "center_lat": 20.52,
            "center_lon": 81.62,
            "radius": 0.12,  # degrees
            "color": "green",
            "description": "Central-eastern and northeastern part of Kanker tehsil"
        }
    }
    
    # Add Phosphorus Zone circles
    for zone_name, zone_info in phosphorus_zones.items():
        folium.Circle(
            location=[zone_info["center_lat"], zone_info["center_lon"]],
            radius=zone_info["radius"] * 111000,  # Convert degrees to meters
            color=zone_info["color"],
            weight=3,
            fill=True,
            fillColor=zone_info["color"],
            fillOpacity=0.2,
            popup=f"""
            <div style="width: 250px;">
                <h4 style="color: {zone_info['color']}; margin: 5px 0;">{zone_name}</h4>
                <p><b>Coordinates:</b> {zone_info['center_lat']:.2f}°N, {zone_info['center_lon']:.2f}°E</p>
                <p><b>Description:</b> {zone_info['description']}</p>
                <p><b>Phosphorus Level:</b> {zone_name.split('(')[1].split(')')[0]}</p>
            </div>
            """
        ).add_to(m)
        
        # Add zone center markers
        folium.Marker(
            [zone_info["center_lat"], zone_info["center_lon"]],
            popup=f"<b>{zone_name}</b><br>Center Point",
            icon=folium.Icon(color=zone_info["color"], icon='star', prefix='glyphicon'),
            tooltip=f"{zone_name} Center"
        ).add_to(m)
    
    # Process villages
    yellow_zone_villages = []
    green_zone_villages = []
    low_phosphorus_villages = []
    
    for village in data['village_wise_data']['villages']:
        if 'coordinates' in village and len(village['coordinates']) == 2:
            lat, lon = village['coordinates']
            phosphorus_zone = village.get('phosphorus_zone', 'Low Phosphorus')
            
            if phosphorus_zone == "Yellow #1 (Medium Phosphorus)":
                yellow_zone_villages.append(village)
            elif phosphorus_zone == "Green #1 (High Phosphorus)":
                green_zone_villages.append(village)
            else:
                low_phosphorus_villages.append(village)
    
    # Add Yellow Zone villages
    for village in yellow_zone_villages:
        lat, lon = village['coordinates']
        
        popup_content = f"""
        <div style="width: 220px;">
            <h4 style="color: #FFD700; margin: 5px 0;">{village['village_name']}</h4>
            <p><b>Population:</b> {village['population']:,}</p>
            <p><b>Nitrogen Level:</b> {village.get('nitrogen_level', 'N/A')}</p>
            <p><b>Phosphorus Level:</b> <span style="color: #FFD700; font-weight: bold;">{village.get('phosphorus_level', 'N/A')}</span></p>
            <p><b>Estimated Phosphorus:</b> {village.get('estimated_phosphorus', 'N/A')}</p>
            <p><b>Zone:</b> <span style="color: #FFD700; font-weight: bold;">YELLOW ZONE</span></p>
            <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color='yellow', icon='info-sign', prefix='glyphicon'),
            tooltip=f"Yellow Zone: {village['village_name']}"
        ).add_to(m)
    
    # Add Green Zone villages
    for village in green_zone_villages:
        lat, lon = village['coordinates']
        
        popup_content = f"""
        <div style="width: 220px;">
            <h4 style="color: #228B22; margin: 5px 0;">{village['village_name']}</h4>
            <p><b>Population:</b> {village['population']:,}</p>
            <p><b>Nitrogen Level:</b> {village.get('nitrogen_level', 'N/A')}</p>
            <p><b>Phosphorus Level:</b> <span style="color: #228B22; font-weight: bold;">{village.get('phosphorus_level', 'N/A')}</span></p>
            <p><b>Estimated Phosphorus:</b> {village.get('estimated_phosphorus', 'N/A')}</p>
            <p><b>Zone:</b> <span style="color: #228B22; font-weight: bold;">GREEN ZONE</span></p>
            <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color='green', icon='info-sign', prefix='glyphicon'),
            tooltip=f"Green Zone: {village['village_name']}"
        ).add_to(m)
    
    # Add Low Phosphorus villages (sample only to avoid overcrowding)
    sample_low_villages = low_phosphorus_villages[:20]  # Show only first 20
    for village in sample_low_villages:
        lat, lon = village['coordinates']
        
        popup_content = f"""
        <div style="width: 220px;">
            <h4 style="color: #666; margin: 5px 0;">{village['village_name']}</h4>
            <p><b>Population:</b> {village['population']:,}</p>
            <p><b>Nitrogen Level:</b> {village.get('nitrogen_level', 'N/A')}</p>
            <p><b>Phosphorus Level:</b> <span style="color: #666; font-weight: bold;">{village.get('phosphorus_level', 'N/A')}</span></p>
            <p><b>Estimated Phosphorus:</b> {village.get('estimated_phosphorus', 'N/A')}</p>
            <p><b>Zone:</b> <span style="color: #666; font-weight: bold;">LOW PHOSPHORUS</span></p>
            <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color='lightgray', icon='info-sign', prefix='glyphicon'),
            tooltip=f"Low Phosphorus: {village['village_name']}"
        ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 350px; height: 280px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; color: #333; text-align: center;">Kanker Phosphorus Zones</h4>
        
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <i class="fa fa-circle fa-2x" style="color: #FFD700; margin-right: 10px;"></i> 
            <span><b>Yellow Zone</b> (Medium Phosphorus)</span>
        </div>
        
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <i class="fa fa-circle fa-2x" style="color: #228B22; margin-right: 10px;"></i> 
            <span><b>Green Zone</b> (High Phosphorus)</span>
        </div>
        
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <i class="fa fa-circle fa-2x" style="color: lightgray; margin-right: 10px;"></i> 
            <span><b>Low Phosphorus</b> Areas</span>
        </div>
        
        <hr style="margin: 10px 0;">
        
        <h5 style="margin: 8px 0; color: #333;">Phosphorus Ranges:</h5>
        <div style="margin: 5px 0; font-size: 12px;">
            <span><b>Low:</b> 8-20 kg/ha</span>
        </div>
        <div style="margin: 5px 0; font-size: 12px;">
            <span><b>Medium:</b> 15-25 kg/ha</span>
        </div>
        <div style="margin: 5px 0; font-size: 12px;">
            <span><b>High:</b> 25-40 kg/ha</span>
        </div>
        
        <div style="margin: 10px 0 0 0; padding: 8px; background-color: #f0f0f0; border-radius: 3px;">
            <p style="margin: 0; font-size: 12px; color: #666; text-align: center;">
                <b>Village Count:</b> {len(yellow_zone_villages)} Yellow + {len(green_zone_villages)} Green + {len(low_phosphorus_villages)} Low
            </p>
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    map_filename = "kanker_phosphorus_zones_map.html"
    m.save(map_filename)
    
    print(f"✅ Phosphorus Zone Map Created: {map_filename}")
    print(f"   - Yellow Zone: {len(yellow_zone_villages)} villages")
    print(f"   - Green Zone: {len(green_zone_villages)} villages")
    print(f"   - Low Phosphorus: {len(low_phosphorus_villages)} villages")
    print(f"   - Total: {len(yellow_zone_villages) + len(green_zone_villages) + len(low_phosphorus_villages)} villages")
    
    return map_filename

if __name__ == "__main__":
    create_phosphorus_zone_map()
