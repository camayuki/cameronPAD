#!/bin/bash
# CameronPAD Production Start Script for Linux

echo "🔍 Checking if port 8000 is already in use..."
if sudo lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is in use. Killing existing process..."
    sudo fuser -k 8000/tcp
    sleep 2
    echo "✅ Port 8000 freed"
fi

# Activate virtual environment
source venv/bin/activate

# Calculate optimal number of workers (2 * CPU cores + 1)
WORKERS=$(($(nproc) * 2 + 1))

echo "🚀 Starting CameronPAD in production mode with $WORKERS workers..."

# Run the application with multiple workers for production
python3 -m uvicorn app_new.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $WORKERS \
    --log-level info \
    --access-log
