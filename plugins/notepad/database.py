"""
Database initialization for Notepad plugin
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


def init_notepad_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize notepad plugin database tables"""
    logger.info("🗄️ Initializing Notepad database tables...")
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Multi-tab notepad
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pad_tabs (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                content TEXT DEFAULT '',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default "General" tab if no tabs exist
        count = cur.execute("SELECT COUNT(*) FROM pad_tabs").fetchone()[0]
        if count == 0:
            cur.execute(
                "INSERT INTO pad_tabs(name, content) VALUES(?, ?)",
                ("General", "")
            )
        
        conn.commit()
        logger.info("✅ Notepad database tables initialized")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_notepad_db()
