"""
Theme Management System for CameronPAD
Handles theme selection, storage, and marketplace features
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ThemeManager:
    """Manages themes, user preferences, and theme marketplace"""
    
    def __init__(self, db_path: str = "data/cameronpad_dev.db"):
        self.db_path = db_path
        self.themes_dir = Path("themes")
        self.themes_dir.mkdir(exist_ok=True)
        self.db_readonly = False  # Track if database is readonly
        self._init_database()
        self._load_built_in_themes()
    
    def _init_database(self):
        """Initialize theme tables in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                # User theme preferences
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_themes (
                        user_id INTEGER PRIMARY KEY,
                        theme_id TEXT NOT NULL,
                        custom_css TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Available themes (marketplace + built-in)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS themes (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        author TEXT,
                        version TEXT,
                        is_builtin INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        css_variables TEXT NOT NULL,
                        preview_image TEXT,
                        download_url TEXT,
                        install_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("✅ Theme tables initialized")
        except sqlite3.OperationalError as e:
            if "readonly" in str(e).lower() or "attempt to write" in str(e).lower():
                self.db_readonly = True
                logger.warning(f"⚠️ Database is readonly - theme updates disabled. Run fix_permissions.sh to fix.")
            else:
                logger.error(f"❌ Error initializing theme database: {e}")
                raise
    
    def _load_built_in_themes(self):
        """Load built-in themes into database"""
        built_in_themes = [
            {
                "id": "space",
                "name": "Space Theme (Default)",
                "description": "Dark space-themed interface with glowing accents",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#0a0e1a",
                    "--secondary-bg": "#1a1f35",
                    "--accent-bg": "#2d3561",
                    "--card-bg": "rgba(26, 31, 53, 0.8)",
                    "--border-color": "#3d4785",
                    "--text-primary": "#e8eaed",
                    "--text-secondary": "#9aa0a6",
                    "--accent-primary": "#4fc3f7",
                    "--accent-secondary": "#ab47bc",
                    "--accent-tertiary": "#66bb6a",
                    "--danger": "#f44336",
                    "--warning": "#ff9800",
                    "--success": "#4caf50",
                    "--glow-color": "rgba(79, 195, 247, 0.3)",
                    "--purple-glow": "rgba(171, 71, 188, 0.3)"
                })
            },
            {
                "id": "dark",
                "name": "Classic Dark",
                "description": "Simple dark theme with minimal distractions",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#1e1e1e",
                    "--secondary-bg": "#2d2d30",
                    "--accent-bg": "#3e3e42",
                    "--card-bg": "rgba(45, 45, 48, 0.95)",
                    "--border-color": "#555555",
                    "--text-primary": "#d4d4d4",
                    "--text-secondary": "#999999",
                    "--accent-primary": "#007acc",
                    "--accent-secondary": "#68217a",
                    "--accent-tertiary": "#4ec9b0",
                    "--danger": "#f48771",
                    "--warning": "#cca700",
                    "--success": "#89d185",
                    "--glow-color": "rgba(0, 122, 204, 0.2)",
                    "--purple-glow": "rgba(104, 33, 122, 0.2)"
                })
            },
            {
                "id": "light",
                "name": "Light Mode",
                "description": "Clean light theme for daytime use",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#ffffff",
                    "--secondary-bg": "#f5f5f5",
                    "--accent-bg": "#e0e0e0",
                    "--card-bg": "rgba(255, 255, 255, 0.95)",
                    "--border-color": "#d0d0d0",
                    "--text-primary": "#1e1e1e",
                    "--text-secondary": "#666666",
                    "--accent-primary": "#0078d4",
                    "--accent-secondary": "#8764b8",
                    "--accent-tertiary": "#107c10",
                    "--danger": "#d13438",
                    "--warning": "#ff8c00",
                    "--success": "#107c10",
                    "--glow-color": "rgba(0, 120, 212, 0.1)",
                    "--purple-glow": "rgba(135, 100, 184, 0.1)"
                })
            },
            {
                "id": "cyberpunk",
                "name": "Cyberpunk Neon",
                "description": "Vibrant neon colors with futuristic vibes",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#0d0221",
                    "--secondary-bg": "#1a0933",
                    "--accent-bg": "#2d1b69",
                    "--card-bg": "rgba(26, 9, 51, 0.9)",
                    "--border-color": "#ff006e",
                    "--text-primary": "#00f3ff",
                    "--text-secondary": "#b967ff",
                    "--accent-primary": "#ff006e",
                    "--accent-secondary": "#ffbe0b",
                    "--accent-tertiary": "#8338ec",
                    "--danger": "#ff006e",
                    "--warning": "#ffbe0b",
                    "--success": "#06ffa5",
                    "--glow-color": "rgba(255, 0, 110, 0.5)",
                    "--purple-glow": "rgba(179, 103, 255, 0.5)"
                })
            },
            {
                "id": "forest",
                "name": "Forest Green",
                "description": "Calming nature-inspired green theme",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#1a2f1a",
                    "--secondary-bg": "#2d4a2d",
                    "--accent-bg": "#3d5c3d",
                    "--card-bg": "rgba(45, 74, 45, 0.9)",
                    "--border-color": "#5a8a5a",
                    "--text-primary": "#e8f5e8",
                    "--text-secondary": "#a8c9a8",
                    "--accent-primary": "#66bb6a",
                    "--accent-secondary": "#81c784",
                    "--accent-tertiary": "#a5d6a7",
                    "--danger": "#ef5350",
                    "--warning": "#ffa726",
                    "--success": "#66bb6a",
                    "--glow-color": "rgba(102, 187, 106, 0.3)",
                    "--purple-glow": "rgba(129, 199, 132, 0.3)"
                })
            },
            {
                "id": "ocean",
                "name": "Ocean Blue",
                "description": "Deep blue ocean-inspired theme",
                "author": "CameronPAD",
                "version": "1.0.0",
                "is_builtin": 1,
                "css_variables": json.dumps({
                    "--primary-bg": "#0a1929",
                    "--secondary-bg": "#1a3a52",
                    "--accent-bg": "#2d5a7b",
                    "--card-bg": "rgba(26, 58, 82, 0.9)",
                    "--border-color": "#3d7aa4",
                    "--text-primary": "#e3f2fd",
                    "--text-secondary": "#90caf9",
                    "--accent-primary": "#29b6f6",
                    "--accent-secondary": "#4fc3f7",
                    "--accent-tertiary": "#81d4fa",
                    "--danger": "#ef5350",
                    "--warning": "#ff9800",
                    "--success": "#26a69a",
                    "--glow-color": "rgba(41, 182, 246, 0.3)",
                    "--purple-glow": "rgba(79, 195, 247, 0.3)"
                })
            }
        ]
        
        # Skip if database is readonly
        if self.db_readonly:
            logger.warning("⚠️ Skipping built-in theme load - database is readonly")
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                for theme in built_in_themes:
                    cur.execute("""
                        INSERT OR REPLACE INTO themes (id, name, description, author, version, is_builtin, css_variables)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (theme["id"], theme["name"], theme["description"], theme["author"], 
                          theme["version"], theme["is_builtin"], theme["css_variables"]))
                conn.commit()
                logger.info(f"✅ Loaded {len(built_in_themes)} built-in themes")
        except sqlite3.OperationalError as e:
            if "readonly" in str(e).lower() or "attempt to write" in str(e).lower():
                self.db_readonly = True
                logger.warning(f"⚠️ Database is readonly - cannot load built-in themes. Run fix_permissions.sh")
            else:
                logger.error(f"❌ Error loading built-in themes: {e}")
                raise
    
    def get_user_theme(self, user_id: int) -> Dict[str, Any]:
        """Get user's selected theme or default"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Check user preference
            cur.execute("""
                SELECT ut.theme_id, ut.custom_css, t.name, t.css_variables
                FROM user_themes ut
                JOIN themes t ON ut.theme_id = t.id
                WHERE ut.user_id = ?
            """, (user_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    "theme_id": result["theme_id"],
                    "theme_name": result["name"],
                    "css_variables": json.loads(result["css_variables"]),
                    "custom_css": result["custom_css"]
                }
            
            # Return default space theme
            cur.execute("SELECT * FROM themes WHERE id = 'space'")
            default = cur.fetchone()
            return {
                "theme_id": "space",
                "theme_name": default["name"],
                "css_variables": json.loads(default["css_variables"]),
                "custom_css": None
            }
    
    def set_user_theme(self, user_id: int, theme_id: str, custom_css: Optional[str] = None):
        """Set user's theme preference"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            
            # Verify theme exists
            cur.execute("SELECT id FROM themes WHERE id = ?", (theme_id,))
            if not cur.fetchone():
                raise ValueError(f"Theme '{theme_id}' not found")
            
            # Update user preference
            cur.execute("""
                INSERT OR REPLACE INTO user_themes (user_id, theme_id, custom_css, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, theme_id, custom_css))
            
            conn.commit()
            logger.info(f"✅ User {user_id} theme set to '{theme_id}'")
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Get all available themes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, description, author, version, is_builtin, 
                       preview_image, rating, install_count
                FROM themes 
                WHERE is_active = 1
                ORDER BY is_builtin DESC, rating DESC, name ASC
            """)
            return [dict(row) for row in cur.fetchall()]
    
    def get_theme_css(self, theme_id: str) -> str:
        """Get CSS variables for a theme"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT css_variables FROM themes WHERE id = ?", (theme_id,))
            result = cur.fetchone()
            if result:
                variables = json.loads(result["css_variables"])
                return "\n".join([f"    {k}: {v};" for k, v in variables.items()])
            return ""
    
    def install_theme_from_file(self, theme_file_path: str, user_id: Optional[int] = None):
        """Install a theme from a JSON file (for marketplace downloads)"""
        with open(theme_file_path, 'r') as f:
            theme_data = json.load(f)
        
        required_fields = ["id", "name", "css_variables"]
        for field in required_fields:
            if field not in theme_data:
                raise ValueError(f"Theme file missing required field: {field}")
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO themes 
                (id, name, description, author, version, is_builtin, css_variables, 
                 preview_image, download_url)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            """, (
                theme_data["id"],
                theme_data["name"],
                theme_data.get("description", ""),
                theme_data.get("author", "Unknown"),
                theme_data.get("version", "1.0.0"),
                json.dumps(theme_data["css_variables"]),
                theme_data.get("preview_image"),
                theme_data.get("download_url")
            ))
            
            # Increment install count
            cur.execute("UPDATE themes SET install_count = install_count + 1 WHERE id = ?", 
                       (theme_data["id"],))
            
            conn.commit()
            logger.info(f"✅ Theme '{theme_data['name']}' installed")
        
        return theme_data["id"]
    
    def install_theme_from_data(self, theme_id: str, name: str, description: str,
                                author: str, version: str, css_variables: dict,
                                preview_image: Optional[str] = None,
                                download_url: Optional[str] = None) -> bool:
        """Install a theme from data dictionary (for marketplace downloads)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO themes 
                    (id, name, description, author, version, is_builtin, css_variables, 
                     preview_image, download_url)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                """, (
                    theme_id,
                    name,
                    description,
                    author,
                    version,
                    json.dumps(css_variables),
                    preview_image,
                    download_url
                ))
                
                # Increment install count
                cur.execute("UPDATE themes SET install_count = install_count + 1 WHERE id = ?", 
                           (theme_id,))
                
                conn.commit()
                logger.info(f"✅ Theme '{name}' installed from data")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to install theme: {e}")
            return False
    
    def uninstall_theme(self, theme_id: str) -> bool:
        """Uninstall a non-builtin theme"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                
                # Check if theme is builtin
                cur.execute("SELECT is_builtin FROM themes WHERE id = ?", (theme_id,))
                result = cur.fetchone()
                
                if not result:
                    logger.warning(f"Theme {theme_id} not found")
                    return False
                
                if result[0]:  # is_builtin
                    logger.warning(f"Cannot uninstall built-in theme: {theme_id}")
                    return False
                
                # Delete theme
                cur.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
                
                # Reset users using this theme to default
                cur.execute("DELETE FROM user_themes WHERE theme_id = ?", (theme_id,))
                
                conn.commit()
                logger.info(f"✅ Theme '{theme_id}' uninstalled")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to uninstall theme: {e}")
            return False


def get_theme_manager() -> ThemeManager:
    """Get theme manager singleton"""
    return ThemeManager()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tm = ThemeManager()
    print("Available themes:")
    for theme in tm.get_all_themes():
        print(f"  - {theme['name']} ({theme['id']})")
