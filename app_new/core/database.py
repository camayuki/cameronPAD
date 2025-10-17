"""
Database setup, connection management, and migrations - With Groups Support
"""
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and migration manager."""
    
    def __init__(self, database_url: str = "sqlite:///data/app.db"):
        self.database_url = database_url
        self.is_sqlite = database_url.startswith("sqlite")
        
        if self.is_sqlite:
            # Extract file path from SQLite URL (handle both sqlite:/// and sqlite+aiosqlite:///)
            self.db_path = database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            # Remove leading ./ if present
            self.db_path = self.db_path.lstrip("./")
            logger.info(f"📁 Using database: {self.db_path}")
            self.db_dir = Path(self.db_path).parent
            self.db_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        if self.is_sqlite:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            try:
                yield conn
            finally:
                conn.close()
        else:
            # For other databases, implement appropriate connection logic
            raise NotImplementedError("Only SQLite is currently supported")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_script(self, script: str) -> None:
        """Execute a SQL script."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(script)
            conn.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        if self.is_sqlite:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        else:
            raise NotImplementedError("Only SQLite is currently supported")
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        if self.is_sqlite:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_query(query)
        else:
            raise NotImplementedError("Only SQLite is currently supported")
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        table_info = self.get_table_info(table_name)
        return any(col['name'] == column_name for col in table_info)
    
    def create_migration_table(self) -> None:
        """Create the migrations tracking table."""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_update(query)
    
    def is_migration_applied(self, migration_name: str) -> bool:
        """Check if a migration has been applied."""
        if not self.table_exists("migrations"):
            return False
        
        query = "SELECT COUNT(*) as count FROM migrations WHERE name = ?"
        result = self.execute_query(query, (migration_name,))
        return result[0]['count'] > 0
    
    def mark_migration_applied(self, migration_name: str) -> None:
        """Mark a migration as applied."""
        query = "INSERT INTO migrations (name) VALUES (?)"
        self.execute_update(query, (migration_name,))
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations."""
        if not self.table_exists("migrations"):
            return []
        
        query = "SELECT name FROM migrations ORDER BY applied_at"
        result = self.execute_query(query)
        return [row['name'] for row in result]


class MigrationManager:
    """Database migration manager."""
    
    def __init__(self, db_manager: DatabaseManager, migrations_dir: str = "migrations"):
        self.db_manager = db_manager
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    def run_core_migrations(self) -> None:
        """Run core application migrations."""
        logger.info("Running core database migrations...")
        
        # Ensure migrations table exists
        self.db_manager.create_migration_table()
        
        # Core migrations
        core_migrations = [
            ("001_create_users", self._create_users_table),
            ("002_create_settings", self._create_settings_table),
            ("003_create_api_keys", self._create_api_keys_table),
            ("004_create_groups", self._create_groups_tables),
            ("005_add_is_admin_column", self._add_is_admin_column),
            ("006_add_full_name_column", self._add_full_name_column),
        ]
        
        for migration_name, migration_func in core_migrations:
            if not self.db_manager.is_migration_applied(migration_name):
                logger.info(f"Applying migration: {migration_name}")
                try:
                    migration_func()
                    self.db_manager.mark_migration_applied(migration_name)
                    logger.info(f"Migration {migration_name} applied successfully")
                except Exception as e:
                    logger.error(f"Error applying migration {migration_name}: {e}")
                    raise
    
    def _create_users_table(self) -> None:
        """Create users table."""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_manager.execute_update(query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        ]
        
        for index_query in indexes:
            self.db_manager.execute_update(index_query)
    
    def _create_settings_table(self) -> None:
        """Create application settings table."""
        query = """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_manager.execute_update(query)
        
        # Insert default settings
        default_settings = [
            ("app_name", "CameronPAD", "Application name"),
            ("app_version", "2.0.0", "Application version"),
            ("registration_enabled", "false", "Whether user registration is enabled"),
            ("max_users", "10", "Maximum number of users allowed"),
        ]
        
        for key, value, description in default_settings:
            query = """
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES (?, ?, ?)
            """
            self.db_manager.execute_update(query, (key, value, description))
    
    def _create_api_keys_table(self) -> None:
        """Create API keys table."""
        query = """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            permissions TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1,
            expires_at DATETIME,
            last_used_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        self.db_manager.execute_update(query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)",
        ]
        
        for index_query in indexes:
            self.db_manager.execute_update(index_query)
    
    def _create_groups_tables(self) -> None:
        """Create groups and user_groups tables."""
        # Create groups table
        groups_query = """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
        )
        """
        self.db_manager.execute_update(groups_query)
        
        # Create user_groups junction table
        user_groups_query = """
        CREATE TABLE IF NOT EXISTS user_groups (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
            UNIQUE(user_id, group_id)
        )
        """
        self.db_manager.execute_update(user_groups_query)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name)",
            "CREATE INDEX IF NOT EXISTS idx_user_groups_user ON user_groups(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id)",
        ]
        
        for index_query in indexes:
            self.db_manager.execute_update(index_query)
        
        # Create default groups
        default_groups = [
            ("Everyone", "Default group for all users", None),
            ("Admins", "Administrator group", None),
        ]
        
        for name, description, created_by in default_groups:
            query = """
            INSERT OR IGNORE INTO groups (name, description, created_by) 
            VALUES (?, ?, ?)
            """
            self.db_manager.execute_update(query, (name, description, created_by))
    
    def _add_is_admin_column(self) -> None:
        """Add is_admin column to users table if it doesn't exist."""
        if not self.db_manager.column_exists("users", "is_admin"):
            query = "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"
            self.db_manager.execute_update(query)
            logger.info("✅ Added is_admin column to users table")
            
            # Update existing users with role='admin' to have is_admin=1
            update_query = "UPDATE users SET is_admin = 1 WHERE role = 'admin'"
            self.db_manager.execute_update(update_query)
            logger.info("✅ Updated existing admin users")
        else:
            logger.info("ℹ️ is_admin column already exists")
    
    def _add_full_name_column(self) -> None:
        """Add full_name column to users table if it doesn't exist."""
        if not self.db_manager.column_exists("users", "full_name"):
            query = "ALTER TABLE users ADD COLUMN full_name TEXT"
            self.db_manager.execute_update(query)
            logger.info("✅ Added full_name column to users table")
        else:
            logger.info("ℹ️ full_name column already exists")
    
    def run_plugin_migrations(self, plugin_name: str, migrations_path: str) -> None:
        """Run migrations for a specific plugin."""
        logger.info(f"Running migrations for plugin: {plugin_name}")
        
        migrations_dir = Path(migrations_path)
        if not migrations_dir.exists():
            logger.debug(f"No migrations directory found for plugin {plugin_name}")
            return
        
        # Get migration files
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.is_file()
        ])
        
        for migration_file in migration_files:
            migration_name = f"{plugin_name}_{migration_file.stem}"
            
            if not self.db_manager.is_migration_applied(migration_name):
                logger.info(f"Applying plugin migration: {migration_name}")
                try:
                    with open(migration_file, 'r') as f:
                        sql_script = f.read()
                    
                    self.db_manager.execute_script(sql_script)
                    self.db_manager.mark_migration_applied(migration_name)
                    logger.info(f"Plugin migration {migration_name} applied successfully")
                except Exception as e:
                    logger.error(f"Error applying plugin migration {migration_name}: {e}")
                    raise
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information."""
        applied_migrations = self.db_manager.get_applied_migrations()
        
        return {
            "total_applied": len(applied_migrations),
            "applied_migrations": applied_migrations,
            "database_url": self.db_manager.database_url,
            "database_exists": self.db_manager.table_exists("migrations")
        }


# Global database manager instance
_db_manager = None
_migration_manager = None


def get_database_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
        logger.info(f"🔧 Creating DatabaseManager with URL: {database_url}")
        _db_manager = DatabaseManager(database_url)
    return _db_manager


def get_migration_manager() -> MigrationManager:
    """Get global migration manager instance."""
    global _migration_manager
    if _migration_manager is None:
        db_manager = get_database_manager()
        _migration_manager = MigrationManager(db_manager)
    return _migration_manager


def initialize_database(database_url: Optional[str] = None) -> None:
    """Initialize database with core migrations."""
    global _db_manager, _migration_manager
    
    # Force recreation if database_url is provided
    if database_url is not None:
        logger.info(f"🔄 Initializing database with URL: {database_url}")
        _db_manager = None
        _migration_manager = None
    
    db_manager = get_database_manager(database_url)
    migration_manager = get_migration_manager()
    
    # Run core migrations
    migration_manager.run_core_migrations()
    
    logger.info("Database initialization completed")