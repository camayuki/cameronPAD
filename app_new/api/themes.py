"""
Theme Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..core.themes import get_theme_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ThemeSelection(BaseModel):
    theme_id: str
    custom_css: Optional[str] = None


@router.get("/themes")
async def get_available_themes(request: Request):
    """Get all available themes"""
    try:
        theme_manager = get_theme_manager()
        themes = theme_manager.get_all_themes()
        return {"themes": themes}
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/themes/current")
async def get_current_theme(request: Request):
    """Get current user's theme"""
    try:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        theme_manager = get_theme_manager()
        theme = theme_manager.get_user_theme(user_id)
        return theme
    except Exception as e:
        logger.error(f"Error fetching current theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/themes/set")
async def set_theme(theme_id: str = Form(...), custom_css: Optional[str] = Form(None), request: Request = None):
    """Set user's theme (form submission)"""
    try:
        user_id = getattr(request.state, "user_id", None) if request else None
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        theme_manager = get_theme_manager()
        theme_manager.set_user_theme(user_id, theme_id, custom_css)
        
        logger.info(f"✅ User {user_id} changed theme to '{theme_id}'")
        
        # Redirect back to settings
        return RedirectResponse(url="/settings", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/themes/set")
async def set_theme_api(theme_selection: ThemeSelection, request: Request):
    """Set user's theme (JSON API)"""
    try:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        theme_manager = get_theme_manager()
        theme_manager.set_user_theme(user_id, theme_selection.theme_id, theme_selection.custom_css)
        
        logger.info(f"✅ User {user_id} changed theme to '{theme_selection.theme_id}'")
        
        return {"status": "success", "theme_id": theme_selection.theme_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/themes/{theme_id}/preview")
async def preview_theme(theme_id: str):
    """Get theme CSS for preview"""
    try:
        theme_manager = get_theme_manager()
        css = theme_manager.get_theme_css(theme_id)
        return {"theme_id": theme_id, "css": css}
    except Exception as e:
        logger.error(f"Error previewing theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/themes/install")
async def install_theme(theme_url: str = Form(...), request: Request = None):
    """Install a theme from marketplace (future feature)"""
    try:
        user_id = getattr(request.state, "user_id", None) if request else None
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # TODO: Download theme from URL, validate, and install
        # For now, return not implemented
        raise HTTPException(status_code=501, detail="Theme marketplace coming soon!")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error installing theme: {e}")
        raise HTTPException(status_code=500, detail=str(e))
