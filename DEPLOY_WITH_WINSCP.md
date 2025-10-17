# Deploying CameronPAD with WinSCP (Overwriting Existing Installation)

This guide covers how to update your Linux server deployment by copying files from Windows using WinSCP.

## Pre-Deployment Checklist

### On Windows (Before Transfer)

1. **Ensure .env file has correct values**
   ```powershell
   # Check your .env file
   Get-Content .env
   ```
   Make sure it contains your actual API keys (not the placeholder values).

2. **Test locally first**
   ```powershell
   # Make sure everything works on Windows
   py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
   ```
   Verify the stock service works and prices update.

3. **Optional: Create a backup copy**
   ```powershell
   # Zip the entire project
   Compress-Archive -Path D:\Repositories\CameronPAD\cameronpad -DestinationPath D:\cameronpad_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip
   ```

## Deployment Steps

### Step 1: Backup Existing Linux Installation

**Before overwriting**, backup your existing installation on Linux:

1. **Connect via SSH** (or use PuTTY)
   ```bash
   ssh user@your-server-ip
   ```

2. **Stop the running service** (if using systemd)
   ```bash
   sudo systemctl stop cameronpad
   ```

3. **Backup the current installation**
   ```bash
   # Go to parent directory
   cd /home/your-username/
   
   # Create backup with timestamp
   tar -czf cameronpad_backup_$(date +%Y%m%d_%H%M%S).tar.gz cameronpad/
   
   # Or just rename the directory
   mv cameronpad cameronpad_backup_$(date +%Y%m%d_%H%M%S)
   
   # Create fresh directory
   mkdir cameronpad
   ```

4. **IMPORTANT: Backup your database and .env**
   ```bash
   # Copy database to safe location
   cp cameronpad/data/cameronpad_dev.db ~/cameronpad_dev.db.backup
   
   # Copy .env file (contains your API keys)
   cp cameronpad/.env ~/.env.backup
   ```

### Step 2: Transfer Files with WinSCP

1. **Open WinSCP** and connect to your Linux server
   - Host name: `your-server-ip`
   - User name: `your-username`
   - Password: `your-password`
   - Port: `22` (default SSH port)

2. **Navigate to the correct directory**
   - **Local (left panel)**: Navigate to `D:\Repositories\CameronPAD\cameronpad`
   - **Remote (right panel)**: Navigate to `/home/your-username/cameronpad`

3. **Select files to transfer**
   
   **OPTION A: Transfer Everything (Safest)**
   - Select ALL files and folders in the local panel
   - Click "Upload" or drag to right panel
   - When prompted, choose **"Overwrite"** or **"Yes to All"**

   **OPTION B: Selective Transfer (Preserve Database)**
   - Select all EXCEPT:
     - `data/` folder (to preserve existing database)
     - `.env` file (if already configured on server)
     - `venv/` folder (Python virtual environment - should be recreated)
   - Upload selected files

4. **Transfer Progress**
   - WinSCP will show progress
   - This may take a few minutes depending on file size and connection speed

### Step 3: Post-Transfer Configuration (SSH into Linux)

After files are transferred, SSH back into your Linux server:

```bash
ssh user@your-server-ip
cd /home/your-username/cameronpad
```

#### 3.1: Restore or Configure .env

**If you transferred .env** (and it has correct keys):
```bash
# Verify it has content
cat .env
```

**If you didn't transfer .env** (restore from backup):
```bash
# Copy back from backup
cp ~/.env.backup .env

# Or create new one
nano .env
# Paste your API keys
```

Your `.env` should contain:
```env
FINNHUB_TOKEN=d34g7shr01qqt8soved0d34g7shr01qqt8sovedg
ALPHA_VANTAGE_KEY=I7TWLR7V5UPHL2AW
POLL_SECONDS=60
SHOWCASE_REFRESH=300
COOLDOWN_MIN=30
ALPHA_MIN_INTERVAL=13.0
```

#### 3.2: Restore Database (if needed)

**If you want to keep existing data**:
```bash
# Copy back the database from backup
cp ~/cameronpad_dev.db.backup data/cameronpad_dev.db

# Set proper permissions
chmod 644 data/cameronpad_dev.db
```

**If you want to start fresh**:
```bash
# Remove old database
rm -f data/cameronpad_dev.db

# Create admin user
python3 create_admin.py
```

#### 3.3: Set File Permissions

```bash
# Set ownership
sudo chown -R your-username:your-username /home/your-username/cameronpad

# Ensure data directory is writable
chmod 755 data/
chmod 644 data/*.db 2>/dev/null || true

# Make scripts executable
chmod +x setup.sh
```

#### 3.4: Recreate Virtual Environment

**IMPORTANT**: Don't transfer the `venv/` folder - always recreate it on Linux:

```bash
# Remove old venv if it exists
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

This ensures all packages are compiled for Linux (not Windows).

### Step 4: Test the Application

```bash
# Make sure venv is activated
source venv/bin/activate

# Test run
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

Watch the logs. You should see:
```
INFO:plugins.stocks.services:🔑 API Keys configured: Finnhub=Yes, AlphaVantage=Yes
```

**Test in browser**: `http://your-server-ip:8000`

Press `Ctrl+C` to stop the test server.

### Step 5: Restart Production Service

**If using systemd service**:

```bash
# Restart the service
sudo systemctl restart cameronpad

# Check status
sudo systemctl status cameronpad

# View logs
sudo journalctl -u cameronpad -f
```

**If running manually with Gunicorn**:

```bash
# Kill any existing processes
pkill -f "uvicorn app_new.main:app" || true
pkill -f "gunicorn app_new.main:app" || true

# Start with gunicorn
gunicorn app_new.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --daemon \
  --access-logfile /var/log/cameronpad/access.log \
  --error-logfile /var/log/cameronpad/error.log
```

## Quick Reference: Complete Update Process

```bash
# === ON LINUX SERVER ===

# 1. Stop service
sudo systemctl stop cameronpad

# 2. Backup database and config
cp data/cameronpad_dev.db ~/db_backup.db
cp .env ~/.env.backup

# 3. [Use WinSCP to transfer files from Windows]

# 4. Restore database and config (if needed)
cp ~/db_backup.db data/cameronpad_dev.db
cp ~/.env.backup .env

# 5. Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Set permissions
chmod 755 data/
chmod 644 data/*.db

# 7. Test
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C after verifying it works

# 8. Restart service
sudo systemctl start cameronpad
sudo systemctl status cameronpad
```

## Troubleshooting

### Issue: "API Keys configured: Finnhub=NO, AlphaVantage=NO"

**Solution**: .env file not transferred or not in correct location
```bash
# Check if .env exists
ls -la .env

# Check contents
cat .env

# If missing, restore from backup or recreate
cp ~/.env.backup .env
```

### Issue: "Module not found" errors

**Solution**: Dependencies not installed
```bash
# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database errors or empty database

**Solution**: Restore database from backup
```bash
# Check if database exists
ls -la data/

# Restore from backup
cp ~/db_backup.db data/cameronpad_dev.db
chmod 644 data/cameronpad_dev.db
```

### Issue: Permission denied errors

**Solution**: Fix file permissions
```bash
# Fix ownership
sudo chown -R your-username:your-username /home/your-username/cameronpad

# Fix directory permissions
chmod 755 data/
chmod 644 data/*.db
```

### Issue: Service won't start

**Check logs**:
```bash
# If using systemd
sudo journalctl -u cameronpad -n 50 --no-pager

# If running manually, run in foreground to see errors
source venv/bin/activate
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

### Issue: Old Python processes still running

**Solution**: Kill old processes
```bash
# Find Python processes
ps aux | grep python

# Kill specific process
kill -9 <process_id>

# Or kill all uvicorn/gunicorn
pkill -f uvicorn
pkill -f gunicorn
```

## What Gets Transferred vs. Recreated

### ✅ TRANSFER (via WinSCP):
- All `.py` files (application code)
- `requirements.txt`
- `templates/` folder (HTML templates)
- `static/` folder (CSS, JS, images)
- `plugins/` folder (all plugin code)
- `app_new/` folder (core application)
- `.env` file (if not already on server)
- Documentation (README.md, DEPLOYMENT.md, etc.)
- Configuration files (*.yaml)

### ❌ DON'T TRANSFER (or recreate):
- `venv/` - Virtual environment (recreate on Linux)
- `data/*.db` - Database (restore from backup or start fresh)
- `data/uploads/*` - User uploads (restore from backup)
- `__pycache__/` - Python cache (will be recreated)
- `*.pyc` files - Compiled Python (will be recreated)

### 🔄 BACKUP BEFORE OVERWRITING:
- `data/cameronpad_dev.db` - Your database with all data
- `.env` - Your API keys and configuration
- `data/uploads/` - Any uploaded files

## Best Practices

1. **Always backup before deploying**
   - Database
   - .env file
   - Uploaded files

2. **Test locally first**
   - Make sure everything works on Windows before deploying

3. **Use selective transfer if possible**
   - Don't overwrite database unless intentional
   - Keep existing .env if already configured

4. **Recreate venv on target system**
   - Never transfer virtual environment between OS
   - Always `pip install -r requirements.txt` on Linux

5. **Check logs after deployment**
   - Verify API keys loaded correctly
   - Ensure no import errors
   - Confirm service started successfully

6. **Keep backups**
   - Maintain multiple backup copies
   - Store backups outside the deployment directory
   - Consider automated daily backups

## Automation Script (Optional)

Create a deployment script on Linux to automate the process:

```bash
#!/bin/bash
# deploy.sh - Run this after WinSCP transfer

echo "🚀 Starting CameronPAD deployment..."

# Stop service
echo "⏸️  Stopping service..."
sudo systemctl stop cameronpad 2>/dev/null || true

# Recreate venv
echo "🐍 Recreating virtual environment..."
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 data/
chmod 644 data/*.db 2>/dev/null || true

# Test configuration
echo "🔍 Testing configuration..."
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Finnhub:', 'Yes' if os.getenv('FINNHUB_TOKEN') else 'NO')"

# Restart service
echo "▶️  Restarting service..."
sudo systemctl start cameronpad

# Show status
echo "📊 Service status:"
sudo systemctl status cameronpad --no-pager

echo "✅ Deployment complete!"
echo "📝 Check logs: sudo journalctl -u cameronpad -f"
```

Save as `deploy.sh`, make executable: `chmod +x deploy.sh`

After WinSCP transfer, just run: `./deploy.sh`
