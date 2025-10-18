#!/bin/bash

# Render.com Deployment Script
# This script helps you deploy to Render.com

echo "🚀 Render.com Deployment Script"
echo "================================"

# Check if git is configured
if ! git config user.name > /dev/null 2>&1; then
    echo "❌ Git not configured. Please run:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

# Check if repository is clean
if ! git diff --quiet; then
    echo "❌ Repository has uncommitted changes. Please commit first:"
    echo "   git add ."
    echo "   git commit -m 'Deploy to Render'"
    exit 1
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Code pushed to GitHub successfully!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to https://render.com"
    echo "2. Sign up/Login with GitHub"
    echo "3. Click 'New +' → 'Web Service'"
    echo "4. Connect repository: bbiruly/satellite-backend-"
    echo "5. Use these settings:"
    echo "   - Build Command: pip install --upgrade pip setuptools wheel && pip install -r requirements-render.txt"
    echo "   - Start Command: python main.py"
    echo "   - Environment: Python 3.11"
    echo "6. Add environment variables:"
    echo "   - HOST=0.0.0.0"
    echo "   - PORT=8000"
    echo "   - WEATHER_API_KEY=your_key_here"
    echo "   - PRODUCTION=true"
    echo ""
    echo "📚 For detailed guide, see: RENDER_DEPLOYMENT_GUIDE.md"
    echo "🔗 Your API will be live at: https://satellite-backend.onrender.com"
else
    echo "❌ Failed to push to GitHub. Please check your git configuration."
    exit 1
fi
