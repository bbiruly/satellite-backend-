#!/usr/bin/env python3
"""
Debug Delhi coordinates (known working)
"""

import asyncio
from api.planetary_computer_retry import retry_manager

async def debug_delhi():
    """Debug Delhi coordinates (known working)"""
    print("🔍 DEBUGGING DELHI COORDINATES")
    print("=" * 50)
    
    # Delhi coordinates (known working)
    coordinates = [28.61, 77.2]
    
    # Create bounding box
    bbox = {
        'minLat': coordinates[0] - 0.005,
        'maxLat': coordinates[0] + 0.005,
        'minLon': coordinates[1] - 0.005,
        'maxLon': coordinates[1] + 0.005
    }
    
    print(f"📍 Coordinates: {coordinates}")
    print(f"📦 Bounding Box: {bbox}")
    
    # Test the retry system
    result = await retry_manager.get_satellite_data_with_retry(
        coordinates=coordinates,
        bbox=bbox,
        field_id="debug-delhi"
    )
    
    print(f"\n📊 Result:")
    print(f"Success: {result.get('success', False)}")
    if result.get('success'):
        print(f"Dataset Used: {result.get('dataset_used', 'unknown')}")
        print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
    else:
        print(f"Error: {result.get('error', 'unknown')}")
        print(f"Datasets Tried: {result.get('datasets_tried', [])}")

if __name__ == "__main__":
    asyncio.run(debug_delhi())
