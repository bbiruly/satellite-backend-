"""
Weather API Configuration
Set your WeatherAPI.com API key here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# WeatherAPI.com Configuration
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')

if not WEATHER_API_KEY or WEATHER_API_KEY == 'YOUR_WEATHERAPI_KEY_HERE':
    print("WARNING: WEATHER_API_KEY not set in environment variables")

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
