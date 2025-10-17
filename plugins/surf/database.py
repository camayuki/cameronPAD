"""
Database initialization for Surf plugin
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


def init_surf_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize surf plugin database tables"""
    logger.info("🗄️ Initializing Surf database tables...")
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Surf spots
        cur.execute("""
            CREATE TABLE IF NOT EXISTS surf_spots (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                provider TEXT DEFAULT 'open-meteo'
            )
        """)
        
        # Surf data cache
        cur.execute("""
            CREATE TABLE IF NOT EXISTS surf_cache (
                spot_id INTEGER PRIMARY KEY,
                height_m REAL,
                period_s REAL,
                direction_deg REAL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(spot_id) REFERENCES surf_spots(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        logger.info("✅ Surf database tables initialized")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_surf_db()
