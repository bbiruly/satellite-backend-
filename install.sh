#!/bin/bash

# Satellite Backend Installation Script
# This script installs dependencies avoiding Rust compilation issues

echo "🚀 Installing Satellite Backend Dependencies..."

# Check Python version
python3 --version

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install core dependencies first
echo "📦 Installing core dependencies..."
python3 -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0

# Install HTTP clients
echo "📦 Installing HTTP clients..."
python3 -m pip install requests>=2.31.0 httpx>=0.25.0

# Install environment handling
echo "📦 Installing environment dependencies..."
python3 -m pip install python-dotenv>=1.0.0

# Install production dependencies
echo "📦 Installing production dependencies..."
python3 -m pip install gunicorn>=21.2.0 python-multipart>=0.0.6 aiofiles>=23.2.0 psutil>=5.9.0

# Install geospatial libraries with pre-compiled wheels
echo "📦 Installing geospatial libraries (using pre-compiled wheels)..."
python3 -m pip install --only-binary=all numpy==1.24.4
python3 -m pip install --only-binary=all rasterio==1.3.8
python3 -m pip install --only-binary=all pyproj==3.6.0
python3 -m pip install --only-binary=all shapely==2.0.2
python3 -m pip install --only-binary=all xarray==2023.7.0
python3 -m pip install --only-binary=all rioxarray==0.15.4

# Install satellite data processing
echo "📦 Installing satellite data processing libraries..."
python3 -m pip install planetary-computer==1.0.0 pystac-client==0.7.0 pystac==1.8.0

echo "✅ Installation complete!"
echo "🚀 To start the server: python3 main.py"
echo "📚 API documentation: http://localhost:8000/docs"
