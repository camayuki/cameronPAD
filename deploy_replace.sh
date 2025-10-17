#!/bin/bash

###############################################################################
# CameronPAD Deployment Script - Replace Existing Instance
# This script stops the old instance and starts the new one
###############################################################################

set -e  # Exit on any error

echo "======================================"
echo "CameronPAD Deployment - Replace Mode"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📍 Working directory: $SCRIPT_DIR${NC}"
echo ""

###############################################################################
# Step 1: Stop Old Instance
###############################################################################

echo -e "${YELLOW}🛑 Step 1: Stopping old CameronPAD instance...${NC}"

# Check if running as systemd service
if systemctl is-active --quiet cameronpad 2>/dev/null; then
    echo "  → Found systemd service, stopping..."
    sudo systemctl stop cameronpad
    echo -e "${GREEN}  ✓ Systemd service stopped${NC}"
elif systemctl is-active --quiet cameronpad.service 2>/dev/null; then
    echo "  → Found systemd service, stopping..."
    sudo systemctl stop cameronpad.service
    echo -e "${GREEN}  ✓ Systemd service stopped${NC}"
else
    echo "  → No systemd service found, looking for running processes..."
    
    # Find and kill any uvicorn processes
    if pgrep -f "uvicorn.*cameronpad" > /dev/null; then
        echo "  → Found uvicorn processes, stopping..."
        pkill -f "uvicorn.*cameronpad" || true
        sleep 2
        
        # Force kill if still running
        if pgrep -f "uvicorn.*cameronpad" > /dev/null; then
            echo "  → Force stopping remaining processes..."
            pkill -9 -f "uvicorn.*cameronpad" || true
        fi
        echo -e "${GREEN}  ✓ Processes stopped${NC}"
    else
        echo "  → No running processes found"
    fi
fi

# Double check port 8000 is free
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}  ⚠ Port 8000 still in use, attempting to free it...${NC}"
    
    # Get PID using port 8000
    PID=$(lsof -t -i :8000 || true)
    if [ ! -z "$PID" ]; then
        echo "  → Killing process $PID on port 8000..."
        kill $PID 2>/dev/null || sudo kill $PID
        sleep 2
        
        # Force kill if needed
        if lsof -i :8000 > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null || sudo kill -9 $PID
        fi
    fi
fi

echo -e "${GREEN}✅ Old instance stopped${NC}"
echo ""

###############################################################################
# Step 2: Backup Current Data
###############################################################################

echo -e "${YELLOW}💾 Step 2: Backing up current data...${NC}"

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database if it exists
if [ -f "data/cameronpad_dev.db" ]; then
    cp "data/cameronpad_dev.db" "$BACKUP_DIR/cameronpad_dev.db.backup"
    echo -e "${GREEN}  ✓ Database backed up${NC}"
fi

# Backup .env if it exists
if [ -f ".env" ]; then
    cp ".env" "$BACKUP_DIR/.env.backup"
    echo -e "${GREEN}  ✓ .env file backed up${NC}"
fi

echo -e "${GREEN}✅ Backup created in: $BACKUP_DIR${NC}"
echo ""

###############################################################################
# Step 3: Setup Virtual Environment
###############################################################################

echo -e "${YELLOW}🐍 Step 3: Setting up Python environment...${NC}"

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "  → Removing old virtual environment..."
    rm -rf venv
fi

# Create new venv
echo "  → Creating new virtual environment..."
python3 -m venv venv

# Activate venv
echo "  → Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "  → Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

echo -e "${GREEN}✅ Virtual environment ready${NC}"
echo ""

###############################################################################
# Step 4: Install Dependencies
###############################################################################

echo -e "${YELLOW}📦 Step 4: Installing dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi
echo ""

###############################################################################
# Step 5: Verify Configuration
###############################################################################

echo -e "${YELLOW}🔍 Step 5: Verifying configuration...${NC}"

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create a .env file with your API keys:"
    echo "  FINNHUB_TOKEN=your_token_here"
    echo "  ALPHA_VANTAGE_KEY=your_key_here"
    exit 1
fi

# Check if API keys are set
if ! grep -q "FINNHUB_TOKEN=.*[a-zA-Z0-9]" .env; then
    echo -e "${YELLOW}⚠ Warning: FINNHUB_TOKEN not set in .env${NC}"
fi

if ! grep -q "ALPHA_VANTAGE_KEY=.*[a-zA-Z0-9]" .env; then
    echo -e "${YELLOW}⚠ Warning: ALPHA_VANTAGE_KEY not set in .env${NC}"
fi

# Create data directory if needed
mkdir -p data/uploads

echo -e "${GREEN}✅ Configuration verified${NC}"
echo ""

###############################################################################
# Step 6: Start New Instance
###############################################################################

echo -e "${YELLOW}🚀 Step 6: Starting new CameronPAD instance...${NC}"

# Check if we should use systemd
if [ -f "/etc/systemd/system/cameronpad.service" ]; then
    echo "  → Starting systemd service..."
    sudo systemctl start cameronpad
    sleep 2
    
    if systemctl is-active --quiet cameronpad; then
        echo -e "${GREEN}✅ Service started successfully via systemd${NC}"
        echo ""
        echo "View logs with: sudo journalctl -u cameronpad -f"
    else
        echo -e "${RED}❌ Service failed to start${NC}"
        echo "Check logs with: sudo journalctl -u cameronpad -n 50"
        exit 1
    fi
else
    echo "  → Starting application directly..."
    
    # Start in background
    nohup python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
    
    # Get the PID
    APP_PID=$!
    echo "  → Application started with PID: $APP_PID"
    
    # Wait a moment and check if it's still running
    sleep 3
    
    if ps -p $APP_PID > /dev/null; then
        echo -e "${GREEN}✅ Application started successfully${NC}"
        echo ""
        echo "  → View logs: tail -f logs/server.log"
        echo "  → Stop server: kill $APP_PID"
    else
        echo -e "${RED}❌ Application failed to start${NC}"
        echo "Check logs/server.log for errors"
        exit 1
    fi
fi

echo ""

###############################################################################
# Step 7: Verification
###############################################################################

echo -e "${YELLOW}🔍 Step 7: Verifying deployment...${NC}"

sleep 2

# Check if port 8000 is listening
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Port 8000 is active${NC}"
else
    echo -e "${RED}  ✗ Port 8000 is not listening${NC}"
fi

# Try to curl the health endpoint
if command -v curl > /dev/null; then
    sleep 2
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|307\|404"; then
        echo -e "${GREEN}  ✓ Application responding to requests${NC}"
    else
        echo -e "${YELLOW}  ⚠ Application may still be starting up...${NC}"
    fi
fi

echo ""

###############################################################################
# Done!
###############################################################################

echo "======================================"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Your CameronPAD instance is now running on:"
echo "  → http://localhost:8000"
echo "  → http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Backup stored in: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Test the application in your browser"
echo "  2. Check that stock prices are updating"
echo "  3. Verify all plugins are working"
echo ""
echo "Useful commands:"
echo "  → View logs: tail -f logs/server.log"
echo "  → Check status: lsof -i :8000"
echo "  → Stop service: pkill -f 'uvicorn.*cameronpad'"
echo ""
