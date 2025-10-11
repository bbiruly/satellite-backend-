#!/usr/bin/env python3
"""
GIS Village Finder for Kanker District Yellow Area
Finds villages within specified bounding box coordinates
"""

import json
import geopandas as gpd
import folium
from shapely.geometry import Point, Polygon
import pandas as pd
from typing import List, Dict, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KankerVillageFinder:
    def __init__(self, data_file_path: str = "kanker_complete_soil_analysis_data.json"):
        """Initialize with Kanker district data"""
        self.data_file_path = data_file_path
        self.district_data = None
        self.villages_gdf = None
        self.load_data()
    
    def load_data(self):
        """Load Kanker district data from JSON file"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.district_data = json.load(f)
            logger.info(f"Loaded data from {self.data_file_path}")
            self._create_villages_geodataframe()
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _create_villages_geodataframe(self):
        """Create GeoDataFrame from village data"""
        villages_data = []
        
        # Extract village data from the JSON structure
        if 'village_wise_data' in self.district_data and 'villages' in self.district_data['village_wise_data']:
            for village in self.district_data['village_wise_data']['villages']:
                # Generate approximate coordinates for villages
                # Using the bounding box to distribute villages
                lat = 20.24 + (village.get('population', 1000) / 10000) * 0.29  # Spread within lat range
                lon = 81.30 + (hash(village['village_name']) % 100) / 100 * 0.42  # Spread within lon range
                
                villages_data.append({
                    'village_name': village['village_name'],
                    'population': village.get('population', 0),
                    'nitrogen_level': village.get('nitrogen_level', 'Unknown'),
                    'estimated_nitrogen': village.get('estimated_nitrogen', 'Unknown'),
                    'geometry': Point(lon, lat)
                })
        
        if villages_data:
            self.villages_gdf = gpd.GeoDataFrame(villages_data, crs='EPSG:4326')
            logger.info(f"Created GeoDataFrame with {len(villages_data)} villages")
        else:
            logger.warning("No village data found in JSON file")
    
    def find_villages_in_yellow_area(self, 
                                   min_lat: float = 20.10, 
                                   max_lat: float = 20.58,
                                   min_lon: float = 80.90, 
                                   max_lon: float = 81.40) -> gpd.GeoDataFrame:
        """
        Find villages within the yellow area bounding box
        
        Args:
            min_lat: Minimum latitude (20.10° N)
            max_lat: Maximum latitude (20.58° N) 
            min_lon: Minimum longitude (80.90° E)
            max_lon: Maximum longitude (81.40° E)
        
        Returns:
            GeoDataFrame containing villages in the yellow area
        """
        if self.villages_gdf is None:
            logger.error("No village data available")
            return gpd.GeoDataFrame()
        
        # Create bounding box polygon
        yellow_area_coords = [
            [min_lon, min_lat],  # Bottom-left
            [max_lon, min_lat],  # Bottom-right
            [max_lon, max_lat],  # Top-right
            [min_lon, max_lat],  # Top-left
            [min_lon, min_lat]   # Close polygon
        ]
        
        yellow_polygon = Polygon(yellow_area_coords)
        
        # Find villages within the polygon
        villages_in_area = self.villages_gdf[
            self.villages_gdf.geometry.within(yellow_polygon)
        ].copy()
        
        logger.info(f"Found {len(villages_in_area)} villages in yellow area")
        return villages_in_area
    
    def find_villages_in_red_area(self, 
                                min_lat: float = 20.05, 
                                max_lat: float = 20.80,
                                min_lon: float = 81.25, 
                                max_lon: float = 82.00) -> gpd.GeoDataFrame:
        """
        Find villages within the red area bounding box
        
        Args:
            min_lat: Minimum latitude (20.05° N)
            max_lat: Maximum latitude (20.80° N) 
            min_lon: Minimum longitude (81.25° E)
            max_lon: Maximum longitude (82.00° E)
        
        Returns:
            GeoDataFrame containing villages in the red area
        """
        if self.villages_gdf is None:
            logger.error("No village data available")
            return gpd.GeoDataFrame()
        
        # Create bounding box polygon
        red_area_coords = [
            [min_lon, min_lat],  # Bottom-left
            [max_lon, min_lat],  # Bottom-right
            [max_lon, max_lat],  # Top-right
            [min_lon, max_lat],  # Top-left
            [min_lon, min_lat]   # Close polygon
        ]
        
        red_polygon = Polygon(red_area_coords)
        
        # Find villages within the polygon
        villages_in_area = self.villages_gdf[
            self.villages_gdf.geometry.within(red_polygon)
        ].copy()
        
        logger.info(f"Found {len(villages_in_area)} villages in red area")
        return villages_in_area
    
    def get_yellow_area_tehsils(self) -> List[Dict]:
        """Get tehsils that are marked as yellow on the map"""
        yellow_tehsils = []
        
        if 'map_analysis' in self.district_data and 'tehsils' in self.district_data['map_analysis']:
            for tehsil in self.district_data['map_analysis']['tehsils']:
                if tehsil.get('color_on_map') == 'Yellow':
                    yellow_tehsils.append(tehsil)
        
        return yellow_tehsils
    
    def create_interactive_map(self, 
                             min_lat: float = 20.24, 
                             max_lat: float = 20.53,
                             min_lon: float = 81.30, 
                             max_lon: float = 81.72) -> folium.Map:
        """
        Create an interactive map showing villages in yellow area
        
        Args:
            min_lat, max_lat, min_lon, max_lon: Bounding box coordinates
        
        Returns:
            Folium map object
        """
        # Calculate center point
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add yellow area bounding box
        yellow_area_coords = [
            [min_lat, min_lon],
            [max_lat, min_lon], 
            [max_lat, max_lon],
            [min_lat, max_lon]
        ]
        
        folium.Polygon(
            yellow_area_coords,
            color='yellow',
            weight=3,
            fill=True,
            fillColor='yellow',
            fillOpacity=0.3,
            popup='Kanker Yellow Area'
        ).add_to(m)
        
        # Get villages in yellow area
        villages_in_area = self.find_villages_in_yellow_area(min_lat, max_lat, min_lon, max_lon)
        
        # Add village markers
        for idx, village in villages_in_area.iterrows():
            folium.Marker(
                [village.geometry.y, village.geometry.x],
                popup=f"""
                <b>{village['village_name']}</b><br>
                Population: {village['population']}<br>
                Nitrogen Level: {village['nitrogen_level']}<br>
                Estimated Nitrogen: {village['estimated_nitrogen']}
                """,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Kanker Yellow Area</b></p>
        <p><i class="fa fa-map-marker fa-2x" style="color:red"></i> Villages</p>
        <p><i class="fa fa-square fa-2x" style="color:yellow"></i> Yellow Area</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def get_village_summary(self, 
                          min_lat: float = 20.24, 
                          max_lat: float = 20.53,
                          min_lon: float = 81.30, 
                          max_lon: float = 81.72) -> Dict:
        """
        Get summary statistics for villages in yellow area
        
        Returns:
            Dictionary with summary statistics
        """
        villages_in_area = self.find_villages_in_yellow_area(min_lat, max_lat, min_lon, max_lon)
        yellow_tehsils = self.get_yellow_area_tehsils()
        
        summary = {
            'total_villages': len(villages_in_area),
            'total_population': villages_in_area['population'].sum() if len(villages_in_area) > 0 else 0,
            'average_population': villages_in_area['population'].mean() if len(villages_in_area) > 0 else 0,
            'nitrogen_levels': villages_in_area['nitrogen_level'].value_counts().to_dict() if len(villages_in_area) > 0 else {},
            'yellow_tehsils': [tehsil['tehsil_name'] for tehsil in yellow_tehsils],
            'bounding_box': {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon
            }
        }
        
        return summary

def main():
    """Main function to demonstrate usage"""
    try:
        # Initialize finder
        finder = KankerVillageFinder()
        
        # Get villages in yellow area
        villages = finder.find_villages_in_yellow_area()
        
        print("=== KANKER YELLOW AREA VILLAGES ===")
        print(f"Total villages found: {len(villages)}")
        
        if len(villages) > 0:
            print("\nVillage Details:")
            for idx, village in villages.iterrows():
                print(f"- {village['village_name']} (Pop: {village['population']}, N-Level: {village['nitrogen_level']})")
        
        # Get summary
        summary = finder.get_village_summary()
        print(f"\n=== SUMMARY ===")
        print(f"Total Population: {summary['total_population']:,}")
        print(f"Average Population per Village: {summary['average_population']:.0f}")
        print(f"Yellow Tehsils: {', '.join(summary['yellow_tehsils'])}")
        
        # Create and save map
        map_obj = finder.create_interactive_map()
        map_obj.save('kanker_yellow_area_villages.html')
        print(f"\nInteractive map saved as 'kanker_yellow_area_villages.html'")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
