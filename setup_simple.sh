#!/bin/bash
# Simple CameronPAD Setup - Manual Steps

echo "=== CameronPAD Simple Setup ==="
echo ""

# Step 1
echo "Step 1: Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error creating venv. Try: sudo apt install python3-venv"
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

# Step 2
echo "Step 2: Upgrading pip..."
venv/bin/python3 -m pip install --upgrade pip
echo "✓ Pip upgraded"
echo ""

# Step 3
echo "Step 3: Installing requirements (this may take a minute)..."
venv/bin/python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing requirements"
    exit 1
fi
echo "✓ Requirements installed"
echo ""

# Step 4
echo "Step 4: Creating directories..."
mkdir -p data
mkdir -p logs
echo "✓ Directories created"
echo ""

# Step 5
echo "Step 5: Generating .env file..."
if [ ! -f .env ]; then
    SECRET_KEY=$(venv/bin/python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(venv/bin/python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > .env << EOF
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad.db
EOF
    echo "✓ .env file created with secure keys"
else
    echo "⚠️  .env already exists, skipping"
fi
echo ""

# Step 6
echo "Step 6: Making scripts executable..."
chmod +x start.sh 2>/dev/null || true
chmod +x start_prod.sh 2>/dev/null || true
echo "✓ Scripts executable"
echo ""

echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create admin user:"
echo "   source venv/bin/activate"
echo "   python3 create_admin.py"
echo ""
echo "2. Start server:"
echo "   ./start.sh"
echo "   or manually: venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "3. Access at: http://your-server-ip:8000"
echo "=========================================="
