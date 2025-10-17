"""
Database initialization for Notes plugin
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


def init_notes_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize notes plugin database tables"""
    logger.info("🗄️ Initializing Notes database tables...")
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Timestamped notes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                content TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("✅ Notes database tables initialized")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_notes_db()
