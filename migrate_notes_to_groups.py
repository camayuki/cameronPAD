"""
Migration script to add group support to existing notes
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_notes_to_groups(db_path: str = "data/cameronpad_dev.db"):
    """Add user_id and group_id columns to notes table"""
    logger.info("📦 Migrating notes table to support groups...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            
            # Check if columns already exist
            cur.execute("PRAGMA table_info(notes)")
            columns = [row[1] for row in cur.fetchall()]
            
            # Add user_id column if it doesn't exist
            if 'user_id' not in columns:
                logger.info("➕ Adding user_id column to notes table...")
                cur.execute("""
                    ALTER TABLE notes ADD COLUMN user_id INTEGER
                """)
                logger.info("✅ Added user_id column")
            else:
                logger.info("ℹ️ user_id column already exists")
            
            # Add group_id column if it doesn't exist
            if 'group_id' not in columns:
                logger.info("➕ Adding group_id column to notes table...")
                cur.execute("""
                    ALTER TABLE notes ADD COLUMN group_id INTEGER
                """)
                logger.info("✅ Added group_id column")
            else:
                logger.info("ℹ️ group_id column already exists")
            
            # Add updated_at column if it doesn't exist
            if 'updated_at' not in columns:
                logger.info("➕ Adding updated_at column to notes table...")
                cur.execute("""
                    ALTER TABLE notes ADD COLUMN updated_at DATETIME
                """)
                # Set default value for existing rows
                cur.execute("""
                    UPDATE notes SET updated_at = ts WHERE updated_at IS NULL
                """)
                logger.info("✅ Added updated_at column")
            else:
                logger.info("ℹ️ updated_at column already exists")
            
            # Create indexes if they don't exist
            logger.info("📊 Creating indexes...")
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
            
            # Get the "Everyone" group ID
            cur.execute("SELECT id FROM groups WHERE name = 'Everyone'")
            everyone_group = cur.fetchone()
            
            if everyone_group:
                everyone_group_id = everyone_group[0]
                
                # Migrate existing notes to "Everyone" group
                cur.execute("""
                    UPDATE notes 
                    SET group_id = ?
                    WHERE group_id IS NULL
                """, (everyone_group_id,))
                
                migrated_count = cur.rowcount
                conn.commit()
                
                logger.info(f"✅ Migrated {migrated_count} existing notes to 'Everyone' group")
            else:
                logger.warning("⚠️ 'Everyone' group not found. Existing notes will have NULL group_id.")
            
            logger.info("✅ Notes table migration completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Error migrating notes table: {e}")
        raise

if __name__ == "__main__":
    migrate_notes_to_groups()
