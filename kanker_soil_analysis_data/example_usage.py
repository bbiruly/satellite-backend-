#!/usr/bin/env python3
"""
Example usage of GIS Village Finder
"""

from gis_village_finder import KankerVillageFinder
import json

def main():
    print("🗺️  Kanker District Yellow Area Village Finder")
    print("=" * 60)
    
    # Initialize the finder
    finder = KankerVillageFinder()
    
    # Define the yellow area coordinates (from your map)
    YELLOW_AREA = {
        "min_lat": 20.10,
        "max_lat": 20.58,
        "min_lon": 80.90,
        "max_lon": 81.40
    }
    
    # Define the red area coordinates (from your map)
    RED_AREA = {
        "min_lat": 20.05,
        "max_lat": 20.80,
        "min_lon": 81.25,
        "max_lon": 82.00
    }
    
    print(f"📍 Yellow Area Bounding Box (Low-Medium Nitrogen):")
    print(f"   Latitude: {YELLOW_AREA['min_lat']}° N to {YELLOW_AREA['max_lat']}° N")
    print(f"   Longitude: {YELLOW_AREA['min_lon']}° E to {YELLOW_AREA['max_lon']}° E")
    print()
    
    print(f"📍 Red Area Bounding Box (High/Very High Nitrogen):")
    print(f"   Latitude: {RED_AREA['min_lat']}° N to {RED_AREA['max_lat']}° N")
    print(f"   Longitude: {RED_AREA['min_lon']}° E to {RED_AREA['max_lon']}° E")
    print()
    
    # 1. Get villages in yellow area
    print("🔍 Finding villages in yellow area...")
    villages = finder.find_villages_in_yellow_area(
        min_lat=YELLOW_AREA['min_lat'],
        max_lat=YELLOW_AREA['max_lat'],
        min_lon=YELLOW_AREA['min_lon'],
        max_lon=YELLOW_AREA['max_lon']
    )
    
    print(f"✅ Found {len(villages)} villages in yellow area")
    print()
    
    # 2. Display village details
    if len(villages) > 0:
        print("🏘️  Village Details:")
        print("-" * 60)
        for idx, village in villages.iterrows():
            print(f"{idx+1:2d}. {village['village_name']}")
            print(f"     Population: {village['population']:,}")
            print(f"     Nitrogen Level: {village['nitrogen_level']}")
            print(f"     Estimated Nitrogen: {village['estimated_nitrogen']}")
            print(f"     Coordinates: {village.geometry.y:.4f}°N, {village.geometry.x:.4f}°E")
            print()
    
    # 3. Get villages in red area
    print("🔍 Finding villages in red area...")
    red_villages = finder.find_villages_in_red_area(
        min_lat=RED_AREA['min_lat'],
        max_lat=RED_AREA['max_lat'],
        min_lon=RED_AREA['min_lon'],
        max_lon=RED_AREA['max_lon']
    )
    
    print(f"✅ Found {len(red_villages)} villages in red area")
    print()
    
    # Display red area village details
    if len(red_villages) > 0:
        print("🏘️  Red Area Village Details (High/Very High Nitrogen):")
        print("-" * 60)
        for idx, village in red_villages.iterrows():
            print(f"{idx+1:2d}. {village['village_name']}")
            print(f"     Population: {village['population']:,}")
            print(f"     Nitrogen Level: {village['nitrogen_level']}")
            print(f"     Estimated Nitrogen: {village['estimated_nitrogen']}")
            print(f"     Coordinates: {village.geometry.y:.4f}°N, {village.geometry.x:.4f}°E")
            print()
    
    # 4. Get summary statistics
    print("📊 Summary Statistics:")
    print("-" * 60)
    summary = finder.get_village_summary(
        min_lat=YELLOW_AREA['min_lat'],
        max_lat=YELLOW_AREA['max_lat'],
        min_lon=YELLOW_AREA['min_lon'],
        max_lon=YELLOW_AREA['max_lon']
    )
    
    print(f"Total Villages: {summary['total_villages']}")
    print(f"Total Population: {summary['total_population']:,}")
    print(f"Average Population: {summary['average_population']:.0f}")
    print(f"Yellow Tehsils: {', '.join(summary['yellow_tehsils'])}")
    print()
    
    # 4. Show nitrogen level distribution
    nitrogen_levels = summary.get('nitrogen_levels', {})
    if nitrogen_levels:
        print("🌱 Nitrogen Level Distribution:")
        print("-" * 60)
        for level, count in nitrogen_levels.items():
            print(f"{level:15s}: {count:3d} villages")
        print()
    
    # 5. Get yellow tehsils
    print("🏛️  Yellow Tehsils:")
    print("-" * 60)
    yellow_tehsils = finder.get_yellow_area_tehsils()
    for tehsil in yellow_tehsils:
        print(f"• {tehsil['tehsil_name']}")
        print(f"  Color: {tehsil['color_on_map']}")
        print(f"  Nitrogen Level: {tehsil['nitrogen_level']}")
        print(f"  Villages Count: {tehsil['villages_count']}")
        print()
    
    # 6. Create interactive map
    print("🗺️  Creating interactive map...")
    try:
        map_obj = finder.create_interactive_map(
            min_lat=YELLOW_AREA['min_lat'],
            max_lat=YELLOW_AREA['max_lat'],
            min_lon=YELLOW_AREA['min_lon'],
            max_lon=YELLOW_AREA['max_lon']
        )
        
        map_filename = "kanker_yellow_area_villages.html"
        map_obj.save(map_filename)
        print(f"✅ Interactive map saved as: {map_filename}")
        print(f"   Open this file in your web browser to view the map")
        
    except Exception as e:
        print(f"❌ Error creating map: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")

if __name__ == "__main__":
    main()
