# Plugin Data Migration Guide

## Overview
This document outlines the database schema and data migration needed to integrate the original app functionality into the new plugin system.

## Database Schema

### Stocks Plugin Tables

```sql
-- Stock tracking (alerts)
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    target REAL NOT NULL,
    direction TEXT CHECK(direction IN ('above','below')) NOT NULL,
    enabled INTEGER DEFAULT 1
);

-- Alert history
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    price REAL,
    target REAL,
    direction TEXT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Latest price cache
CREATE TABLE IF NOT EXISTS latest_prices (
    symbol TEXT PRIMARY KEY,
    price REAL,
    high REAL,
    low REAL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Price predictions
CREATE TABLE IF NOT EXISTS predictions (
    symbol TEXT PRIMARY KEY,
    pred_next REAL,
    src_days INTEGER,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Notes Plugin Tables

```sql
-- Timestamped notes
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    content TEXT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Notepad Plugin Tables

```sql
-- Multi-tab notepad
CREATE TABLE IF NOT EXISTS pad_tabs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    content TEXT DEFAULT '',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Surf Plugin Tables

```sql
-- Surf spots
CREATE TABLE IF NOT EXISTS surf_spots (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    provider TEXT DEFAULT 'open-meteo'
);

-- Surf data cache
CREATE TABLE IF NOT EXISTS surf_cache (
    spot_id INTEGER PRIMARY KEY,
    height_m REAL,
    period_s REAL,
    direction_deg REAL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(spot_id) REFERENCES surf_spots(id) ON DELETE CASCADE
);
```

### Journal Plugin Tables

```sql
-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,        -- YYYY-MM-DD
    title TEXT,
    time TEXT,                 -- HH:MM
    location TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Journal images
CREATE TABLE IF NOT EXISTS journal_images (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    filename TEXT NOT NULL,    -- stored filename
    orig_name TEXT,
    size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
);
```

### TradingView Plugin Tables

```sql
-- TradingView symbol configuration
CREATE TABLE IF NOT EXISTS tv_symbols (
    tv_symbol TEXT PRIMARY KEY,   -- e.g. NASDAQ:AAPL
    label TEXT                    -- display label
);
```

## Migration Steps

### 1. Run Database Migrations
Each plugin will create its own tables on first initialization.

### 2. Data Migration from Old App
If migrating from `data/app.db` to `data/cameronpad_dev.db`:

```python
# Migration script (run once)
import sqlite3

old_db = sqlite3.connect('data/app.db')
new_db = sqlite3.connect('data/cameronpad_dev.db')

# Copy each table
for table in ['stocks', 'alerts', 'latest_prices', 'predictions', 'notes', 
              'pad_tabs', 'surf_spots', 'surf_cache', 'journal_entries', 
              'journal_images', 'tv_symbols']:
    try:
        rows = old_db.execute(f"SELECT * FROM {table}").fetchall()
        # Insert into new_db with appropriate plugin schema
    except sqlite3.OperationalError:
        print(f"Table {table} not found in old database")
```

### 3. API Keys Configuration
Add to `.env`:
```
FINNHUB_TOKEN=your_token_here
ALPHA_VANTAGE_KEY=your_key_here
TWILIO_SID=your_sid
TWILIO_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_token
DISCORD_WEBHOOK_URL=your_webhook
```

### 4. Enable Background Tasks
- Stock alert polling (60s)
- Showcase update (300s)  
- Prediction update (3600s)
- Surf data update (600s)

## Implementation Priority

1. ✅ Database schemas created
2. ✅ Models defined
3. 🔄 Services implementation (API integration)
4. 🔄 Background polling tasks
5. ⏳ UI integration with live data
6. ⏳ Notification system
