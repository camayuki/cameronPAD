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
                user_id INTEGER,
                group_id INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        """)
        
        # Add columns if they don't exist (for existing databases)
        try:
            cur.execute("ALTER TABLE pad_tabs ADD COLUMN user_id INTEGER")
            logger.info("Added user_id column to pad_tabs")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cur.execute("ALTER TABLE pad_tabs ADD COLUMN group_id INTEGER")
            logger.info("Added group_id column to pad_tabs")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
