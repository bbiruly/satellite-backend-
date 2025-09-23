#!/usr/bin/env python3
"""
Debug script to identify the satellite data processing error
"""

import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_satellite_processing():
    """Debug the satellite data processing error"""
    try:
        print("🔍 Debugging satellite data processing...")
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        # Test with Delhi coordinates
        bbox = {
            'minLat': 28.6039,
            'maxLat': 28.6239,
            'minLon': 77.199,
            'maxLon': 77.219
        }
        
        print(f"Testing with bbox: {bbox}")
        
        # Call the function and catch any errors
        result = compute_indices_and_npk_for_bbox(bbox)
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        if isinstance(result, dict):
            print("✅ Result is a dictionary")
            if result.get('success'):
                print("✅ Success: True")
                print(f"Keys: {list(result.keys())}")
            else:
                print(f"❌ Success: False, Error: {result.get('error')}")
        else:
            print(f"❌ Result is not a dictionary: {type(result)}")
            print(f"Result content: {result}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()

def debug_imports():
    """Debug imports to make sure everything is available"""
    try:
        print("🔍 Testing imports...")
        
        import numpy as np
        print("✅ numpy imported")
        
        import pystac_client
        print("✅ pystac_client imported")
        
        import planetary_computer as pc
        print("✅ planetary_computer imported")
        
        import rioxarray
        print("✅ rioxarray imported")
        
        import xarray as xr
        print("✅ xarray imported")
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        print("✅ sentinel_indices imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def debug_simple_call():
    """Make a simple call to see what happens"""
    try:
        print("\n🔍 Making simple satellite data call...")
        
        from api.working.sentinel_indices import compute_indices_and_npk_for_bbox
        
        # Very simple bbox
        bbox = {
            'minLat': 28.6,
            'maxLat': 28.7,
            'minLon': 77.1,
            'maxLon': 77.2
        }
        
        print(f"Calling with bbox: {bbox}")
        
        # This should return a dictionary
        result = compute_indices_and_npk_for_bbox(bbox)
        
        print(f"Result type: {type(result)}")
        
        if isinstance(result, str):
            print(f"❌ ERROR: Function returned string instead of dict!")
            print(f"String content: {result}")
            return False
        elif isinstance(result, dict):
            print(f"✅ Function returned dictionary")
            print(f"Keys: {list(result.keys())}")
            return True
        else:
            print(f"❌ Function returned unexpected type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Exception in simple call: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Satellite Data Processing Debug")
    print("=" * 50)
    
    # Test 1: Imports
    imports_ok = debug_imports()
    
    if imports_ok:
        # Test 2: Simple call
        simple_ok = debug_simple_call()
        
        # Test 3: Full debug
        debug_satellite_processing()
        
        print("\n" + "=" * 50)
        print("📊 Debug Results:")
        print(f"Imports: {'✅ OK' if imports_ok else '❌ FAIL'}")
        print(f"Simple call: {'✅ OK' if simple_ok else '❌ FAIL'}")
    else:
        print("\n❌ Import tests failed")
