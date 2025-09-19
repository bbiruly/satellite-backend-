"""
Weather API Setup Script
Helps you configure the WeatherAPI.com API key
"""

import os

def setup_weather_api():
    """Setup WeatherAPI.com API key"""
    print("🌤️ WeatherAPI.com Setup")
    print("=" * 50)
    
    print("\n📋 Steps to get your API key:")
    print("1. Go to: https://www.weatherapi.com/signup.aspx")
    print("2. Sign up for a free account")
    print("3. Get your API key from the dashboard")
    print("4. Free tier: 1 million calls/month")
    
    print("\n🔑 Enter your WeatherAPI.com API key:")
    api_key = input("API Key: ").strip()
    
    if not api_key or api_key == "YOUR_WEATHERAPI_KEY_HERE":
        print("❌ Please enter a valid API key")
        return False
    
    # Update the config file
    config_content = f'''"""
Weather API Configuration
Set your WeatherAPI.com API key here
"""

# WeatherAPI.com Configuration
WEATHER_API_KEY = "{api_key}"

# Instructions:
# 1. Go to https://www.weatherapi.com/signup.aspx
# 2. Sign up for a free account
# 3. Get your API key from the dashboard
# 4. Replace "YOUR_WEATHERAPI_KEY_HERE" with your actual API key
# 5. Save this file

# Example:
# WEATHER_API_KEY = "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"

# Free tier includes:
# - 1 million API calls per month
# - Current weather data
# - 7-day forecast
# - Historical weather data
# - Weather alerts
# - Air quality data
'''
    
    try:
        with open("weather_config.py", "w") as f:
            f.write(config_content)
        
        print(f"\n✅ API key saved to weather_config.py")
        print(f"🔑 Key: {api_key[:8]}...{api_key[-4:]}")
        
        # Test the API key
        print("\n🧪 Testing API key...")
        test_api_key(api_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving API key: {str(e)}")
        return False

def test_api_key(api_key):
    """Test the API key with a simple request"""
    import requests
    
    try:
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": "London",  # Test with London
            "aqi": "no"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            location = data.get("location", {}).get("name", "Unknown")
            temp = data.get("current", {}).get("temp_c", "N/A")
            print(f"✅ API key working! Test location: {location}, Temp: {temp}°C")
        else:
            print(f"❌ API key test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API key test error: {str(e)}")

if __name__ == "__main__":
    print("🚀 ZumAgro Weather API Setup")
    print("This script will help you configure your WeatherAPI.com API key")
    
    if setup_weather_api():
        print("\n🎉 Setup complete!")
        print("You can now run: python main.py")
        print("And test with: python test_weather_api.py")
    else:
        print("\n❌ Setup failed. Please try again.")
