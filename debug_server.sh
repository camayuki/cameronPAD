#!/bin/bash
# Debug script for CameronPAD on Linux server

echo "🔍 CameronPAD Server Diagnostics"
echo "=================================="
echo ""

# Check database permissions
echo "📁 Database file permissions:"
ls -lh data/cameronpad.db 2>/dev/null || echo "❌ Database file not found!"
echo ""

echo "📁 Data directory permissions:"
ls -lhd data/
echo ""

# Check database owner
echo "👤 Database owner:"
stat -c '%U:%G' data/cameronpad.db 2>/dev/null || echo "❌ Cannot read database file owner"
echo ""

# Check if database is writable
echo "✍️ Database write test:"
if [ -w data/cameronpad.db ]; then
    echo "✅ Database is writable"
else
    echo "❌ Database is NOT writable!"
fi
echo ""

# Check process user
echo "👤 Current user running this script:"
whoami
echo ""

# Check what user is running the app
echo "👤 User running uvicorn (if any):"
ps aux | grep uvicorn | grep -v grep || echo "No uvicorn process found"
echo ""

# Check recent errors in system log
echo "📋 Recent application errors (last 50 lines):"
if [ -f logs/app.log ]; then
    tail -50 logs/app.log | grep -i "error\|exception\|traceback" || echo "No errors found in logs"
else
    echo "❌ No log file found at logs/app.log"
fi
echo ""

# Check Python version
echo "🐍 Python version:"
python3 --version
echo ""

# Check virtual environment
echo "🔧 Virtual environment:"
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    echo "Python in venv: $(venv/bin/python3 --version)"
else
    echo "❌ Virtual environment not found!"
fi
echo ""

# Check SQLite version
echo "💾 SQLite version:"
venv/bin/python3 -c "import sqlite3; print(sqlite3.sqlite_version)" 2>/dev/null || echo "❌ Cannot check SQLite version"
echo ""

# Check if database is locked
echo "🔒 Check if database is locked:"
venv/bin/python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('data/cameronpad.db', timeout=1)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.close()
    print('✅ Database is accessible and not locked')
except Exception as e:
    print(f'❌ Database error: {e}')
" 2>&1
echo ""

# Fix permissions if needed
echo "🔧 Suggested fixes:"
echo "1. Fix database permissions:"
echo "   chmod 664 data/cameronpad.db"
echo "   chown \$(whoami):\$(whoami) data/cameronpad.db"
echo ""
echo "2. Fix data directory permissions:"
echo "   chmod 775 data/"
echo "   chown \$(whoami):\$(whoami) data/"
echo ""
echo "3. Enable WAL mode for better concurrency:"
echo "   sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;'"
echo ""

echo "=================================="
echo "Would you like to auto-fix permissions? (y/n)"
