"""
Quick test of Crop Health API
"""

import requests
import json

# Test the API
BASE_URL = "http://127.0.0.1:8001"

print("🌱 Quick Test of Crop Health API")
print("=" * 40)

# Test 1: Check if server is running
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("✅ Server is running")
        print(f"   Version: {data.get('version', 'N/A')}")
        print(f"   Endpoints: {len(data.get('endpoints', []))} available")
        
        # Check if crop health endpoints are listed
        endpoints = data.get('endpoints', [])
        crop_health_endpoints = [ep for ep in endpoints if 'crop-health' in ep]
        print(f"   Crop Health Endpoints: {len(crop_health_endpoints)}")
        for ep in crop_health_endpoints:
            print(f"     - {ep}")
    else:
        print(f"❌ Server returned status {response.status_code}")
except Exception as e:
    print(f"❌ Server not responding: {str(e)}")
    exit(1)

# Test 2: Test crop health endpoint
print(f"\n🌱 Testing Crop Health Endpoint")
try:
    test_data = {
        "fieldId": "test-quick-123",
        "coordinates": [28.6139, 77.209],
        "cropType": "wheat"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/crop-health",
        json=test_data,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Crop Health API - SUCCESS")
        print(f"   Field ID: {data.get('fieldId', 'N/A')}")
        print(f"   Health Score: {data.get('cropHealth', {}).get('overallHealthScore', 'N/A')}")
        print(f"   Stress Level: {data.get('cropHealth', {}).get('stressLevel', 'N/A')}")
        print(f"   Growth Stage: {data.get('cropHealth', {}).get('growthStage', 'N/A')}")
        print(f"   Data Source: {data.get('dataSource', 'N/A')}")
        print(f"   Confidence: {data.get('confidence', 'N/A')}")
        print(f"   Recommendations: {len(data.get('recommendations', []))} items")
    else:
        print(f"❌ Crop Health API - FAILED")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Crop Health API - ERROR: {str(e)}")

print(f"\n🌱 Quick Test Complete!")
