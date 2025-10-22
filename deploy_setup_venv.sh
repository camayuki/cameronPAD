#!/bin/bash

# CameronPAD Linux Server Setup Script with Virtual Environment
# This script sets up the application with a virtual environment

set -e  # Exit on any error

echo "🚀 CameronPAD Server Setup (Virtual Environment)"
echo "================================================"

# Navigate to application directory
cd /opt/cameronpad

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Upgrade pip (use venv's pip directly)
echo "⬆️  Upgrading pip..."
./venv/bin/pip install --upgrade pip

# Install requirements (use venv's pip directly)
echo "📚 Installing requirements..."
./venv/bin/pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the server:"
echo "  1. SSH to your server: ssh root@ubuntu-2gb-ash-1"
echo "  2. cd /opt/cameronpad"
echo "  3. source venv/bin/activate"
echo "  4. python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or use the systemd service (recommended):"
echo "  sudo systemctl start cameronpad"
echo ""
