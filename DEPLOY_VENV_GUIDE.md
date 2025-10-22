# Linux Server Deployment Guide (Virtual Environment)

## Problem
Modern Linux distributions (Debian/Ubuntu) have "externally-managed-environment" protection that prevents installing packages directly with pip to avoid breaking system Python.

## Solution: Virtual Environment

### Step 1: Upload Files to Server
Use WinSCP or similar to upload to `/opt/cameronpad`:
- All project files
- `deploy_setup_venv.sh`
- `cameronpad.service`

### Step 2: Run Setup Script

SSH to your server:
```bash
ssh root@ubuntu-2gb-ash-1
cd /opt/cameronpad
chmod +x deploy_setup_venv.sh
./deploy_setup_venv.sh
```

This will:
- ✅ Create a virtual environment in `/opt/cameronpad/venv`
- ✅ Install all requirements inside the virtual environment
- ✅ Not affect system Python at all

### Step 3: Create .env File

Create `/opt/cameronpad/.env` with your API keys:
```bash
FINNHUB_TOKEN=d3r3519r01qopgh6oqsgd3r3519r01qopgh6oqt0
ALPHA_VANTAGE_KEY=HG933KBDCEDV99X4
```

### Step 4: Test Run

Test the server manually:
```bash
cd /opt/cameronpad
source venv/bin/activate
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

### Step 5: Setup Systemd Service (Automatic Start)

```bash
# Copy service file
cp /opt/cameronpad/cameronpad.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable cameronpad

# Start the service
systemctl start cameronpad

# Check status
systemctl status cameronpad
```

## Managing the Service

```bash
# Start
systemctl start cameronpad

# Stop
systemctl stop cameronpad

# Restart
systemctl restart cameronpad

# View logs
journalctl -u cameronpad -f

# Check status
systemctl status cameronpad
```

## Updating the Application

When you deploy updates:
```bash
cd /opt/cameronpad
systemctl stop cameronpad

# Upload new files via WinSCP

# Activate venv and install any new requirements
source venv/bin/activate
pip install -r requirements.txt

# Restart
systemctl start cameronpad
```

## Troubleshooting

### Virtual Environment Not Activating
```bash
cd /opt/cameronpad
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Check Logs
```bash
# Application logs
cat /opt/cameronpad/logs/server_debug.log

# System logs
journalctl -u cameronpad -n 50

# Real-time logs
journalctl -u cameronpad -f
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Why Virtual Environment?

1. **Isolated Dependencies**: Your app's packages don't affect system Python
2. **No Permission Issues**: No need for sudo or --break-system-packages
3. **Best Practice**: Industry standard for Python deployment
4. **Easy Cleanup**: Just delete the `venv` folder to start fresh
5. **Multiple Versions**: Can have different Python versions per project

## File Structure After Setup

```
/opt/cameronpad/
├── venv/                    # Virtual environment (created by script)
│   ├── bin/
│   │   ├── python           # Python interpreter for this project
│   │   ├── pip              # pip for this project
│   │   └── uvicorn          # uvicorn for this project
│   └── lib/                 # All installed packages here
├── app_new/                 # Your application
├── plugins/
├── templates/
├── requirements.txt
├── .env                     # API keys (create this manually)
└── logs/

/etc/systemd/system/
└── cameronpad.service       # Service definition
```
