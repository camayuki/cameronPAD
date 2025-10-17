"""
Database initialization for Notes plugin - Group Support Enabled
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


def init_notes_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize notes plugin database tables"""
    logger.info(f"🗄️ Initializing Notes database tables at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
        table_exists = cur.fetchone() is not None
        
        if not table_exists:
            # Create new table with group support
            cur.execute("""
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY,
                    content TEXT,
                    user_id INTEGER,
                    group_id INTEGER,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
                    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
                )
            """)
            logger.info("✅ Created notes table with group support")
        else:
            # Table exists, check if it has the new columns
            cur.execute("PRAGMA table_info(notes)")
            columns = {row[1] for row in cur.fetchall()}
            
            # Add missing columns if needed
            if 'user_id' not in columns:
                cur.execute("ALTER TABLE notes ADD COLUMN user_id INTEGER")
                logger.info("✅ Added user_id column")
            
            if 'group_id' not in columns:
                cur.execute("ALTER TABLE notes ADD COLUMN group_id INTEGER")
                logger.info("✅ Added group_id column")
            
            if 'updated_at' not in columns:
                cur.execute("ALTER TABLE notes ADD COLUMN updated_at DATETIME")
                logger.info("✅ Added updated_at column")
        
        # Create indexes for better performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_group ON notes(group_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_ts ON notes(ts)
        """)
        
        conn.commit()
        logger.info("✅ Notes database tables initialized")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_notes_db()
