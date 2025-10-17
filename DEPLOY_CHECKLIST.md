# 🚀 Quick Deploy Checklist (WinSCP Method)

## Before Transfer (Windows)

- [ ] Test application locally works
- [ ] Verify `.env` has real API keys (not placeholders)
- [ ] Check stock service updates prices successfully
- [ ] Optional: Create backup zip of project

## On Linux Server (Before Transfer)

- [ ] SSH into server: `ssh user@server-ip`
- [ ] Stop running service: `sudo systemctl stop cameronpad`
- [ ] Backup database: `cp data/cameronpad_dev.db ~/db_backup.db`
- [ ] Backup .env: `cp .env ~/.env.backup`
- [ ] Optional: Backup entire directory: `tar -czf ~/cameronpad_backup.tar.gz cameronpad/`

## Transfer with WinSCP

- [ ] Connect to server (Host, Username, Password, Port 22)
- [ ] Navigate to `/home/your-username/cameronpad` (right panel)
- [ ] Navigate to `D:\Repositories\CameronPAD\cameronpad` (left panel)
- [ ] Select all files (or all except `data/` and `venv/`)
- [ ] Upload files (Overwrite when prompted)
- [ ] Wait for transfer to complete

## After Transfer (Linux Server)

### 1. Configuration
- [ ] SSH into server: `ssh user@server-ip`
- [ ] Navigate: `cd cameronpad`
- [ ] Check .env exists: `cat .env`
- [ ] If missing: `cp ~/.env.backup .env`
- [ ] Restore database: `cp ~/db_backup.db data/cameronpad_dev.db`

### 2. Virtual Environment
- [ ] Remove old venv: `rm -rf venv`
- [ ] Create new venv: `python3 -m venv venv`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Upgrade pip: `pip install --upgrade pip`
- [ ] Install dependencies: `pip install -r requirements.txt`

### 3. Permissions
- [ ] Set ownership: `sudo chown -R username:username /home/username/cameronpad`
- [ ] Data directory: `chmod 755 data/`
- [ ] Database files: `chmod 644 data/*.db`

### 4. Testing
- [ ] Test run: `python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000`
- [ ] Check logs show: `🔑 API Keys configured: Finnhub=Yes, AlphaVantage=Yes`
- [ ] Test in browser: `http://server-ip:8000`
- [ ] Stop test: Press `Ctrl+C`

### 5. Start Service
- [ ] Start service: `sudo systemctl start cameronpad`
- [ ] Check status: `sudo systemctl status cameronpad`
- [ ] View logs: `sudo journalctl -u cameronpad -f`
- [ ] Test in browser again

## Verification

- [ ] Website loads at `http://server-ip:8000`
- [ ] Can login with credentials
- [ ] Stock service starts successfully
- [ ] Stock prices update (not showing "--")
- [ ] All plugins load correctly
- [ ] No errors in logs

## Quick Copy-Paste Commands

```bash
# === BACKUP ===
sudo systemctl stop cameronpad
cp data/cameronpad_dev.db ~/db_backup.db
cp .env ~/.env.backup

# === [TRANSFER FILES WITH WINSCP] ===

# === AFTER TRANSFER ===
cd cameronpad
cp ~/.env.backup .env
cp ~/db_backup.db data/cameronpad_dev.db
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
chmod 755 data/
chmod 644 data/*.db

# === TEST ===
python -m uvicorn app_new.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C after verifying

# === RESTART ===
sudo systemctl start cameronpad
sudo systemctl status cameronpad
```

## Troubleshooting

### API Keys Not Loading
```bash
cat .env                    # Check file exists
cp ~/.env.backup .env      # Restore from backup
```

### Module Not Found
```bash
source venv/bin/activate   # Activate venv
pip install -r requirements.txt  # Reinstall
```

### Database Issues
```bash
cp ~/db_backup.db data/cameronpad_dev.db
chmod 644 data/cameronpad_dev.db
```

### Permission Errors
```bash
sudo chown -R username:username /home/username/cameronpad
chmod 755 data/
```

### Service Won't Start
```bash
sudo journalctl -u cameronpad -n 50 --no-pager  # Check logs
pkill -f uvicorn                                 # Kill old processes
```

---

**Need detailed instructions?** See `DEPLOY_WITH_WINSCP.md`
