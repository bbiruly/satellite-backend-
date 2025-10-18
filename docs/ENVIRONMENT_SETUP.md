# Environment Setup Guide

## 🚀 Quick Start

### 1. Set Up Environment Variables
```bash
# Run the environment setup script
python setup_env.py

# Or manually create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start the Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start server with environment loading
python start_server.py

# Or start manually
python main.py
```

## 📋 Required Environment Variables

### Essential Variables
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `WEATHER_API_KEY` | WeatherAPI.com API key | ✅ Yes | - |
| `HOST` | Server host | ❌ No | `127.0.0.1` |
| `PORT` | Server port | ❌ No | `8001` |
| `DEBUG` | Debug mode | ❌ No | `True` |
| `LOG_LEVEL` | Logging level | ❌ No | `INFO` |

### Optional Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_CLOUD_COVER` | Max cloud cover for satellite data (0-100) | `20` |
| `SATELLITE_SEARCH_DAYS` | Days to search back for satellite data | `90` |
| `CACHE_TTL` | Cache time-to-live in seconds | `3600` |
| `MAX_CACHE_SIZE` | Maximum cache entries | `100` |
| `MAX_WORKERS` | Parallel processing workers | `4` |
| `REQUEST_TIMEOUT` | Request timeout in seconds | `60` |
| `DEVELOPMENT_MODE` | Enable development features | `True` |
| `VERBOSE_LOGGING` | Enable detailed logging | `False` |

## 🔑 API Keys Setup

### WeatherAPI.com (Required)
1. Go to [WeatherAPI.com Signup](https://www.weatherapi.com/signup.aspx)
2. Create a free account
3. Get your API key from the dashboard
4. Add to `.env` file:
   ```bash
   WEATHER_API_KEY=your_api_key_here
   ```

**Free Tier Includes:**
- 1 million API calls per month
- Current weather data
- 7-day forecast
- Historical weather data
- Weather alerts
- Air quality data

### Microsoft Planetary Computer (No Key Required)
- **Public Access**: No API key needed
- **Data Sources**: Sentinel-2, Landsat-8, MODIS, Sentinel-1
- **Coverage**: Global satellite imagery
- **Update Frequency**: Real-time

## 🛠️ Environment Files

### `.env` File Structure
```bash
# Weather API Configuration
WEATHER_API_KEY=your_weatherapi_key_here

# Application Configuration
HOST=127.0.0.1
PORT=8001
DEBUG=True
LOG_LEVEL=INFO

# Satellite Data Configuration
MAX_CLOUD_COVER=20
SATELLITE_SEARCH_DAYS=90

# Cache Configuration
CACHE_TTL=3600
MAX_CACHE_SIZE=100

# Performance Configuration
MAX_WORKERS=4
REQUEST_TIMEOUT=60

# Development Configuration
DEVELOPMENT_MODE=True
VERBOSE_LOGGING=False
```

## 🚀 Startup Scripts

### Option 1: Environment-Aware Startup
```bash
python start_server.py
```
- Automatically loads `.env` file
- Validates environment variables
- Shows configuration summary
- Starts server with proper settings

### Option 2: Manual Startup
```bash
python main.py
```
- Uses system environment variables
- Requires manual environment setup

### Option 3: Development Mode
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```
- Auto-reload on code changes
- Development-friendly settings

## 🔍 Environment Validation

### Check Environment Status
```bash
python load_env.py
```

### Manual Validation
```bash
# Check if environment variables are set
echo $WEATHER_API_KEY

# Test API endpoints
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/docs
```

## 🐳 Docker Environment

### Using Docker
```bash
# Build Docker image
docker build -t zumagro-api .

# Run with environment variables
docker run -p 8001:8000 \
  -e WEATHER_API_KEY=your_key_here \
  -e DEBUG=True \
  zumagro-api
```

### Docker Compose
```yaml
version: '3.8'
services:
  zumagro-api:
    build: .
    ports:
      - "8001:8000"
    environment:
      - WEATHER_API_KEY=your_key_here
      - DEBUG=True
      - LOG_LEVEL=INFO
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Missing Weather API Key
```
❌ Error: WEATHER_API_KEY is not set!
```
**Solution**: Run `python setup_env.py` or set the environment variable

#### 2. Port Already in Use
```
❌ [Errno 48] error while attempting to bind on address ('127.0.0.1', 8001): address already in use
```
**Solution**: 
```bash
# Kill existing process
lsof -ti:8001 | xargs kill -9

# Or use different port
PORT=8002 python start_server.py
```

#### 3. Environment File Not Found
```
⚠️ No .env file found. Using system environment variables.
```
**Solution**: Create `.env` file with `python setup_env.py`

#### 4. Virtual Environment Not Activated
```
❌ ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: 
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 Environment Monitoring

### Health Check
```bash
curl http://127.0.0.1:8001/health
```

### API Documentation
- **Swagger UI**: http://127.0.0.1:8001/docs
- **ReDoc**: http://127.0.0.1:8001/redoc

### Logs
- **Server Logs**: Console output
- **Debug Mode**: Detailed request/response logging
- **Error Logs**: Exception details and stack traces

## 🔒 Security Notes

### Environment Variables
- Never commit `.env` files to version control
- Use different API keys for development/production
- Rotate API keys regularly
- Use environment-specific configurations

### API Keys
- WeatherAPI.com keys are rate-limited
- Monitor API usage in WeatherAPI dashboard
- Use caching to reduce API calls
- Implement proper error handling

## 📈 Performance Tuning

### Cache Configuration
```bash
# Increase cache TTL for better performance
CACHE_TTL=7200  # 2 hours

# Increase cache size for more data
MAX_CACHE_SIZE=500
```

### Parallel Processing
```bash
# Increase workers for better performance
MAX_WORKERS=8

# Adjust timeout for slow connections
REQUEST_TIMEOUT=120
```

### Satellite Data
```bash
# Reduce cloud cover for better data quality
MAX_CLOUD_COVER=10

# Increase search range for more data
SATELLITE_SEARCH_DAYS=180
```
