#!/bin/bash
# CameronPAD Quick Setup Script for Linux
# This script automates the initial setup process

set -e  # Exit on error

echo "=================================="
echo "CameronPAD Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✓ Found Python $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Stock Service API Keys
FINNHUB_TOKEN=your_finnhub_token_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Service Configuration
POLL_SECONDS=60
SHOWCASE_REFRESH=300
COOLDOWN_MIN=30
ALPHA_MIN_INTERVAL=13.0

# Application Configuration
SECRET_KEY=change-this-secret-key-in-production-use-random-string
DEBUG=false
EOF
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys!"
    echo "   Run: nano .env"
else
    echo "✓ .env file already exists"
fi

# Create data directory
echo ""
echo "Creating data directory..."
mkdir -p data
mkdir -p data/uploads
echo "✓ Data directories created"

# Check if admin user exists
echo ""
echo "Checking for admin user..."
if [ -f "create_admin.py" ]; then
    echo ""
    echo "Do you want to create an admin user now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        python create_admin.py
    else
        echo "⚠️  Remember to create an admin user later by running: python create_admin.py"
    fi
else
    echo "⚠️  create_admin.py not found - you may need to create users manually"
fi

# Display completion message
echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys: nano .env"
echo "2. Start the application:"
echo "   - Development: python -m uvicorn app_new.main:app --reload --host 0.0.0.0 --port 8000"
echo "   - Production: gunicorn app_new.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
echo ""
echo "3. Access the application at: http://localhost:8000"
echo ""
echo "For production deployment, see DEPLOYMENT.md"
echo ""
