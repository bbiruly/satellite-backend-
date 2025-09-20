#!/usr/bin/env python3
"""
Debug Data Flow Issue
Test what the enhanced system is actually returning
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.enhanced_planetary_computer import enhanced_pc_manager

async def debug_data_flow():
    """Debug what the enhanced system returns"""
    print("🔍 DEBUGGING DATA FLOW ISSUE")
    print("=" * 60)
    
    # Test coordinates that should work
    coordinates = [30.9, 75.8]  # Punjab
    bbox = {
        'minLat': coordinates[0] - 0.005,
        'maxLat': coordinates[0] + 0.005,
        'minLon': coordinates[1] - 0.005,
        'maxLon': coordinates[1] + 0.005
    }
    
    print(f"📍 Testing coordinates: {coordinates}")
    print(f"📦 Bbox: {bbox}")
    print()
    
    try:
        # Call enhanced system directly
        result = await enhanced_pc_manager.get_satellite_data_with_enhanced_retry(
            coordinates=coordinates,
            bbox=bbox,
            field_id="debug-test",
            cloud_coverage=None,
            monsoon_phase=None
        )
        
        print("📊 ENHANCED SYSTEM RESULT:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Dataset: {result.get('dataset', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Error: {result.get('error', 'none')}")
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"\n📋 DATA STRUCTURE:")
            print(f"   Data keys: {list(data.keys()) if data else 'None'}")
            
            if 'indices' in data:
                indices = data['indices']
                print(f"   Indices: {indices}")
            
            if 'npk' in data:
                npk = data['npk']
                print(f"   NPK: {npk}")
            
            # Check if data is empty
            if not data:
                print("   ❌ DATA IS EMPTY!")
            else:
                print("   ✅ DATA IS PRESENT")
        
        print(f"\n🔍 FULL RESULT STRUCTURE:")
        print(f"   Result keys: {list(result.keys())}")
        print(f"   Result type: {type(result)}")
        
        # Test the data extraction logic
        print(f"\n🧪 TESTING DATA EXTRACTION:")
        if result and result.get('success'):
            satellite_data = result.get('data', {})
            print(f"   Extracted data: {satellite_data}")
            print(f"   Data is empty: {not satellite_data}")
            
            if satellite_data:
                print("   ✅ Data extraction successful")
            else:
                print("   ❌ Data extraction failed - data is empty")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_data_flow())
