# 🚀 Render.com Deployment Guide

## Step-by-Step Deployment on Render

### 1. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Connect your GitHub repository

### 2. Deploy from GitHub Repository

#### Option A: Automatic Deployment
1. **Connect Repository:**
   - Click "New +" → "Web Service"
   - Connect GitHub account
   - Select repository: `bbiruly/satellite-backend-`

2. **Configure Service:**
   - **Name**: `satellite-backend`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)` or `Frankfurt (EU)`
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements-deploy.txt`
   - **Start Command**: `python main.py`

3. **Environment Variables:**
   ```
   HOST=0.0.0.0
   PORT=8000
   DEBUG=false
   PRODUCTION=true
   LOG_LEVEL=INFO
   WEATHER_API_KEY=your_weatherapi_key_here
   MAX_CLOUD_COVER=20
   CACHE_TTL=3600
   MAX_CACHE_SIZE=100
   MAX_WORKERS=4
   REQUEST_TIMEOUT=60
   ```

#### Option B: Using render.yaml (Recommended)
1. **Deploy with Configuration File:**
   - Repository already has `render.yaml`
   - Render will automatically detect and use it
   - Just connect repository and deploy

### 3. Get Weather API Key (Required)

1. **Sign up at WeatherAPI.com:**
   - Go to [weatherapi.com/signup](https://www.weatherapi.com/signup.aspx)
   - Create free account
   - Get API key from dashboard

2. **Add to Render:**
   - Go to your service dashboard
   - Click "Environment"
   - Add `WEATHER_API_KEY` with your key

### 4. Deploy and Test

#### Deploy:
1. Click "Create Web Service"
2. Wait for build to complete (5-10 minutes)
3. Get your service URL: `https://satellite-backend.onrender.com`

#### Test Deployment:
```bash
# Health check
curl https://satellite-backend.onrender.com/health

# API documentation
https://satellite-backend.onrender.com/docs

# Test NPK analysis
curl -X POST "https://satellite-backend.onrender.com/api/npk-analysis-by-date" \
  -H "Content-Type: application/json" \
  -d '{
    "fieldId": "test",
    "coordinates": [21.8468660, 82.0069310],
    "crop_type": "RICE",
    "field_area_hectares": 1.0
  }'
```

## Render.com Configuration Details

### Free Tier Limits:
- **Memory**: 512MB
- **CPU**: 0.1 CPU
- **Bandwidth**: 100GB/month
- **Sleep**: After 15 minutes of inactivity
- **Build Time**: 90 minutes/month

### Paid Tier Benefits:
- **Memory**: Up to 8GB
- **CPU**: Up to 8 CPU
- **Always On**: No sleep
- **Custom Domains**: Yes
- **SSL**: Automatic

## Troubleshooting Render Deployment

### 1. Build Fails
**Error**: `Build failed: pip install error`

**Solution**:
```bash
# Check requirements-deploy.txt
# Ensure all dependencies are compatible
# Use exact versions to avoid conflicts
```

### 2. Service Won't Start
**Error**: `Service failed to start`

**Solution**:
```bash
# Check start command
# Ensure main.py is in root directory
# Check environment variables
```

### 3. Memory Issues
**Error**: `Process killed due to memory limit`

**Solution**:
```bash
# Reduce MAX_WORKERS to 2
# Reduce MAX_CACHE_SIZE to 50
# Upgrade to paid plan
```

### 4. Slow Response Times
**Symptoms**: API responses > 30 seconds

**Solutions**:
```bash
# Check logs in Render dashboard
# Monitor memory usage
# Consider upgrading plan
```

## Environment Variables Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `false` | Debug mode |
| `PRODUCTION` | `true` | Production mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `WEATHER_API_KEY` | `your_key` | Weather API key |
| `MAX_CLOUD_COVER` | `20` | Max cloud cover % |
| `CACHE_TTL` | `3600` | Cache time-to-live |
| `MAX_CACHE_SIZE` | `100` | Max cache entries |
| `MAX_WORKERS` | `4` | Parallel workers |
| `REQUEST_TIMEOUT` | `60` | Request timeout |

## Monitoring and Logs

### View Logs:
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab
4. View real-time logs

### Monitor Performance:
1. Click "Metrics" tab
2. Monitor CPU, Memory, Response Time
3. Set up alerts if needed

## Custom Domain (Paid Plans)

### Setup Custom Domain:
1. Go to service settings
2. Click "Custom Domains"
3. Add your domain
4. Update DNS records
5. SSL certificate auto-generated

### DNS Configuration:
```
Type: CNAME
Name: api.yourdomain.com
Value: satellite-backend.onrender.com
```

## Cost Estimation

### Free Tier:
- **Cost**: $0/month
- **Limitations**: Sleeps after 15 min inactivity
- **Good for**: Development, testing, low traffic

### Starter Plan:
- **Cost**: $7/month
- **Benefits**: Always on, 512MB RAM
- **Good for**: Small production apps

### Professional Plan:
- **Cost**: $25/month
- **Benefits**: 2GB RAM, better performance
- **Good for**: Production apps with moderate traffic

## Security Considerations

### Environment Variables:
- Never commit API keys to repository
- Use Render's environment variable system
- Rotate keys regularly

### HTTPS:
- Automatic SSL certificate
- Force HTTPS in production
- Secure API endpoints

### Rate Limiting:
- Built-in rate limiting
- Monitor usage in dashboard
- Set appropriate limits

## Backup and Recovery

### Database Backup:
- Render provides automatic backups
- Export data regularly
- Test restore procedures

### Code Backup:
- GitHub repository is your backup
- Tag releases for rollback
- Keep deployment history

## Support and Resources

### Render Documentation:
- [render.com/docs](https://render.com/docs)
- Python deployment guide
- Environment variables guide

### Community Support:
- Render community forum
- GitHub issues
- Stack Overflow

## Next Steps After Deployment

1. **Test All Endpoints**: Verify API functionality
2. **Set Up Monitoring**: Monitor performance and errors
3. **Configure Alerts**: Set up notifications for issues
4. **Update Documentation**: Update API docs with new URL
5. **Set Up CI/CD**: Automatic deployments from GitHub

## API Endpoints After Deployment

Your API will be available at:
- **Base URL**: `https://satellite-backend.onrender.com`
- **Health Check**: `GET /health`
- **API Docs**: `GET /docs`
- **NPK Analysis**: `POST /api/npk-analysis-by-date`
- **Mobile API**: `POST /api/npk-analysis-mobile`
- **Historical Trends**: `GET /api/historical-trends`

## Success Checklist

- [ ] Repository connected to Render
- [ ] Service deployed successfully
- [ ] Environment variables configured
- [ ] Weather API key added
- [ ] Health check working
- [ ] API documentation accessible
- [ ] NPK analysis endpoint working
- [ ] Custom domain configured (if needed)
- [ ] Monitoring set up
- [ ] Documentation updated

## Need Help?

1. Check Render logs for errors
2. Verify environment variables
3. Test locally first
4. Check Render documentation
5. Contact support if needed

---

**Your satellite backend will be live at: `https://satellite-backend.onrender.com`** 🚀
