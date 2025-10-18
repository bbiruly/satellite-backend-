# 🔧 Troubleshooting Guide

## Common Installation Issues

### 1. Rust Compilation Error (maturin failed)

**Error:**
```
error: subprocess-exited-with-error
× Preparing metadata (pyproject.toml) did not run successfully.
│ exit code: 1
💥 maturin failed
```

**Solution:**
```bash
# Use the installation script
./install.sh

# Or install with pre-compiled wheels
pip install --only-binary=all -r requirements-deploy.txt
```

### 2. GDAL/Geospatial Library Issues

**Error:**
```
ERROR: Could not find a version that satisfies the requirement rasterio
```

**Solution:**
```bash
# Install system dependencies first (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y libgdal-dev libproj-dev libgeos-dev

# Then install Python packages
pip install --only-binary=all rasterio pyproj shapely
```

### 3. Port Already in Use

**Error:**
```
[Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): address already in use
```

**Solution:**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
PORT=8001 python3 main.py
```

### 4. Permission Denied (GitHub Push)

**Error:**
```
remote: Permission to officialzumagro/pyhon-processor.git denied to bbiruly
```

**Solution:**
```bash
# Check remote URL
git remote -v

# Update remote URL
git remote set-url origin https://github.com/bbiruly/satellite-backend-.git
```

### 5. Environment Variables Not Loading

**Error:**
```
WARNING: WEATHER_API_KEY not set in environment variables
```

**Solution:**
```bash
# Create .env file
cp .env.example .env

# Edit .env file with your API keys
nano .env

# Or set environment variables
export WEATHER_API_KEY=your_key_here
```

## Deployment Issues

### 1. Docker Build Fails

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c pip install" did not complete successfully
```

**Solution:**
```bash
# Use the deployment requirements
docker build -f Dockerfile.deploy .

# Or build with no cache
docker build --no-cache -t satellite-backend .
```

### 2. Fly.io Deployment Fails

**Error:**
```
Error: failed to fetch an image or run a container
```

**Solution:**
```bash
# Check fly.toml configuration
fly config validate

# Deploy with verbose logging
fly deploy --verbose
```

### 3. Memory Issues

**Error:**
```
Process killed due to memory limit
```

**Solution:**
```bash
# Increase memory in fly.toml
[[vm]]
  memory = '2gb'  # Increase from 1gb

# Or optimize code
# Reduce parallel processing workers
```

## Performance Issues

### 1. Slow Response Times

**Symptoms:**
- API responses > 5 seconds
- Timeout errors

**Solutions:**
```bash
# Check cache status
curl http://localhost:8000/api/cache-stats

# Clear cache
curl -X POST http://localhost:8000/api/clear-cache

# Check rate limiting
curl http://localhost:8000/api/rate-limit-stats
```

### 2. High Memory Usage

**Symptoms:**
- Server crashes
- Out of memory errors

**Solutions:**
```bash
# Monitor memory usage
curl http://localhost:8000/api/system-stats

# Reduce cache size in .env
MAX_CACHE_SIZE=50

# Reduce parallel workers
MAX_WORKERS=2
```

## API Issues

### 1. NPK Analysis Fails

**Error:**
```
{"success": false, "error": "No satellite data available"}
```

**Solutions:**
```bash
# Check fallback stats
curl http://localhost:8000/api/fallback-stats

# Try different coordinates
curl -X POST "http://localhost:8000/api/npk-analysis-by-date" \
  -H "Content-Type: application/json" \
  -d '{"fieldId": "test", "coordinates": [21.8468660, 82.0069310], "crop_type": "RICE"}'
```

### 2. Weather API Issues

**Error:**
```
Weather data unavailable
```

**Solutions:**
```bash
# Check API key
echo $WEATHER_API_KEY

# Test weather endpoint
curl -X POST "http://localhost:8000/api/weather" \
  -H "Content-Type: application/json" \
  -d '{"fieldId": "test", "coordinates": [21.8468660, 82.0069310]}'
```

## Quick Fixes

### Reset Everything
```bash
# Stop server
pkill -f "python3 main.py"

# Clear cache
rm -rf __pycache__/
rm -rf .cache/

# Reinstall dependencies
pip uninstall -r requirements.txt -y
./install.sh

# Start server
python3 main.py
```

### Check System Status
```bash
# Health check
curl http://localhost:8000/health

# System stats
curl http://localhost:8000/api/system-stats

# All endpoints status
curl http://localhost:8000/api/fallback-stats
curl http://localhost:8000/api/cache-stats
curl http://localhost:8000/api/rate-limit-stats
```

## Getting Help

1. **Check logs**: Look at server output for error messages
2. **Test endpoints**: Use the health check and stats endpoints
3. **Verify configuration**: Check .env file and environment variables
4. **Check dependencies**: Ensure all packages are installed correctly
5. **Monitor resources**: Check memory and CPU usage

## Contact

For additional help, check the documentation in the `/docs` folder or create an issue in the repository.
