# 🚀 API Quick Reference Guide

## Essential Endpoints

### 1. NPK Analysis (Main)
```bash
curl -X POST "http://localhost:8001/api/npk-analysis-by-date" \
  -H "Content-Type: application/json" \
  -d '{
    "fieldId": "test-field",
    "coordinates": [21.8468660, 82.0069310],
    "specific_date": "2025-01-15",
    "crop_type": "RICE",
    "field_area_hectares": 1.0
  }'
```

### 2. Mobile Version
```bash
curl -X POST "http://localhost:8001/api/npk-analysis-mobile" \
  -H "Content-Type: application/json" \
  -d '{
    "fieldId": "mobile-test",
    "coordinates": [21.8468660, 82.0069310],
    "specific_date": "2025-01-15",
    "crop_type": "RICE",
    "field_area_hectares": 1.0
  }'
```

### 3. Historical Trends
```bash
# 6 months (default)
curl "http://localhost:8001/api/historical-trends?lat=21.8468660&lon=82.0069310&crop_type=RICE"

# 12 months
curl "http://localhost:8001/api/historical-trends?lat=21.8468660&lon=82.0069310&months=12&crop_type=RICE"
```

## System Status

### Health Check
```bash
curl "http://localhost:8001/health"
```

### Performance Stats
```bash
# Fallback system stats
curl "http://localhost:8001/api/fallback-stats"

# Cache performance
curl "http://localhost:8001/api/cache-stats"

# Rate limiting
curl "http://localhost:8001/api/rate-limit-stats"
```

## Response Examples

### Successful NPK Analysis
```json
{
  "success": true,
  "soilNutrients": {
    "Nitrogen": 230.0,
    "Phosphorus": 28.0,
    "Potassium": 177.0,
    "Soc": 1.5
  },
  "metadata": {
    "satelliteSource": "Sentinel-2",
    "dataQuality": "high",
    "confidenceScore": 0.85,
    "processingTime": "1.2s"
  }
}
```

### Rate Limit Exceeded
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "retry_after_seconds": 45
}
```

## Common Parameters

### Crop Types
- `RICE` - Rice cultivation
- `WHEAT` - Wheat cultivation  
- `CORN` - Corn/Maize cultivation
- `VEGETABLES` - Vegetable crops
- `FRUITS` - Fruit crops
- `GENERIC` - General analysis

### Coordinates Format
- **Latitude**: -90 to 90 (decimal degrees)
- **Longitude**: -180 to 180 (decimal degrees)
- **Example**: `[21.8468660, 82.0069310]` (Rajnandgaon, Chhattisgarh)

### Date Format
- **Format**: YYYY-MM-DD
- **Example**: `"2025-01-15"`
- **Range**: Current date and historical (satellite data availability dependent)

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue |
| 400 | Bad Request | Check parameters |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Contact support |

## Performance Tips

1. **Use caching**: Same location requests are cached for 24 hours
2. **Mobile endpoint**: Use `/api/npk-analysis-mobile` for mobile apps
3. **Batch requests**: Process multiple fields in sequence
4. **Monitor limits**: Check rate limit stats regularly

## Testing Commands

### Basic Test
```bash
curl -X POST "http://localhost:8001/api/npk-analysis-by-date" \
  -H "Content-Type: application/json" \
  -d '{"fieldId": "test", "coordinates": [21.8468660, 82.0069310], "specific_date": "2025-01-15", "crop_type": "RICE", "field_area_hectares": 1.0}' | jq '.success'
```

### Performance Test
```bash
time curl -X POST "http://localhost:8001/api/npk-analysis-by-date" \
  -H "Content-Type: application/json" \
  -d '{"fieldId": "perf-test", "coordinates": [21.8468660, 82.0069310], "specific_date": "2025-01-15", "crop_type": "RICE", "field_area_hectares": 1.0}'
```

### Historical Test
```bash
curl "http://localhost:8001/api/historical-trends?lat=21.8468660&lon=82.0069310&months=3&crop_type=RICE" | jq '.data.data_points'
```

---

*For detailed documentation, see API_GUIDE.md*
