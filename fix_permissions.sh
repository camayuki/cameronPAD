#!/bin/bash
# Auto-fix permissions and database issues for CameronPAD

echo "🔧 Fixing CameronPAD permissions and database issues..."
echo ""

# Get current user
CURRENT_USER=$(whoami)

# Fix data directory
echo "📁 Fixing data directory permissions..."
chmod 775 data/ 2>/dev/null
chown $CURRENT_USER:$CURRENT_USER data/ 2>/dev/null
echo "✅ Data directory fixed"

# Fix database file
if [ -f data/cameronpad.db ]; then
    echo "💾 Fixing database file permissions..."
    chmod 664 data/cameronpad.db
    chown $CURRENT_USER:$CURRENT_USER data/cameronpad.db
    echo "✅ Database file fixed"
    
    # Enable WAL mode
    echo "🔧 Enabling WAL mode for better concurrency..."
    sqlite3 data/cameronpad.db 'PRAGMA journal_mode=WAL;' 2>/dev/null
    
    # Fix WAL files if they exist
    if [ -f data/cameronpad.db-wal ]; then
        chmod 664 data/cameronpad.db-wal
        chown $CURRENT_USER:$CURRENT_USER data/cameronpad.db-wal
        echo "✅ WAL file fixed"
    fi
    
    if [ -f data/cameronpad.db-shm ]; then
        chmod 664 data/cameronpad.db-shm
        chown $CURRENT_USER:$CURRENT_USER data/cameronpad.db-shm
        echo "✅ SHM file fixed"
    fi
else
    echo "❌ Database file not found!"
fi

# Fix logs directory
if [ -d logs ]; then
    echo "📋 Fixing logs directory permissions..."
    chmod 775 logs/
    chown $CURRENT_USER:$CURRENT_USER logs/ 2>/dev/null
    echo "✅ Logs directory fixed"
fi

# Fix uploads directory
if [ -d data/uploads ]; then
    echo "📤 Fixing uploads directory permissions..."
    chmod 775 data/uploads/
    chown -R $CURRENT_USER:$CURRENT_USER data/uploads/ 2>/dev/null
    echo "✅ Uploads directory fixed"
fi

echo ""
echo "=================================="
echo "✅ All permissions fixed!"
echo ""
echo "📊 Current permissions:"
ls -lh data/cameronpad.db* 2>/dev/null
echo ""
echo "Now restart your server:"
echo "  ./start.sh"
echo "=================================="
