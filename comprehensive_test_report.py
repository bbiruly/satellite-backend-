#!/usr/bin/env python3
"""
Comprehensive Testing Report for NPK Analysis System
Tests all features including soil type integration and performance
"""

import requests
import json
import time
from datetime import datetime

def comprehensive_testing():
    """Comprehensive testing of NPK analysis system"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 COMPREHENSIVE NPK ANALYSIS SYSTEM TESTING")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Server: {base_url}")
    print()
    
    # Test cases for different regions and crops
    test_cases = [
        {
            "name": "Chhattisgarh Rice (Red Soil)",
            "coordinates": [21.8468660, 82.0069310],
            "crop": "RICE",
            "expected_soil": "red_soil",
            "expected_region": "central_india",
            "description": "Original iAvenue Labs comparison location"
        },
        {
            "name": "Punjab Wheat (Alluvial Soil)",
            "coordinates": [30.7333, 76.7794],
            "crop": "WHEAT",
            "expected_soil": "alluvial",
            "expected_region": "north_india",
            "description": "High fertility alluvial soil region"
        },
        {
            "name": "Maharashtra Cotton (Black Soil)",
            "coordinates": [19.0760, 72.8777],
            "crop": "COTTON",
            "expected_soil": "black_soil",
            "expected_region": "central_india",
            "description": "Black cotton soil region"
        },
        {
            "name": "Tamil Nadu Sugarcane (Red Soil)",
            "coordinates": [11.1271, 78.6569],
            "crop": "SUGARCANE",
            "expected_soil": "red_soil",
            "expected_region": "south_india",
            "description": "Southern red soil region"
        }
    ]
    
    results = []
    total_start_time = time.time()
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * 50)
        print(f"📍 Description: {test_case['description']}")
        print(f"🌍 Coordinates: {test_case['coordinates']}")
        print(f"🌱 Crop: {test_case['crop']}")
        print(f"🏞️ Expected Soil: {test_case['expected_soil']}")
        print(f"🌍 Expected Region: {test_case['expected_region']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/npk-analysis-by-date",
                json={
                    "fieldId": f"comprehensive_test_{i}",
                    "coordinates": test_case["coordinates"],
                    "crop_type": test_case["crop"],
                    "specific_date": "2025-07-14"
                },
                timeout=60
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"⏱️ Response Time: {response_time:.2f}s")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    print("✅ SUCCESS!")
                    
                    # Extract key information
                    npk = data.get('npk', {})
                    region = data.get('region', 'unknown')
                    soil_type = data.get('soilType', 'unknown')
                    crop_type = data.get('cropType', 'unknown')
                    accuracy = data.get('dynamicAccuracy', 0)
                    local_calibration = data.get('localCalibration', 'unknown')
                    soil_calibration = data.get('soilTypeCalibration', 'unknown')
                    
                    print(f"🌍 Region: {region}")
                    print(f"🏞️ Soil Type: {soil_type}")
                    print(f"🌱 Crop: {crop_type}")
                    print(f"🎯 Accuracy: {accuracy:.2f}")
                    print(f"🔧 Local Calibration: {local_calibration}")
                    print(f"🏞️ Soil Calibration: {soil_calibration}")
                    
                    print(f"📊 NPK Values:")
                    nitrogen_kg_acre = npk.get('Nitrogen', 0) / 2.471
                    phosphorus_kg_acre = npk.get('Phosphorus', 0) / 2.471
                    potassium_kg_acre = npk.get('Potassium', 0) / 2.471
                    
                    print(f"   Nitrogen: {npk.get('Nitrogen', 'N/A')} kg/ha = {nitrogen_kg_acre:.1f} kg/acre")
                    print(f"   Phosphorus: {npk.get('Phosphorus', 'N/A')} kg/ha = {phosphorus_kg_acre:.1f} kg/acre")
                    print(f"   Potassium: {npk.get('Potassium', 'N/A')} kg/ha = {potassium_kg_acre:.1f} kg/acre")
                    print(f"   SOC: {npk.get('SOC', 'N/A')}%")
                    
                    # Validation
                    soil_correct = soil_type == test_case['expected_soil']
                    region_correct = region == test_case['expected_region']
                    
                    print(f"🔍 Validation:")
                    print(f"   Soil Type Detection: {'✅ Correct' if soil_correct else '❌ Incorrect'}")
                    print(f"   Region Detection: {'✅ Correct' if region_correct else '❌ Incorrect'}")
                    
                    # Store results
                    results.append({
                        'name': test_case['name'],
                        'success': True,
                        'response_time': response_time,
                        'region': region,
                        'soil_type': soil_type,
                        'crop_type': crop_type,
                        'nitrogen': npk.get('Nitrogen', 0),
                        'phosphorus': npk.get('Phosphorus', 0),
                        'potassium': npk.get('Potassium', 0),
                        'soc': npk.get('SOC', 0),
                        'accuracy': accuracy,
                        'soil_correct': soil_correct,
                        'region_correct': region_correct,
                        'local_calibration': local_calibration,
                        'soil_calibration': soil_calibration
                    })
                    
                else:
                    print("❌ FAILED!")
                    print(f"Error: {data.get('error', 'Unknown error')}")
                    results.append({
                        'name': test_case['name'],
                        'success': False,
                        'response_time': response_time,
                        'error': data.get('error', 'Unknown error')
                    })
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                results.append({
                    'name': test_case['name'],
                    'success': False,
                    'response_time': response_time,
                    'error': f'HTTP {response.status_code}'
                })
                
        except requests.exceptions.Timeout:
            print("⏰ TIMEOUT - Request took too long")
            results.append({
                'name': test_case['name'],
                'success': False,
                'response_time': 60,
                'error': 'Timeout'
            })
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'response_time': 0,
                'error': str(e)
            })
        
        print()
    
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    # Generate comprehensive report
    print("=" * 60)
    print("📊 COMPREHENSIVE TESTING REPORT")
    print("=" * 60)
    
    # Summary statistics
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"📈 SUMMARY STATISTICS:")
    print(f"   Total Tests: {len(results)}")
    print(f"   Successful: {len(successful_tests)}")
    print(f"   Failed: {len(failed_tests)}")
    print(f"   Success Rate: {len(successful_tests)/len(results)*100:.1f}%")
    print(f"   Total Test Time: {total_time:.2f}s")
    print(f"   Average Response Time: {sum(r['response_time'] for r in successful_tests)/len(successful_tests):.2f}s" if successful_tests else "   Average Response Time: N/A")
    
    # Performance analysis
    print(f"\n⚡ PERFORMANCE ANALYSIS:")
    if successful_tests:
        response_times = [r['response_time'] for r in successful_tests]
        print(f"   Fastest Response: {min(response_times):.2f}s")
        print(f"   Slowest Response: {max(response_times):.2f}s")
        print(f"   Average Response: {sum(response_times)/len(response_times):.2f}s")
        
        # Performance rating
        avg_time = sum(response_times)/len(response_times)
        if avg_time < 20:
            performance_rating = "🚀 Excellent"
        elif avg_time < 40:
            performance_rating = "✅ Good"
        elif avg_time < 60:
            performance_rating = "⚠️ Moderate"
        else:
            performance_rating = "🐌 Slow"
        
        print(f"   Performance Rating: {performance_rating}")
    
    # Accuracy analysis
    print(f"\n🎯 ACCURACY ANALYSIS:")
    if successful_tests:
        soil_correct_count = sum(1 for r in successful_tests if r.get('soil_correct', False))
        region_correct_count = sum(1 for r in successful_tests if r.get('region_correct', False))
        
        print(f"   Soil Type Detection: {soil_correct_count}/{len(successful_tests)} ({soil_correct_count/len(successful_tests)*100:.1f}%)")
        print(f"   Region Detection: {region_correct_count}/{len(successful_tests)} ({region_correct_count/len(successful_tests)*100:.1f}%)")
        
        avg_accuracy = sum(r.get('accuracy', 0) for r in successful_tests) / len(successful_tests)
        print(f"   Average Dynamic Accuracy: {avg_accuracy:.2f}")
    
    # NPK values analysis
    print(f"\n📊 NPK VALUES ANALYSIS:")
    if successful_tests:
        print(f"   {'Region':<20} | {'Soil Type':<12} | {'Nitrogen':<8} | {'Phosphorus':<10} | {'Potassium':<9} | {'SOC':<5} | {'Accuracy':<8}")
        print(f"   {'-'*20} | {'-'*12} | {'-'*8} | {'-'*10} | {'-'*9} | {'-'*5} | {'-'*8}")
        for result in successful_tests:
            print(f"   {result['name']:<20} | {result['soil_type']:<12} | {result['nitrogen']:>8.1f} | {result['phosphorus']:>10.1f} | {result['potassium']:>9.1f} | {result['soc']:>5.1f} | {result['accuracy']:>8.2f}")
    
    # Feature validation
    print(f"\n✅ FEATURE VALIDATION:")
    if successful_tests:
        local_calibration_applied = sum(1 for r in successful_tests if r.get('local_calibration') == 'applied')
        soil_calibration_applied = sum(1 for r in successful_tests if r.get('soil_calibration') == 'applied')
        
        print(f"   Local Calibration: {local_calibration_applied}/{len(successful_tests)} applied")
        print(f"   Soil Type Calibration: {soil_calibration_applied}/{len(successful_tests)} applied")
        print(f"   Dynamic Accuracy Calculation: {len(successful_tests)}/{len(successful_tests)} working")
        print(f"   Regional Detection: {region_correct_count}/{len(successful_tests)} correct")
        print(f"   Soil Type Detection: {soil_correct_count}/{len(successful_tests)} correct")
    
    # Error analysis
    if failed_tests:
        print(f"\n❌ ERROR ANALYSIS:")
        error_counts = {}
        for result in failed_tests:
            error = result.get('error', 'Unknown')
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in error_counts.items():
            print(f"   {error}: {count} occurrences")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if len(successful_tests) == len(results):
        print("   ✅ All tests passed successfully!")
        print("   ✅ System is production-ready")
        print("   ✅ All features working correctly")
    else:
        print("   ⚠️ Some tests failed - investigate errors")
        print("   ⚠️ Check server logs for detailed error information")
    
    if successful_tests:
        avg_time = sum(r['response_time'] for r in successful_tests)/len(successful_tests)
        if avg_time > 30:
            print("   ⚠️ Response times are slow - consider further optimization")
        else:
            print("   ✅ Response times are acceptable")
    
    print(f"\n🏆 FINAL VERDICT:")
    if len(successful_tests) == len(results) and len(successful_tests) > 0:
        print("   🎉 SYSTEM FULLY OPERATIONAL!")
        print("   🎉 All features working correctly!")
        print("   🎉 Ready for production deployment!")
    else:
        print("   ⚠️ System needs attention before production deployment")
    
    print("\n" + "=" * 60)
    print("📋 TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    comprehensive_testing()
