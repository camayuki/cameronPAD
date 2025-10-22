"""
Blog Database - Reddit-style posts and comments system
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def init_blog_db(db_path: str = "data/cameronpad_dev.db"):
    """Initialize blog plugin database tables"""
    logger.info(f"🗄️ Initializing Blog database tables at: {db_path}")
    
    # Ensure the data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        # Create blog_posts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                author_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                image_url TEXT,
                video_url TEXT,
                media_type TEXT,
                media_created_at DATETIME,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_pinned INTEGER DEFAULT 0,
                is_locked INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create blog_comments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                parent_id INTEGER,
                author_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                content TEXT NOT NULL,
                image_url TEXT,
                video_url TEXT,
                media_type TEXT,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (post_id) REFERENCES blog_posts (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES blog_comments (id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create post_votes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS post_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote_type INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, user_id),
                FOREIGN KEY (post_id) REFERENCES blog_posts (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create comment_votes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote_type INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES blog_comments (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blog_posts_created ON blog_posts(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blog_posts_author ON blog_posts(author_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_post ON blog_comments(post_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blog_comments_parent ON blog_comments(parent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_post_votes_post ON post_votes(post_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_comment_votes_comment ON comment_votes(comment_id)")
        
        # Migration: Add media_created_at column if it doesn't exist
        try:
            cur.execute("SELECT media_created_at FROM blog_posts LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Adding media_created_at column to blog_posts table")
            cur.execute("ALTER TABLE blog_posts ADD COLUMN media_created_at DATETIME")
        
        conn.commit()
        logger.info("✅ Blog database tables initialized")


def get_db_connection(db_path: str = "data/cameronpad_dev.db"):
    """Get a database connection"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

