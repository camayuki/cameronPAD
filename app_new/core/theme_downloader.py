"""
Theme Download Manager
Handles downloading, installing, and managing themes from external sources
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ThemeDownloader:
    """Manages downloading and installing themes from various sources"""
    
    # Default theme sources (can be configured via config file)
    THEME_SOURCES = {
        "github": {
            "name": "GitHub Theme Registry",
            "base_url": "https://raw.githubusercontent.com",
            "repos": [
                # Example: Your own theme repository
                {
                    "owner": "camayuki",
                    "repo": "cameronpad-themes",
                    "branch": "main",
                    "path": "themes"
                }
            ]
        },
        "cdn": {
            "name": "CameronPAD CDN",
            "base_url": "https://themes.cameronpad.com",
            "enabled": False  # Enable when you have a CDN
        }
    }
    
    # Sample theme registry (will be fetched from remote in production)
    SAMPLE_MARKETPLACE_THEMES = [
        {
            "id": "monokai-pro",
            "name": "Monokai Pro",
            "description": "Popular dark theme inspired by Monokai",
            "author": "Community",
            "version": "1.0.0",
            "category": "Dark",
            "tags": ["dark", "popular", "professional"],
            "preview_image": "https://via.placeholder.com/400x300/272822/F8F8F2?text=Monokai+Pro",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/monokai-pro.json",
            "rating": 4.8,
            "downloads": 1250,
            "css_variables": {
                "--primary-bg": "#272822",
                "--secondary-bg": "#1e1f1c",
                "--accent-bg": "#3e3d32",
                "--card-bg": "rgba(30, 31, 28, 0.9)",
                "--border-color": "#75715e",
                "--text-primary": "#f8f8f2",
                "--text-secondary": "#75715e",
                "--accent-primary": "#66d9ef",
                "--accent-secondary": "#ae81ff",
                "--accent-tertiary": "#a6e22e",
                "--danger": "#f92672",
                "--warning": "#e6db74",
                "--success": "#a6e22e",
                "--glow-color": "rgba(102, 217, 239, 0.3)",
                "--purple-glow": "rgba(174, 129, 255, 0.3)"
            }
        },
        {
            "id": "dracula",
            "name": "Dracula",
            "description": "Beautiful dark theme with vibrant colors",
            "author": "Community",
            "version": "1.0.0",
            "category": "Dark",
            "tags": ["dark", "vibrant", "popular"],
            "preview_image": "https://via.placeholder.com/400x300/282a36/f8f8f2?text=Dracula",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/dracula.json",
            "rating": 4.9,
            "downloads": 2100,
            "css_variables": {
                "--primary-bg": "#282a36",
                "--secondary-bg": "#1e1f29",
                "--accent-bg": "#44475a",
                "--card-bg": "rgba(30, 31, 41, 0.9)",
                "--border-color": "#6272a4",
                "--text-primary": "#f8f8f2",
                "--text-secondary": "#6272a4",
                "--accent-primary": "#8be9fd",
                "--accent-secondary": "#bd93f9",
                "--accent-tertiary": "#50fa7b",
                "--danger": "#ff5555",
                "--warning": "#f1fa8c",
                "--success": "#50fa7b",
                "--glow-color": "rgba(139, 233, 253, 0.3)",
                "--purple-glow": "rgba(189, 147, 249, 0.3)"
            }
        },
        {
            "id": "nord",
            "name": "Nord",
            "description": "Arctic, north-bluish color palette",
            "author": "Community",
            "version": "1.0.0",
            "category": "Dark",
            "tags": ["dark", "cool", "minimal"],
            "preview_image": "https://via.placeholder.com/400x300/2e3440/eceff4?text=Nord",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/nord.json",
            "rating": 4.7,
            "downloads": 1800,
            "css_variables": {
                "--primary-bg": "#2e3440",
                "--secondary-bg": "#242933",
                "--accent-bg": "#3b4252",
                "--card-bg": "rgba(36, 41, 51, 0.9)",
                "--border-color": "#4c566a",
                "--text-primary": "#eceff4",
                "--text-secondary": "#d8dee9",
                "--accent-primary": "#88c0d0",
                "--accent-secondary": "#b48ead",
                "--accent-tertiary": "#a3be8c",
                "--danger": "#bf616a",
                "--warning": "#ebcb8b",
                "--success": "#a3be8c",
                "--glow-color": "rgba(136, 192, 208, 0.3)",
                "--purple-glow": "rgba(180, 142, 173, 0.3)"
            }
        },
        {
            "id": "solarized-light",
            "name": "Solarized Light",
            "description": "Precision colors for machines and people",
            "author": "Community",
            "version": "1.0.0",
            "category": "Light",
            "tags": ["light", "warm", "minimal"],
            "preview_image": "https://via.placeholder.com/400x300/fdf6e3/657b83?text=Solarized+Light",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/solarized-light.json",
            "rating": 4.6,
            "downloads": 950,
            "css_variables": {
                "--primary-bg": "#fdf6e3",
                "--secondary-bg": "#eee8d5",
                "--accent-bg": "#ded8c5",
                "--card-bg": "rgba(238, 232, 213, 0.9)",
                "--border-color": "#93a1a1",
                "--text-primary": "#657b83",
                "--text-secondary": "#93a1a1",
                "--accent-primary": "#268bd2",
                "--accent-secondary": "#6c71c4",
                "--accent-tertiary": "#859900",
                "--danger": "#dc322f",
                "--warning": "#b58900",
                "--success": "#859900",
                "--glow-color": "rgba(38, 139, 210, 0.2)",
                "--purple-glow": "rgba(108, 113, 196, 0.2)"
            }
        },
        {
            "id": "tokyo-night",
            "name": "Tokyo Night",
            "description": "A clean dark theme inspired by Tokyo's night",
            "author": "Community",
            "version": "1.0.0",
            "category": "Dark",
            "tags": ["dark", "modern", "clean"],
            "preview_image": "https://via.placeholder.com/400x300/1a1b26/a9b1d6?text=Tokyo+Night",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/tokyo-night.json",
            "rating": 4.9,
            "downloads": 2500,
            "css_variables": {
                "--primary-bg": "#1a1b26",
                "--secondary-bg": "#16161e",
                "--accent-bg": "#24283b",
                "--card-bg": "rgba(22, 22, 30, 0.9)",
                "--border-color": "#414868",
                "--text-primary": "#a9b1d6",
                "--text-secondary": "#565f89",
                "--accent-primary": "#7aa2f7",
                "--accent-secondary": "#bb9af7",
                "--accent-tertiary": "#9ece6a",
                "--danger": "#f7768e",
                "--warning": "#e0af68",
                "--success": "#9ece6a",
                "--glow-color": "rgba(122, 162, 247, 0.3)",
                "--purple-glow": "rgba(187, 154, 247, 0.3)"
            }
        },
        {
            "id": "gruvbox",
            "name": "Gruvbox",
            "description": "Retro groove color scheme with pastel 'retro groove' colors",
            "author": "Community",
            "version": "1.0.0",
            "category": "Dark",
            "tags": ["dark", "warm", "retro"],
            "preview_image": "https://via.placeholder.com/400x300/282828/ebdbb2?text=Gruvbox",
            "download_url": "https://raw.githubusercontent.com/camayuki/cameronpad-themes/main/gruvbox.json",
            "rating": 4.8,
            "downloads": 1600,
            "css_variables": {
                "--primary-bg": "#282828",
                "--secondary-bg": "#1d2021",
                "--accent-bg": "#3c3836",
                "--card-bg": "rgba(29, 32, 33, 0.9)",
                "--border-color": "#504945",
                "--text-primary": "#ebdbb2",
                "--text-secondary": "#a89984",
                "--accent-primary": "#83a598",
                "--accent-secondary": "#d3869b",
                "--accent-tertiary": "#b8bb26",
                "--danger": "#fb4934",
                "--warning": "#fabd2f",
                "--success": "#b8bb26",
                "--glow-color": "rgba(131, 165, 152, 0.3)",
                "--purple-glow": "rgba(211, 134, 155, 0.3)"
            }
        }
    ]
    
    def __init__(self):
        self.timeout = 10  # seconds
    
    def get_marketplace_themes(self) -> List[Dict[str, Any]]:
        """
        Get available themes from marketplace
        Fetches from GitHub repository
        """
        logger.info("📦 Fetching marketplace themes from GitHub...")
        
        # Use jsDelivr CDN for better cache control
        marketplace_url = "https://cdn.jsdelivr.net/gh/camayuki/theme_marketplace@main/index.json"
        
        try:
            response = urllib.request.urlopen(marketplace_url, timeout=self.timeout)
            data = json.loads(response.read())
            themes = data.get("themes", [])
            logger.info(f"✅ Loaded {len(themes)} themes from marketplace")
            return themes
        except urllib.error.URLError as e:
            logger.warning(f"⚠️ Failed to fetch from GitHub marketplace: {e}")
            logger.info("📦 Using sample themes as fallback")
            return self.SAMPLE_MARKETPLACE_THEMES
        except Exception as e:
            logger.error(f"❌ Error loading marketplace themes: {e}")
            return self.SAMPLE_MARKETPLACE_THEMES
    
    def download_theme(self, theme_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Download theme from URL
        
        Args:
            theme_data: Theme metadata including download_url
            
        Returns:
            Theme data ready for installation, or None if failed
        """
        download_url = theme_data.get("download_url")
        
        if not download_url:
            logger.error("No download URL provided")
            return None
        
        try:
            logger.info(f"⬇️ Downloading theme from: {download_url}")
            
            # Download theme from GitHub or other source
            if download_url.startswith("https://raw.githubusercontent.com") or download_url.startswith("https://cdn.jsdelivr.net"):
                # Actually download the theme JSON file
                try:
                    response = urllib.request.urlopen(download_url, timeout=self.timeout)
                    theme_json = json.loads(response.read())
                    
                    logger.info(f"✅ Successfully downloaded theme: {theme_data['name']}")
                    return theme_json
                except Exception as e:
                    logger.warning(f"⚠️ Failed to download from {download_url}: {e}")
                    # Fall back to using theme_data if it has css_variables
                    if "css_variables" in theme_data:
                        logger.info(f"📦 Using theme data from index")
                        return {
                            "id": theme_data["id"],
                            "name": theme_data["name"],
                            "description": theme_data["description"],
                            "author": theme_data.get("author", "Community"),
                            "version": theme_data.get("version", "1.0.0"),
                            "css_variables": theme_data["css_variables"]
                        }
                    return None
            
        except urllib.error.URLError as e:
            logger.error(f"❌ Failed to download theme: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid theme JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading theme: {e}")
            return None
    
    def validate_theme(self, theme_data: Dict[str, Any]) -> bool:
        """
        Validate theme data structure and required fields
        
        Args:
            theme_data: Theme data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "name", "css_variables"]
        
        # Check required fields
        for field in required_fields:
            if field not in theme_data:
                logger.error(f"❌ Theme missing required field: {field}")
                return False
        
        # Validate CSS variables
        css_vars = theme_data["css_variables"]
        if not isinstance(css_vars, dict):
            logger.error("❌ css_variables must be a dictionary")
            return False
        
        # Check for minimum required CSS variables
        required_vars = [
            "--primary-bg",
            "--secondary-bg",
            "--text-primary",
            "--accent-primary"
        ]
        
        for var in required_vars:
            if var not in css_vars:
                logger.warning(f"⚠️ Theme missing recommended variable: {var}")
        
        logger.info(f"✅ Theme validation passed: {theme_data['name']}")
        return True
    
    def search_themes(self, query: str, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Search themes by name, description, or tags
        
        Args:
            query: Search query
            themes: List of themes to search
            
        Returns:
            Filtered list of themes
        """
        query = query.lower()
        results = []
        
        for theme in themes:
            # Search in name
            if query in theme.get("name", "").lower():
                results.append(theme)
                continue
            
            # Search in description
            if query in theme.get("description", "").lower():
                results.append(theme)
                continue
            
            # Search in tags
            tags = theme.get("tags", [])
            if any(query in tag.lower() for tag in tags):
                results.append(theme)
                continue
            
            # Search in category
            if query in theme.get("category", "").lower():
                results.append(theme)
                continue
        
        return results
    
    def filter_by_category(self, category: str, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter themes by category"""
        return [t for t in themes if t.get("category", "").lower() == category.lower()]
    
    def sort_themes(self, themes: List[Dict[str, Any]], sort_by: str = "downloads") -> List[Dict[str, Any]]:
        """
        Sort themes by various criteria
        
        Args:
            themes: List of themes to sort
            sort_by: Sorting criteria (downloads, rating, name, date)
            
        Returns:
            Sorted list of themes
        """
        if sort_by == "downloads":
            return sorted(themes, key=lambda t: t.get("downloads", 0), reverse=True)
        elif sort_by == "rating":
            return sorted(themes, key=lambda t: t.get("rating", 0), reverse=True)
        elif sort_by == "name":
            return sorted(themes, key=lambda t: t.get("name", "").lower())
        else:
            return themes


# Global instance
_theme_downloader = None


def get_theme_downloader() -> ThemeDownloader:
    """Get global theme downloader instance"""
    global _theme_downloader
    if _theme_downloader is None:
        _theme_downloader = ThemeDownloader()
    return _theme_downloader
