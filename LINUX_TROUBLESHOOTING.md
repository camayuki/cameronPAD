# Linux Server Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "attempt to write a readonly database"

This happens when the database file has incorrect permissions or is owned by a different user.

**Solution:**
```bash
# Run the fix script
chmod +x fix_permissions.sh
./fix_permissions.sh
```

**Manual fix:**
```bash
# Fix database permissions
chmod 664 data/cameronpad.db
chown $(whoami):$(whoami) data/cameronpad.db

# Fix data directory
chmod 775 data/
chown $(whoami):$(whoami) data/

# Enable WAL mode for better concurrency
sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'
```

### Issue 2: "Internal Server Error" on Settings Page

**Fixed in latest version!** The settings page had a bug with database query results. 

**Solution:**
```bash
# Pull latest code
git pull origin branch.production.part2

# Restart server
./start.sh
```

### Issue 3: Port 8000 already in use

**Now automatically fixed!** The `start.sh` script automatically kills any process using port 8000.

**Manual solution:**
```bash
# Kill process on port 8000
sudo fuser -k 8000/tcp

# Or find and kill manually
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Issue 4: Permission denied on scripts

**Solution:**
```bash
chmod +x *.sh
```

### Issue 5: Database locked errors

This happens when multiple processes try to access the database.

**Solution:**
```bash
# Enable WAL mode (Write-Ahead Logging)
sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'

# Check for multiple uvicorn processes
ps aux | grep uvicorn

# Kill extra processes
sudo pkill -9 python
```

## Diagnostic Commands

### Check what's running
```bash
# Check if server is running
ps aux | grep uvicorn

# Check port usage
sudo lsof -i :8000

# Check which user is running the server
ps aux | grep uvicorn | awk '{print $1}'
```

### Check permissions
```bash
# Check database permissions
ls -lh data/cameronpad.db*

# Check data directory
ls -lhd data/

# Check logs
ls -lhd logs/
```

### Check logs
```bash
# View recent errors
grep -i "error\|exception" logs/*.log | tail -20

# Follow logs in real-time
tail -f logs/*.log

# Check systemd logs (if using systemd)
sudo journalctl -u cameronpad -f
```

### Test database
```bash
# Check if database is accessible
venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('data/cameronpad.db')
print('✅ Database is accessible')
conn.close()
"

# Check database tables
sqlite3 data/cameronpad.db ".tables"

# Check users table
sqlite3 data/cameronpad.db "SELECT * FROM users;"
```

## Full Diagnostic Script

Run the diagnostic script to check everything:
```bash
chmod +x debug_server.sh
./debug_server.sh
```

## Complete Restart Procedure

If everything is broken, here's how to start fresh:

```bash
# 1. Kill all Python processes
sudo pkill -9 python

# 2. Fix all permissions
./fix_permissions.sh

# 3. Enable WAL mode
sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'

# 4. Check virtual environment
source venv/bin/activate
pip list

# 5. Start server
./start.sh
```

## Server Access Issues

### Can't access from outside
```bash
# Check firewall
sudo ufw status

# Allow port 8000
sudo ufw allow 8000/tcp

# Check if server is listening on all interfaces
sudo lsof -i :8000 | grep LISTEN
```

### Getting timeout errors
```bash
# Check if server is running
ps aux | grep uvicorn

# Check server logs
tail -50 logs/*.log

# Check if port is accessible
curl localhost:8000
```

## Database Migration Issues

### Migrations not applying
```bash
# Check current migration version
sqlite3 data/cameronpad.db "SELECT * FROM schema_migrations;"

# Manually run migrations
venv/bin/python3 -c "
from app_new.core.database import get_database_manager
db = get_database_manager()
# Migrations run automatically on startup
print('✅ Migrations checked')
"
```

## Quick Fixes Cheat Sheet

```bash
# Fix permissions
./fix_permissions.sh

# Restart server
./start.sh

# Kill and restart
sudo pkill python; sleep 2; ./start.sh

# Check if running
ps aux | grep uvicorn

# View errors
tail -50 logs/*.log | grep -i error

# Test database
sqlite3 data/cameronpad.db ".tables"

# Fix port conflict
sudo fuser -k 8000/tcp
```

## Getting Help

If none of these work:

1. Run the diagnostic script: `./debug_server.sh`
2. Check the output for any ❌ errors
3. Review the suggested fixes
4. Check the logs: `tail -100 logs/*.log`

## Prevention

### Set up proper permissions from start
```bash
# After installation
./fix_permissions.sh

# Enable WAL mode
sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'

# Make scripts executable
chmod +x *.sh
```

### Use systemd for production
See `LINUX_DEPLOYMENT.md` for setting up as a system service with:
- Automatic restarts
- Proper user permissions
- Log rotation
- Firewall configuration
