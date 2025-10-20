"""
Theme Marketplace API
Handles browsing, downloading, and installing themes from marketplace
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional
import logging

from app_new.core.themes import get_theme_manager
from app_new.core.theme_downloader import get_theme_downloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/themes/marketplace", tags=["theme-marketplace"])


def get_current_user_from_state(request: Request) -> Optional[dict]:
    """Extract current user from request.state"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return None
    
    return {
        "id": user_id,
        "username": getattr(request.state, 'username', 'Unknown'),
        "role": 'admin' if getattr(request.state, 'is_admin', False) else 'user',
        "is_admin": getattr(request.state, 'is_admin', False)
    }


@router.get("", response_class=HTMLResponse)
async def marketplace_page(request: Request):
    """Theme marketplace page"""
    try:
        current_user = get_current_user_from_state(request)
        
        if not current_user:
            return RedirectResponse(url="/login", status_code=303)
        
        # Get marketplace themes
        downloader = get_theme_downloader()
        marketplace_themes = downloader.get_marketplace_themes()
        
        # Get user's installed themes to mark which are already installed
        theme_manager = get_theme_manager()
        
        # Check if database is readonly
        db_readonly_warning = None
        if theme_manager.db_readonly:
            db_readonly_warning = "⚠️ Database is readonly. Theme installation disabled. Run 'fix_permissions.sh' on your server to enable."
        
        installed_themes = theme_manager.get_all_themes()
        installed_ids = {t["id"] for t in installed_themes}
        
        # Mark themes as installed
        for theme in marketplace_themes:
            theme["is_installed"] = theme["id"] in installed_ids
        
        # Get templates from app state
        templates = getattr(request.app.state, 'templates', None)
        if not templates:
            raise HTTPException(status_code=500, detail="Templates not initialized")
        
        return templates.TemplateResponse("theme_marketplace.html", {
            "request": request,
            "current_user": current_user,
            "marketplace_themes": marketplace_themes,
            "installed_count": len(installed_ids),
            "db_readonly_warning": db_readonly_warning
        })
    
    except Exception as e:
        logger.error(f"Error loading marketplace: {e}", exc_info=True)
        # Show friendly error if database is readonly
        if "readonly" in str(e).lower() or "attempt to write" in str(e).lower():
            raise HTTPException(
                status_code=500, 
                detail="Database is readonly. Run 'chmod 664 data/cameronpad.db' or './fix_permissions.sh' on your server."
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/themes", response_class=JSONResponse)
async def get_marketplace_themes_api(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "downloads"
):
    """API endpoint to get marketplace themes with filtering"""
    try:
        current_user = get_current_user_from_state(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        downloader = get_theme_downloader()
        themes = downloader.get_marketplace_themes()
        
        # Apply filters
        if category:
            themes = downloader.filter_by_category(category, themes)
        
        if search:
            themes = downloader.search_themes(search, themes)
        
        # Sort themes
        themes = downloader.sort_themes(themes, sort)
        
        return {
            "success": True,
            "themes": themes,
            "count": len(themes)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching marketplace themes: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/api/install/{theme_id}")
async def install_theme_from_marketplace(theme_id: str, request: Request):
    """
    Download and install a theme from marketplace
    Returns installation status and theme details
    """
    try:
        current_user = get_current_user_from_state(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        logger.info(f"🎨 Installing theme '{theme_id}' for user {current_user.get('username')}")
        
        # Get theme data from marketplace
        downloader = get_theme_downloader()
        marketplace_themes = downloader.get_marketplace_themes()
        
        theme_data = next((t for t in marketplace_themes if t["id"] == theme_id), None)
        if not theme_data:
            raise HTTPException(status_code=404, detail="Theme not found in marketplace")
        
        # Check if already installed
        theme_manager = get_theme_manager()
        existing_theme = next((t for t in theme_manager.get_all_themes() if t["id"] == theme_id), None)
        
        if existing_theme:
            return {
                "success": True,
                "already_installed": True,
                "message": f"Theme '{theme_data['name']}' is already installed",
                "theme": existing_theme
            }
        
        # Download theme
        downloaded_theme = downloader.download_theme(theme_data)
        if not downloaded_theme:
            raise HTTPException(status_code=500, detail="Failed to download theme")
        
        # Validate theme
        if not downloader.validate_theme(downloaded_theme):
            raise HTTPException(status_code=400, detail="Invalid theme format")
        
        # Install theme using theme manager
        success = theme_manager.install_theme_from_data(
            theme_id=downloaded_theme["id"],
            name=downloaded_theme["name"],
            description=downloaded_theme.get("description", ""),
            author=downloaded_theme.get("author", "Community"),
            version=downloaded_theme.get("version", "1.0.0"),
            css_variables=downloaded_theme["css_variables"],
            preview_image=theme_data.get("preview_image"),
            download_url=theme_data.get("download_url")
        )
        
        if success:
            logger.info(f"✅ Theme '{theme_data['name']}' installed successfully")
            return {
                "success": True,
                "already_installed": False,
                "message": f"Theme '{theme_data['name']}' installed successfully!",
                "theme": downloaded_theme,
                "prompt_apply": True  # Signal to frontend to ask user if they want to apply
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to install theme")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error installing theme: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/uninstall/{theme_id}")
async def uninstall_marketplace_theme(theme_id: str, request: Request):
    """Uninstall a marketplace theme (only non-builtin themes can be uninstalled)"""
    try:
        current_user = get_current_user_from_state(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        theme_manager = get_theme_manager()
        
        # Check if theme exists and is not builtin
        theme = next((t for t in theme_manager.get_all_themes() if t["id"] == theme_id), None)
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        if theme.get("is_builtin"):
            raise HTTPException(status_code=400, detail="Cannot uninstall built-in themes")
        
        # Uninstall theme
        success = theme_manager.uninstall_theme(theme_id)
        
        if success:
            return {
                "success": True,
                "message": f"Theme '{theme['theme_name']}' uninstalled successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to uninstall theme")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uninstalling theme: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
