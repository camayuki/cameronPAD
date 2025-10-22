#!/bin/bash
# CameronPAD Installation Script for Linux/macOS
# This script installs dependencies and sets up the application

echo "========================================"
echo "   CameronPAD Installation Script"
echo "========================================"
echo ""

# Check if Python is installed
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✓ Found: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo "✗ Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if (( $(echo "$VERSION < 3.8" | bc -l) )); then
    echo "✗ Python 3.8+ is required. Current version: $VERSION"
    exit 1
fi

echo ""
echo "Installing/Updating Python packages..."
echo "This may take a few minutes..."

# Upgrade pip first
$PYTHON_CMD -m pip install --upgrade pip

# Install requirements
$PYTHON_CMD -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Installation failed!"
    exit 1
fi

echo ""
echo "✓ All packages installed successfully!"

# Create necessary directories
echo ""
echo "Creating necessary directories..."

directories=(
    "data"
    "data/blog_uploads"
    "data/journal_uploads"
    "logs"
    "backups"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  ✓ Created: $dir"
    else
        echo "  ✓ Exists: $dir"
    fi
done

# Check for .env file
echo ""
echo "Checking configuration..."
if [ ! -f ".env" ]; then
    echo "  ! .env file not found"
    echo "    Creating .env from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "  ✓ .env file created"
        echo "    Please edit .env to configure your API keys"
    else
        echo "  ! .env.example not found. You may need to create .env manually"
    fi
else
    echo "  ✓ .env file exists"
fi

# Check for FFmpeg (optional for video metadata)
echo ""
echo "Checking optional dependencies..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1)
    echo "  ✓ FFmpeg found: Video metadata extraction enabled"
else
    echo "  ! FFmpeg not found: Video metadata will use file timestamps"
    echo "    Install FFmpeg for better video date detection:"
    echo "      Ubuntu/Debian: sudo apt install ffmpeg"
    echo "      macOS: brew install ffmpeg"
fi

echo ""
echo "========================================"
echo "   Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review and edit .env file with your API keys"
echo "  2. Run: ./start.sh"
echo ""
