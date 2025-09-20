#!/usr/bin/env python3
"""
Debug Enhanced System Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_import():
    """Test if enhanced system can be imported"""
    try:
        from api.enhanced_planetary_computer import enhanced_pc_manager
        print("✅ Enhanced Planetary Computer Manager imported successfully")
        
        # Test basic functionality
        print(f"   Satellite configs: {len(enhanced_pc_manager.satellite_configs)}")
        print(f"   Cache config: {len(enhanced_pc_manager.cache_config)}")
        print(f"   Performance stats: {enhanced_pc_manager.get_performance_stats()}")
        
        return True
    except Exception as e:
        print(f"❌ Enhanced Planetary Computer Manager import failed: {str(e)}")
        return False

def test_optimized_field_metrics_import():
    """Test if optimized field metrics can import enhanced system"""
    try:
        from api.optimized_field_metrics import OptimizedFieldMetricsService
        print("✅ Optimized Field Metrics Service imported successfully")
        
        # Check if it has the enhanced manager
        service = OptimizedFieldMetricsService()
        print(f"   Service created: {service is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Optimized Field Metrics Service import failed: {str(e)}")
        return False

def test_main_import():
    """Test if main.py can import enhanced system"""
    try:
        # This will test if main.py can start without errors
        import main
        print("✅ Main.py imported successfully")
        return True
    except Exception as e:
        print(f"❌ Main.py import failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 DEBUGGING ENHANCED SYSTEM INTEGRATION")
    print("=" * 60)
    
    # Test imports
    enhanced_ok = test_enhanced_import()
    optimized_ok = test_optimized_field_metrics_import()
    main_ok = test_main_import()
    
    print(f"\n📊 Import Test Results:")
    print(f"   Enhanced System: {'✅' if enhanced_ok else '❌'}")
    print(f"   Optimized Service: {'✅' if optimized_ok else '❌'}")
    print(f"   Main Application: {'✅' if main_ok else '❌'}")
    
    if enhanced_ok and optimized_ok and main_ok:
        print("\n🎉 All imports successful - Enhanced system should be working!")
    else:
        print("\n⚠️ Some imports failed - Check the errors above")
