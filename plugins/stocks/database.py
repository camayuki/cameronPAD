"""
Database initialization for Stocks plugin
"""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def init_stocks_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize stocks plugin database tables"""
    logger.info("🗄️ Initializing Stocks database tables...")
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Stock tracking table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                target REAL NOT NULL,
                direction TEXT CHECK(direction IN ('above','below')) NOT NULL,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        # Alert history
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                price REAL,
                target REAL,
                direction TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Latest price cache
        cur.execute("""
            CREATE TABLE IF NOT EXISTS latest_prices (
                symbol TEXT PRIMARY KEY,
                price REAL,
                high REAL,
                low REAL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure high/low columns exist (migration)
        cols = {r[1] for r in cur.execute("PRAGMA table_info(latest_prices)")}
        if "high" not in cols:
            cur.execute("ALTER TABLE latest_prices ADD COLUMN high REAL")
        if "low" not in cols:
            cur.execute("ALTER TABLE latest_prices ADD COLUMN low REAL")
        
        # Price predictions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                symbol TEXT PRIMARY KEY,
                pred_next REAL,
                src_days INTEGER,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("✅ Stocks database tables initialized")


if __name__ == "__main__":
    # Run standalone for testing
    logging.basicConfig(level=logging.INFO)
    init_stocks_db()
