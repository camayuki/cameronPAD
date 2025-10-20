#!/bin/bash
# CameronPAD Quick Setup Script for Linux

set -e  # Exit on error

echo "🚀 CameronPAD Setup Script"
echo "=========================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Check if Python 3.8+
REQUIRED_PYTHON="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    echo "❌ Error: Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Upgrade pip using python3 -m pip (more reliable)
echo "⬆️  Upgrading pip..."
venv/bin/python3 -m pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
venv/bin/python3 -m pip install -r requirements.txt

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    
    # Generate secure keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > .env << EOF
# Environment
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad.db

# Optional: Stock API Keys
# FINNHUB_TOKEN=your_token_here
# ALPHA_VANTAGE_KEY=your_key_here

# Optional: Surf API
# STORMGLASS_API_KEY=your_key_here
EOF
    
    echo "✓ Created .env file with secure random keys"
else
    echo "⚠️  .env file already exists, skipping..."
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x start.sh
chmod +x start_prod.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create an admin user: python3 create_admin.py"
echo "2. Start development server: ./start.sh"
echo "3. Or start production server: ./start_prod.sh"
echo ""
echo "🌐 The application will be available at http://localhost:8000"
echo ""
