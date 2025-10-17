#!/bin/bash
# deploy_after_winscp.sh
# Run this script on Linux AFTER transferring files with WinSCP
# Usage: ./deploy_after_winscp.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════"
echo "  CameronPAD Post-Transfer Deployment Script"
echo "════════════════════════════════════════════════════"
echo ""

# Get current directory
DEPLOY_DIR=$(pwd)
echo "📍 Deploy directory: $DEPLOY_DIR"
echo ""

# Stop existing service
echo "⏸️  Stopping existing service..."
if systemctl is-active --quiet cameronpad 2>/dev/null; then
    sudo systemctl stop cameronpad
    echo "   ✅ Service stopped"
else
    echo "   ℹ️  Service not running or not found"
fi
echo ""

# Backup existing .env and database (if they exist)
echo "💾 Creating backups..."
if [ -f ".env" ]; then
    cp .env ~/.env.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✅ Backed up .env"
else
    echo "   ⚠️  No .env file found"
fi

if [ -f "data/cameronpad_dev.db" ]; then
    cp data/cameronpad_dev.db ~/cameronpad_dev.db.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✅ Backed up database"
else
    echo "   ℹ️  No database found (fresh install)"
fi
echo ""

# Check for .env file
echo "🔍 Checking configuration..."
if [ ! -f ".env" ]; then
    echo "   ❌ ERROR: .env file not found!"
    echo "   Please ensure .env was transferred or restore from backup:"
    echo "   cp ~/.env.backup .env"
    exit 1
fi

# Verify .env has content
if ! grep -q "FINNHUB_TOKEN" .env; then
    echo "   ⚠️  WARNING: .env file may be incomplete"
    echo "   Please verify it contains API keys"
fi
echo "   ✅ .env file exists"
echo ""

# Remove old virtual environment
echo "🗑️  Removing old virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "   ✅ Old venv removed"
else
    echo "   ℹ️  No existing venv found"
fi
echo ""

# Create new virtual environment
echo "🐍 Creating new virtual environment..."
python3 -m venv venv
echo "   ✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet
echo "   ✅ pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies (this may take a minute)..."
if pip install -r requirements.txt --quiet; then
    echo "   ✅ Dependencies installed successfully"
else
    echo "   ❌ Error installing dependencies"
    exit 1
fi
echo ""

# Create data directory if it doesn't exist
echo "📁 Ensuring data directories exist..."
mkdir -p data
mkdir -p data/uploads
echo "   ✅ Data directories ready"
echo ""

# Set permissions
echo "🔐 Setting file permissions..."
chmod 755 data/
if [ -f "data/cameronpad_dev.db" ]; then
    chmod 644 data/cameronpad_dev.db
fi
echo "   ✅ Permissions set"
echo ""

# Test configuration
echo "🔍 Testing configuration..."
TEST_OUTPUT=$(python3 << 'EOF'
from dotenv import load_dotenv
import os
load_dotenv()
finnhub = 'Yes' if os.getenv('FINNHUB_TOKEN') else 'NO'
alpha = 'Yes' if os.getenv('ALPHA_VANTAGE_KEY') else 'NO'
print(f"Finnhub: {finnhub}, AlphaVantage: {alpha}")
EOF
)
echo "   API Keys: $TEST_OUTPUT"

if [[ $TEST_OUTPUT == *"NO"* ]]; then
    echo "   ⚠️  WARNING: Some API keys not found!"
    echo "   Please check your .env file"
fi
echo ""

# Check if systemd service exists
echo "🔍 Checking for systemd service..."
if systemctl list-unit-files | grep -q cameronpad.service; then
    echo "   ✅ systemd service found"
    USING_SYSTEMD=true
else
    echo "   ℹ️  No systemd service configured"
    USING_SYSTEMD=false
fi
echo ""

# Offer to start the service
if [ "$USING_SYSTEMD" = true ]; then
    echo "▶️  Starting service with systemd..."
    sudo systemctl start cameronpad
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    if systemctl is-active --quiet cameronpad; then
        echo "   ✅ Service started successfully!"
        echo ""
        echo "📊 Service Status:"
        sudo systemctl status cameronpad --no-pager | head -15
    else
        echo "   ❌ Service failed to start!"
        echo ""
        echo "📋 Recent logs:"
        sudo journalctl -u cameronpad -n 20 --no-pager
    fi
else
    echo "ℹ️  To start manually, run:"
    echo "   source venv/bin/activate"
    echo "   python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "   Or with Gunicorn:"
    echo "   gunicorn app_new.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ Deployment Complete!"
echo "════════════════════════════════════════════════════"
echo ""
echo "📝 Useful commands:"
echo "   View logs:    sudo journalctl -u cameronpad -f"
echo "   Stop service: sudo systemctl stop cameronpad"
echo "   Restart:      sudo systemctl restart cameronpad"
echo "   Status:       sudo systemctl status cameronpad"
echo ""
echo "🌐 Access your application at: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
