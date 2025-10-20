# URGENT: Fix "readonly database" Error

## Quick Fix (Run this on your Linux server)

```bash
# Transfer these files to your Linux server first:
# - fix_permissions.sh
# - app_new/main.py (updated)
# - app_new/core/themes.py (will update)

# Then run:
chmod +x fix_permissions.sh
./fix_permissions.sh

# Restart the server
./start.sh
```

## What's Causing the Error

The theme manager tries to insert built-in themes into the database every time it loads. On your Linux server, the database file (`data/cameronpad.db`) has readonly permissions, causing the "attempt to write a readonly database" error.

## Solution 1: Fix Permissions (RECOMMENDED)

Run the `fix_permissions.sh` script I created:

```bash
#!/bin/bash
chmod 664 data/cameronpad.db
chown $(whoami):$(whoami) data/cameronpad.db
chmod 775 data/
sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'
```

## Solution 2: Check Current Permissions

```bash
# Check database permissions
ls -lh data/cameronpad.db

# Should show something like:
# -rw-rw-r-- 1 youruser youruser 1.2M Oct 17 12:00 data/cameronpad.db
#  ^^^ these need to be rw-

# If it shows:
# -r--r--r-- (readonly)
# Then run: chmod 664 data/cameronpad.db
```

## Solution 3: Check Who Owns the Database

```bash
# Check owner
stat -c '%U:%G' data/cameronpad.db

# If it's owned by root or another user:
sudo chown $(whoami):$(whoami) data/cameronpad.db
sudo chown $(whoami):$(whoami) data/
```

## After Fixing

1. Restart the server:
```bash
./start.sh
```

2. Try accessing the marketplace again

3. Check the settings page

Both should work now!

## If Still Having Issues

Run the full diagnostic:
```bash
chmod +x debug_server.sh
./debug_server.sh
```

This will show you exactly what's wrong.
