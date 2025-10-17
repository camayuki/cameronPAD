# WinSCP Transfer Instructions

## Quick Setup

### Method 1: Using WinSCP GUI (Recommended for beginners)

1. **Download and Install WinSCP**
   - Download from: https://winscp.net/eng/download.php
   - Install with default settings

2. **Connect to Your Server**
   - Open WinSCP
   - Click "New Site"
   - Fill in:
     - **File protocol**: SFTP
     - **Host name**: your-server-ip (e.g., 192.168.1.100)
     - **Port number**: 22
     - **User name**: your-linux-username
     - **Password**: your-linux-password
   - Click "Save" (optional, to save connection)
   - Click "Login"

3. **Navigate to Directories**
   - **Left panel (Local/Windows)**: 
     - Navigate to: `D:\Repositories\CameronPAD\cameronpad`
   - **Right panel (Remote/Linux)**:
     - Navigate to: `/home/your-username/cameronpad`

4. **Select Files to Transfer**
   
   **Option A: Transfer Everything (Easiest)**
   - In left panel, press `Ctrl+A` to select all
   - Click "Upload" button (or drag to right panel)
   - When prompted, select "Overwrite"
   
   **Option B: Selective Transfer (Recommended)**
   - Select all files and folders EXCEPT:
     - `venv/` folder (will be recreated on Linux)
     - `__pycache__/` folders (will be recreated)
     - `.git/` folder (if present, not needed on server)
   - To select multiple: Hold `Ctrl` and click each item
   - Click "Upload"

5. **Wait for Transfer**
   - Progress will be shown in the bottom panel
   - Wait for "Transfer done" message

6. **After Transfer Complete**
   - Close WinSCP or keep it open for next deployment
   - Open your SSH client (PuTTY, Windows Terminal, etc.)
   - Run the post-deployment script (see below)

### Method 2: Using WinSCP Script (Advanced)

Create a script file `deploy.txt`:

```
# WinSCP Script
option batch abort
option confirm off

# Connect
open sftp://username:password@server-ip/

# Navigate to target directory
cd /home/username/cameronpad

# Transfer files (excluding venv and cache)
put * -filemask="|venv/;__pycache__/;*.pyc;.git/"

# Close connection
close

# Exit
exit
```

Run from Command Prompt:
```batch
"C:\Program Files (x86)\WinSCP\WinSCP.com" /script=deploy.txt
```

### Method 3: Using SCP from PowerShell (Windows 10+)

```powershell
# Transfer entire directory
scp -r D:\Repositories\CameronPAD\cameronpad username@server-ip:/home/username/

# Or transfer excluding specific folders
# (Requires zip utility)
$exclude = @('venv', '__pycache__', '.git')
Get-ChildItem -Exclude $exclude | ForEach-Object {
    scp -r $_.FullName username@server-ip:/home/username/cameronpad/
}
```

## After Transfer: Run on Linux Server

```bash
# SSH into your server
ssh username@server-ip

# Navigate to project directory
cd cameronpad

# Run automated deployment script
chmod +x deploy_after_winscp.sh
./deploy_after_winscp.sh
```

The script will:
1. ✅ Stop existing service
2. ✅ Backup database and .env
3. ✅ Recreate virtual environment
4. ✅ Install all dependencies
5. ✅ Set proper permissions
6. ✅ Start the service

## Files to Transfer vs Skip

### ✅ TRANSFER (Essential):
- `app_new/` - Core application
- `plugins/` - All plugins
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `requirements.txt` - Dependencies
- `.env` - Configuration (if not already on server)
- `*.md` - Documentation
- `*.sh` - Shell scripts
- `*.py` - Python scripts
- `data/*.db` - Database (optional, can restore from backup)

### ⏭️ SKIP (Auto-generated or OS-specific):
- `venv/` - Virtual environment (will be recreated)
- `__pycache__/` - Python cache (will be recreated)
- `*.pyc` - Compiled Python files
- `.git/` - Git repository (not needed on server)
- `*.log` - Log files (if any)

### 🔄 BACKUP FIRST (Before overwriting):
- `data/cameronpad_dev.db` - Your database
- `.env` - Your configuration
- `data/uploads/` - User uploaded files

## Troubleshooting

### Connection Failed
- Check server IP address is correct
- Verify port 22 is open (firewall)
- Confirm SSH service is running on Linux: `sudo systemctl status sshd`
- Try connecting with SSH first: `ssh username@server-ip`

### Authentication Failed
- Double-check username and password
- Try SSH authentication test: `ssh username@server-ip`
- Check if SSH key authentication is required

### Permission Denied During Transfer
- Ensure target directory exists: `mkdir -p /home/username/cameronpad`
- Check directory permissions: `ls -la /home/username/`
- Ensure you own the directory: `sudo chown username:username /home/username/cameronpad`

### Transfer Stuck or Slow
- Check network connection
- Try transferring in smaller batches
- Compress before transfer: Create a zip on Windows, transfer zip, extract on Linux

### Files Not Showing After Transfer
- Refresh WinSCP view (F5)
- Check correct directory on Linux side
- List files via SSH: `ls -la /home/username/cameronpad/`

## Quick Reference Commands

### On Windows (PowerShell)
```powershell
# Run pre-deployment check
.\pre_deploy_check.ps1

# Create backup before deploying
Compress-Archive -Path D:\Repositories\CameronPAD\cameronpad -DestinationPath cameronpad_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip
```

### On Linux (after transfer)
```bash
# Quick deploy
cd cameronpad && chmod +x deploy_after_winscp.sh && ./deploy_after_winscp.sh

# Manual steps if script fails
cd cameronpad
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cameronpad
```

## Keeping WinSCP Session for Quick Updates

**Save your session** in WinSCP:
1. After entering connection details, click "Save"
2. Give it a name: "CameronPAD Production"
3. Next time: Double-click saved session to connect instantly

**For quick updates** (after initial deployment):
1. Open saved WinSCP session
2. Select only changed files (e.g., modified plugins)
3. Upload selected files
4. SSH and restart service: `sudo systemctl restart cameronpad`

## Alternative: Using rsync (More efficient for updates)

If rsync is available:

```bash
# From Windows (using WSL or Git Bash)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
  /d/Repositories/CameronPAD/cameronpad/ \
  username@server-ip:/home/username/cameronpad/
```

## Need Help?

- **Detailed guide**: See `DEPLOY_WITH_WINSCP.md`
- **Quick checklist**: See `DEPLOY_CHECKLIST.md`
- **Full deployment**: See `DEPLOYMENT.md`
