#!/usr/bin/env python3
"""
Create interactive map showing both Yellow and Red zone villages
Using coordinate-based zone assignment from JSON data
"""

import json
import folium
from folium import plugins

def create_dual_zone_map():
    """Create interactive map with both Yellow and Red zone villages"""
    
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
    
    # Add zone polygons
    # Yellow Zone
    folium.Polygon(
        [[20.1, 80.9], [20.58, 80.9], [20.58, 81.4], [20.1, 81.4]],
        color='yellow',
        weight=3,
        fill=True,
        fillColor='yellow',
        fillOpacity=0.2,
        popup='Yellow Zone (Low-Medium Nitrogen)'
    ).add_to(m)
    
    # Red Zone
    folium.Polygon(
        [[20.05, 81.25], [20.8, 81.25], [20.8, 82.0], [20.05, 82.0]],
        color='red',
        weight=3,
        fill=True,
        fillColor='red',
        fillOpacity=0.2,
        popup='Red Zone (High/Very High Nitrogen)'
    ).add_to(m)
    
    # Process villages based on zone field in JSON
    yellow_villages = []
    red_villages = []
    
    for village in data['village_wise_data']['villages']:
        if 'coordinates' in village and len(village['coordinates']) == 2:
            lat, lon = village['coordinates']
            zone = village.get('zone', 'unknown')
            
            if zone == 'yellow':
                yellow_villages.append(village)
            elif zone == 'red':
                red_villages.append(village)
    
    print(f"Found {len(yellow_villages)} yellow zone villages")
    print(f"Found {len(red_villages)} red zone villages")
    
    # Add Yellow Zone villages
    for village in yellow_villages:
        lat, lon = village['coordinates']
        
        # Determine marker color based on nitrogen level
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
        
        # Create popup content
        popup_content = f"""
        <div style="width: 200px;">
            <h4 style="color: #2E8B57; margin: 5px 0;">{village['village_name']}</h4>
            <p><b>Population:</b> {village['population']:,}</p>
            <p><b>Nitrogen Level:</b> {nitrogen_level}</p>
            <p><b>Estimated Nitrogen:</b> {village.get('estimated_nitrogen', 'N/A')}</p>
            <p><b>Zone:</b> <span style="color: #FFD700; font-weight: bold;">YELLOW ZONE</span></p>
            <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color=marker_color, icon='info-sign', prefix='glyphicon'),
            tooltip=f"Yellow Zone: {village['village_name']}"
        ).add_to(m)
    
    # Add Red Zone villages
    for village in red_villages:
        lat, lon = village['coordinates']
        
        # Determine marker color based on nitrogen level
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
        
        # Create popup content
        popup_content = f"""
        <div style="width: 200px;">
            <h4 style="color: #DC143C; margin: 5px 0;">{village['village_name']}</h4>
            <p><b>Population:</b> {village['population']:,}</p>
            <p><b>Nitrogen Level:</b> {nitrogen_level}</p>
            <p><b>Estimated Nitrogen:</b> {village.get('estimated_nitrogen', 'N/A')}</p>
            <p><b>Zone:</b> <span style="color: #DC143C; font-weight: bold;">RED ZONE</span></p>
            <p><b>Coordinates:</b> {lat:.4f}°N, {lon:.4f}°E</p>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(color=marker_color, icon='info-sign', prefix='glyphicon'),
            tooltip=f"Red Zone: {village['village_name']}"
        ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 320px; height: 220px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; color: #333; text-align: center;">Kanker District Zones</h4>
        
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <i class="fa fa-square fa-2x" style="color: #FFD700; margin-right: 10px;"></i> 
            <span><b>Yellow Zone</b> (Low-Medium Nitrogen)</span>
        </div>
        
        <div style="margin: 8px 0; display: flex; align-items: center;">
            <i class="fa fa-square fa-2x" style="color: #DC143C; margin-right: 10px;"></i> 
            <span><b>Red Zone</b> (High/Very High Nitrogen)</span>
        </div>
        
        <hr style="margin: 10px 0;">
        
        <h5 style="margin: 8px 0; color: #333;">Nitrogen Level Markers:</h5>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span><i class="fa fa-circle" style="color: lightblue;"></i> Low</span>
            <span><i class="fa fa-circle" style="color: blue;"></i> Low-Medium</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span><i class="fa fa-circle" style="color: orange;"></i> Medium</span>
            <span><i class="fa fa-circle" style="color: red;"></i> High</span>
        </div>
        <div style="margin: 5px 0;">
            <i class="fa fa-circle" style="color: darkred;"></i> Very High
        </div>
        
        <div style="margin: 10px 0 0 0; padding: 8px; background-color: #f0f0f0; border-radius: 3px;">
            <p style="margin: 0; font-size: 12px; color: #666; text-align: center;">
                <b>Total Villages:</b> {len(yellow_villages)} Yellow + {len(red_villages)} Red = {len(yellow_villages) + len(red_villages)}
            </p>
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    map_filename = "kanker_dual_zone_villages.html"
    m.save(map_filename)
    
    print(f"✅ Dual Zone Map Created: {map_filename}")
    print(f"   - Yellow Zone: {len(yellow_villages)} villages")
    print(f"   - Red Zone: {len(red_villages)} villages")
    print(f"   - Total: {len(yellow_villages) + len(red_villages)} villages")
    
    return map_filename

if __name__ == "__main__":
    create_dual_zone_map()
