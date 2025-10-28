#!/bin/bash
# CameronPAD Start Script for Linux/macOS
# Starts the development server with auto-reload

echo "� Starting CameronPAD Server"
echo "================================"

# Check if python3 is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python is not installed or not in PATH"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Found Python: $PYTHON_CMD"

# Check if FastAPI is installed
$PYTHON_CMD -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error: FastAPI is not installed"
    echo "   Please run ./install.sh first to install dependencies"
    exit 1
fi

echo "✓ FastAPI installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Warning: .env file not found"
    echo "   Using default configuration. Run ./install.sh to set up .env file"
    echo ""
fi

echo ""
echo "🌐 Starting server on http://127.0.0.1:8000"
echo "📝 Press Ctrl+C to stop the server"
echo ""

# Start the server
$PYTHON_CMD -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
