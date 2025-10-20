# Quick Fix Guide for Linux Server Errors

## Errors You're Seeing:
1. ❌ "attempt to write a readonly database" (Theme Marketplace)
2. ❌ "Internal Server Error" (Settings Page) - **FIXED in code**

## Files to Transfer to Linux Server:

### 1. Updated Code Files (Fixed):
- `app_new/main.py` - Fixed settings page error
- `fix_permissions.sh` - Fixes database permissions
- `debug_server.sh` - Diagnoses issues

### 2. Run These Commands on Linux Server:

```bash
# Step 1: Make scripts executable
chmod +x fix_permissions.sh debug_server.sh start.sh

# Step 2: Fix database permissions
./fix_permissions.sh

# Step 3: Restart server  
./start.sh
```

## What Each Script Does:

### fix_permissions.sh
- Fixes database file permissions (makes it writable)
- Fixes data directory permissions
- Enables WAL mode for better performance
- Fixes log directory permissions

### debug_server.sh
- Shows database permissions
- Shows who owns the files
- Checks if database is locked
- Shows recent errors
- Suggests fixes

## Expected Output After Running fix_permissions.sh:

```
🔧 Fixing CameronPAD permissions and database issues...

📁 Fixing data directory permissions...
✅ Data directory fixed
💾 Fixing database file permissions...
✅ Database file fixed
🔧 Enabling WAL mode for better concurrency...
✅ WAL file fixed
✅ SHM file fixed
📋 Fixing logs directory permissions...
✅ Logs directory fixed

==================================
✅ All permissions fixed!

📊 Current permissions:
-rw-rw-r-- 1 youruser youruser 1.2M Oct 17 12:00 data/cameronpad.db
-rw-rw-r-- 1 youruser youruser  32K Oct 17 12:00 data/cameronpad.db-shm
-rw-rw-r-- 1 youruser youruser 512K Oct 17 12:00 data/cameronpad.db-wal

Now restart your server:
  ./start.sh
==================================
```

## After Restarting:

Both issues should be fixed:
- ✅ Theme Marketplace will load properly
- ✅ Settings page will work (code was updated)

## If You Still Have Errors:

Run the diagnostic:
```bash
./debug_server.sh
```

And send me the output!

## Quick Command Sequence:

```bash
# All in one go:
chmod +x *.sh && ./fix_permissions.sh && ./start.sh
```

That's it! 🚀
