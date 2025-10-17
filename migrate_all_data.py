"""
Migrate all data from app.db to cameronpad_dev.db
Includes: notes, notepad tabs, surf spots, stocks, etc.
"""
import sqlite3

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def migrate_pad_tabs():
    """Migrate notepad tabs"""
    source_conn = sqlite3.connect('data/app.db')
    source_cur = source_conn.cursor()
    
    target_conn = sqlite3.connect('data/cameronpad_dev.db')
    target_cur = target_conn.cursor()
    
    if not check_table_exists(source_cur, 'pad_tabs'):
        print("⚠️  pad_tabs table not found in source database")
        source_conn.close()
        target_conn.close()
        return
    
    print("\n=== MIGRATING NOTEPAD TABS ===")
    source_cur.execute("SELECT id, name, content, updated_at FROM pad_tabs ORDER BY id")
    tabs = source_cur.fetchall()
    
    print(f"Found {len(tabs)} tab(s) in source database")
    
    if not tabs:
        source_conn.close()
        target_conn.close()
        return
    
    # Clear existing tabs in target (except default "General" tab)
    target_cur.execute("DELETE FROM pad_tabs")
    
    migrated = 0
    for tab in tabs:
        tab_id, name, content, updated_at = tab
        print(f"  - Migrating tab: {name} ({len(content) if content else 0} chars)")
        try:
            target_cur.execute(
                "INSERT INTO pad_tabs(name, content, updated_at) VALUES(?, ?, ?)",
                (name, content or '', updated_at)
            )
            migrated += 1
        except Exception as e:
            print(f"    Error: {e}")
    
    target_conn.commit()
    print(f"✅ Migrated {migrated}/{len(tabs)} tabs")
    
    source_conn.close()
    target_conn.close()

def migrate_surf_spots():
    """Migrate surf spots"""
    source_conn = sqlite3.connect('data/app.db')
    source_cur = source_conn.cursor()
    
    target_conn = sqlite3.connect('data/cameronpad_dev.db')
    target_cur = target_conn.cursor()
    
    if not check_table_exists(source_cur, 'surf_spots'):
        print("⚠️  surf_spots table not found in source database")
        source_conn.close()
        target_conn.close()
        return
    
    print("\n=== MIGRATING SURF SPOTS ===")
    source_cur.execute("SELECT id, name, lat, lon, provider FROM surf_spots ORDER BY id")
    spots = source_cur.fetchall()
    
    print(f"Found {len(spots)} surf spot(s) in source database")
    
    if not spots:
        source_conn.close()
        target_conn.close()
        return
    
    migrated = 0
    for spot in spots:
        spot_id, name, lat, lon, provider = spot
        print(f"  - Migrating spot: {name} ({lat}, {lon})")
        try:
            target_cur.execute(
                "INSERT INTO surf_spots(name, lat, lon, provider) VALUES(?, ?, ?, ?)",
                (name, lat, lon, provider or 'open-meteo')
            )
            migrated += 1
        except Exception as e:
            print(f"    Error: {e}")
    
    target_conn.commit()
    print(f"✅ Migrated {migrated}/{len(spots)} surf spots")
    
    source_conn.close()
    target_conn.close()

def migrate_stocks():
    """Migrate stock alerts"""
    source_conn = sqlite3.connect('data/app.db')
    source_cur = source_conn.cursor()
    
    target_conn = sqlite3.connect('data/cameronpad_dev.db')
    target_cur = target_conn.cursor()
    
    if not check_table_exists(source_cur, 'stocks'):
        print("⚠️  stocks table not found in source database")
        source_conn.close()
        target_conn.close()
        return
    
    print("\n=== MIGRATING STOCKS ===")
    source_cur.execute("SELECT id, symbol, target, direction, enabled FROM stocks ORDER BY id")
    stocks = source_cur.fetchall()
    
    print(f"Found {len(stocks)} stock(s) in source database")
    
    if not stocks:
        source_conn.close()
        target_conn.close()
        return
    
    migrated = 0
    for stock in stocks:
        stock_id, symbol, target, direction, enabled = stock
        print(f"  - Migrating stock: {symbol} (target: ${target} {direction})")
        try:
            target_cur.execute(
                "INSERT INTO stocks(symbol, target, direction, enabled) VALUES(?, ?, ?, ?)",
                (symbol, target, direction, enabled)
            )
            migrated += 1
        except Exception as e:
            print(f"    Error: {e}")
    
    target_conn.commit()
    print(f"✅ Migrated {migrated}/{len(stocks)} stocks")
    
    source_conn.close()
    target_conn.close()

def show_summary():
    """Show summary of migrated data"""
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    
    conn = sqlite3.connect('data/cameronpad_dev.db')
    cur = conn.cursor()
    
    tables = [
        ('notes', 'Notes'),
        ('pad_tabs', 'Notepad Tabs'),
        ('surf_spots', 'Surf Spots'),
        ('stocks', 'Stocks'),
        ('alerts', 'Stock Alerts'),
        ('latest_prices', 'Latest Prices'),
        ('predictions', 'Predictions'),
    ]
    
    for table_name, display_name in tables:
        if check_table_exists(cur, table_name):
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"{display_name:20} : {count} records")
    
    conn.close()
    print("="*50)

if __name__ == "__main__":
    print("🔄 Starting data migration from app.db to cameronpad_dev.db")
    print("="*50)
    
    migrate_pad_tabs()
    migrate_surf_spots()
    migrate_stocks()
    
    show_summary()
    
    print("\n✅ Migration complete!")
