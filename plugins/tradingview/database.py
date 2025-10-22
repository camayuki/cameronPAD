"""
Database utilities for TradingView plugin
"""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("data/cameronpad_dev.db")


def init_db():
    """Initialize TradingView database tables"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create charts table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tradingview_charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_number INTEGER NOT NULL UNIQUE,
            timeframe TEXT DEFAULT 'D',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chart notes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tradingview_chart_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_number INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chart_number) REFERENCES tradingview_charts(chart_number) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ TradingView database tables initialized")


def get_all_charts():
    """Get all saved charts"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.chart_number, c.timeframe, c.created_at, 
               COALESCE(n.notes, '') as notes
        FROM tradingview_charts c
        LEFT JOIN tradingview_chart_notes n ON c.chart_number = n.chart_number
        ORDER BY c.chart_number
    """)
    
    charts = [dict(row) for row in cur.fetchall()]
    conn.close()
    return charts


def add_chart(chart_number: int, timeframe: str = 'D'):
    """Add a new chart"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO tradingview_charts (chart_number, timeframe) VALUES (?, ?)",
            (chart_number, timeframe)
        )
        # Initialize empty notes
        cur.execute(
            "INSERT INTO tradingview_chart_notes (chart_number, notes) VALUES (?, ?)",
            (chart_number, '')
        )
        conn.commit()
        logger.info(f"✅ Added chart #{chart_number}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Chart #{chart_number} already exists")
        return False
    finally:
        conn.close()


def delete_chart(chart_number: int):
    """Delete a chart and its notes"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Delete notes first (will be handled by CASCADE, but explicit is better)
    cur.execute("DELETE FROM tradingview_chart_notes WHERE chart_number = ?", (chart_number,))
    cur.execute("DELETE FROM tradingview_charts WHERE chart_number = ?", (chart_number,))
    
    conn.commit()
    conn.close()
    logger.info(f"🗑️ Deleted chart #{chart_number}")


def save_chart_notes(chart_number: int, notes: str):
    """Save or update notes for a chart"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if notes exist
    cur.execute("SELECT id FROM tradingview_chart_notes WHERE chart_number = ?", (chart_number,))
    exists = cur.fetchone()
    
    if exists:
        cur.execute(
            "UPDATE tradingview_chart_notes SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE chart_number = ?",
            (notes, chart_number)
        )
    else:
        cur.execute(
            "INSERT INTO tradingview_chart_notes (chart_number, notes) VALUES (?, ?)",
            (chart_number, notes)
        )
    
    conn.commit()
    conn.close()
    logger.info(f"💾 Saved notes for chart #{chart_number}")


def get_chart_notes(chart_number: int):
    """Get notes for a specific chart"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT notes FROM tradingview_chart_notes WHERE chart_number = ?", (chart_number,))
    result = cur.fetchone()
    conn.close()
    
    return result[0] if result else ""
