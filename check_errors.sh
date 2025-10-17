#!/bin/bash

echo "======================================"
echo "CameronPAD Error Diagnostics"
echo "======================================"
echo ""

# Check if server is running
echo "1. Checking if server is running..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✓ Port 8000 is active"
    lsof -i :8000
else
    echo "✗ Port 8000 is NOT active - server not running!"
fi
echo ""

# Check recent logs
echo "2. Recent server logs (last 50 lines)..."
echo "--------------------------------------"
if [ -f "logs/server.log" ]; then
    tail -n 50 logs/server.log
elif journalctl -u cameronpad -n 1 > /dev/null 2>&1; then
    echo "Checking systemd logs..."
    sudo journalctl -u cameronpad -n 50 --no-pager
else
    echo "No log files found. Check where logs are being written."
fi
echo ""

# Check for Python errors
echo "3. Checking for Python errors..."
echo "--------------------------------------"
if [ -f "logs/server.log" ]; then
    grep -i "error\|exception\|traceback\|failed" logs/server.log | tail -n 20
elif journalctl -u cameronpad -n 1 > /dev/null 2>&1; then
    sudo journalctl -u cameronpad -n 100 --no-pager | grep -i "error\|exception\|traceback\|failed" | tail -n 20
fi
echo ""

# Check .env file
echo "4. Checking .env configuration..."
echo "--------------------------------------"
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    echo "API Keys configured:"
    grep "FINNHUB_TOKEN" .env | sed 's/=.*/=***HIDDEN***/'
    grep "ALPHA_VANTAGE_KEY" .env | sed 's/=.*/=***HIDDEN***/'
else
    echo "✗ .env file NOT found!"
fi
echo ""

# Check database
echo "5. Checking database..."
echo "--------------------------------------"
if [ -f "data/cameronpad_dev.db" ]; then
    echo "✓ Database file exists"
    ls -lh data/cameronpad_dev.db
else
    echo "✗ Database file NOT found!"
fi
echo ""

# Check Python environment
echo "6. Checking Python environment..."
echo "--------------------------------------"
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
    source venv/bin/activate
    echo "Python version: $(python --version)"
    echo "Checking key packages:"
    pip list | grep -E "fastapi|uvicorn|pydantic|aiohttp|python-dotenv" || echo "Some packages may be missing"
else
    echo "✗ Virtual environment NOT found!"
fi
echo ""

echo "======================================"
echo "Quick fixes to try:"
echo "======================================"
echo "1. Restart the server:"
echo "   ./deploy_replace.sh"
echo ""
echo "2. Check detailed logs:"
echo "   tail -f logs/server.log"
echo "   OR: sudo journalctl -u cameronpad -f"
echo ""
echo "3. Test if dependencies are installed:"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
