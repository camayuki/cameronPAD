echo "🚀 Starting CameronPAD on port 8000..."

#!/bin/bash
# Robust CameronPAD Start Script for Linux

set -e

echo "🔍 Checking if port 8000 is already in use..."
if command -v lsof >/dev/null 2>&1 && sudo lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is in use. Killing existing process..."
    sudo fuser -k 8000/tcp || true
    sleep 2
    echo "✅ Port 8000 freed"
fi

# Always fix Windows line endings in venv/bin/activate
if [ -f venv/bin/activate ]; then
    sed -i 's/\r$//' venv/bin/activate
else
    echo "❌ venv/bin/activate not found. Please create a virtual environment first."
    exit 1
fi

# Check for python3 and pip3
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ python3 not found. Please install Python 3."
    exit 1
fi
if ! command -v pip3 >/dev/null 2>&1; then
    echo "❌ pip3 not found. Please install pip for Python 3."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Ensure uvicorn is installed in venv
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "Installing uvicorn..."
    pip3 install uvicorn
fi

echo "🚀 Starting CameronPAD on port 8000..."
python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000 --reload
