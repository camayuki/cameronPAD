"""
Authentication routes for login, logout, and registration.
"""
import logging
from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app_new.core.auth import get_user_manager, get_security_manager
from app_new.core.database import get_database_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

# Setup templates
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    """Display login page."""
    logger.info("🌐 GET /auth/login - Displaying login page")
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "next": next,
        "error": None
    })


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
    remember: bool = Form(default=False)
):
    """Process login form."""
    logger.info("=" * 80)
    logger.info("🚀 LOGIN HANDLER CALLED!")
    logger.info(f"📬 POST /auth/login received!")
    logger.info(f"🔐 Username: '{username}', Password length: {len(password)}")
    logger.info("=" * 80)
    
    try:
        
        user_manager = get_user_manager()
        security_manager = get_security_manager()
        db = get_database_manager()
        
        # Authenticate user
        try:
            logger.info(f"🔍 Calling authenticate_user for '{username}'")
            user = user_manager.authenticate_user(username, password)
            logger.info(f"✅ authenticate_user returned: {user}")
        except Exception as e:
            logger.error(f"❌ Exception during authentication: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "next": next,
                "error": str(e)
            }, status_code=400)
        
        if not user:
            logger.warning("=" * 80)
            logger.warning("❌ USER IS NONE - AUTHENTICATION FAILED!")
            logger.warning(f"Username attempted: {username}")
            logger.warning(f"Password length: {len(password)}")
            logger.warning("=" * 80)
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "next": next,
                "error": "Invalid username or password"
            }, status_code=400)
        
        if not user.get("is_active"):
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "next": next,
                "error": "Account is disabled"
            }, status_code=400)
        
        # Create access token
        try:
            logger.info(f"✅ User authenticated successfully: {user.get('username')}")
            logger.info("Creating access token...")
            token = user_manager.create_access_token(user)
            logger.info("✅ Token created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating token: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
        # Create redirect response
        redirect_url = next if next else "/"
        redirect_response = RedirectResponse(url=redirect_url, status_code=303)
        
        # Set token as cookie (no "Bearer " prefix in cookie, only in Authorization header)
        max_age = 30 * 24 * 60 * 60 if remember else None  # 30 days if remember me
        redirect_response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=max_age,
            samesite="lax"
        )
        logger.info(f"🍪 Cookie set: access_token (max_age={max_age})")
        
        logger.info(f"✅ Login successful! Redirecting to: {redirect_url}")
        logger.info("=" * 80)
        
        return redirect_response
    
    except Exception as e:
        logger.error("❌❌❌ EXCEPTION IN LOGIN HANDLER ❌❌❌")
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise


@router.get("/logout")
async def logout(request: Request):
    """Logout user."""
    logger.info("🚪 User logging out")
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page (if enabled)."""
    # For now, registration is disabled - admin must create users
    return RedirectResponse(url="/auth/login")
