# CameronPAD - Quick Install Commands for Linux

## Option 1: Use Setup Script (Recommended)

```bash
chmod +x setup_simple.sh
./setup_simple.sh
```

## Option 2: Manual Installation (Copy-Paste These Commands)

```bash
# Create virtual environment
python3 -m venv venv

# Install requirements
venv/bin/python3 -m pip install --upgrade pip
venv/bin/python3 -m pip install -r requirements.txt

# Create directories
mkdir -p data logs

# Generate .env file (copy-paste this entire block)
cat > .env << 'EOF'
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
SECRET_KEY=change-this-to-a-random-secret-key-in-production
JWT_SECRET_KEY=change-this-to-another-random-secret-key
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad.db
EOF

# Make scripts executable
chmod +x start.sh start_prod.sh

# Create admin user
source venv/bin/activate
python3 create_admin.py

# Start server
venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

## Option 3: Absolute Minimal (One Command at a Time)

```bash
# 1. Create venv
python3 -m venv venv

# 2. Install packages
venv/bin/python3 -m pip install -r requirements.txt

# 3. Create data folder
mkdir -p data

# 4. Start server (will create database automatically)
venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

Then visit http://your-server-ip:8000

## Troubleshooting

### If you get "python3-venv not found"
```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

### If you get "permission denied"
```bash
chmod +x *.sh
```

### If port 8000 is in use
```bash
# Kill existing process
sudo lsof -i :8000
sudo kill -9 <PID>

# Or use different port
venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8080
```

### To stop the server
Press `Ctrl+C` in the terminal

### To restart
```bash
# Stop with Ctrl+C, then:
venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

## Quick Reference

**Activate venv:**
```bash
source venv/bin/activate
```

**Run server (after venv activated):**
```bash
python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

**Run server (without activating venv):**
```bash
venv/bin/python3 -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

**Create admin user:**
```bash
source venv/bin/activate
python3 create_admin.py
```

**Check what's running on port 8000:**
```bash
sudo lsof -i :8000
```

**View logs (if running as service):**
```bash
sudo journalctl -u cameronpad -f
```
