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
async def login_page(request: Request, next: str = "/", success: str = None):
    """Display login page."""
    logger.info("🌐 GET /auth/login - Displaying login page")
    
    # Get plugin stats and featured apps for the info panel
    from app_new.main import plugin_manager
    featured_apps = []
    
    if plugin_manager:
        enabled_plugins = plugin_manager.get_enabled_plugins()
        stats = {
            "total_plugins": len(plugin_manager.plugins),
            "active_plugins": len(enabled_plugins)
        }
        
        # Get featured apps (stocks, surf, system_monitor, notes)
        featured_names = ["stocks", "surf", "system_monitor", "notes"]
        for plugin_name in enabled_plugins:
            # Get the actual plugin object
            plugin = plugin_manager.plugins.get(plugin_name)
            if plugin and plugin_name.lower() in featured_names:
                featured_apps.append({
                    "name": plugin.metadata.name.title(),  # Use metadata.name and capitalize
                    "icon": getattr(plugin.metadata, "icon", "🔌"),
                    "description": plugin.metadata.description,
                    "route": f"/api/v1/plugins/{plugin_name}",  # Use plugin_name (the key)
                    "requires_auth": getattr(plugin.metadata, "requires_auth", True)  # Default to requiring auth
                })
            if len(featured_apps) >= 4:  # Limit to 4 featured apps
                break
    else:
        stats = {
            "total_plugins": 9,
            "active_plugins": 9
        }
    
    # Always provide default featured apps if we don't have enough
    if len(featured_apps) < 4:
        featured_apps = [
            {"name": "Stocks", "icon": "📈", "description": "Real-time stock tracking", "route": "/api/v1/plugins/stocks", "requires_auth": True},
            {"name": "Surf", "icon": "🏄", "description": "Wave conditions monitor", "route": "/api/v1/plugins/surf", "requires_auth": False},
            {"name": "System Monitor", "icon": "🖥️", "description": "Server health dashboard", "route": "/api/v1/plugins/system_monitor", "requires_auth": True},
            {"name": "Notes", "icon": "📝", "description": "Quick note-taking", "route": "/api/v1/plugins/notes", "requires_auth": True}
        ]
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "next": next,
        "error": None,
        "success": success,
        "stats": stats,
        "featured_apps": featured_apps
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
    """Display registration page."""
    logger.info("🌐 GET /auth/register - Displaying registration page")
    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "error": None,
        "success": None
    })


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Process registration form."""
    logger.info("=" * 80)
    logger.info("🎉 REGISTRATION HANDLER CALLED!")
    logger.info(f"📬 POST /auth/register received!")
    logger.info(f"👤 Username: '{username}', Email: '{email}'")
    logger.info("=" * 80)
    
    try:
        # Validate passwords match
        if password != confirm_password:
            logger.warning("❌ Passwords do not match")
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "error": "Passwords do not match",
                "username": username,
                "email": email
            }, status_code=400)
        
        # Validate password length
        if len(password) < 8:
            logger.warning("❌ Password too short")
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "error": "Password must be at least 8 characters",
                "username": username,
                "email": email
            }, status_code=400)
        
        # Validate username format (alphanumeric and underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', username):
            logger.warning("❌ Invalid username format")
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "error": "Username must be 3-50 characters (letters, numbers, underscores only)",
                "email": email
            }, status_code=400)
        
        user_manager = get_user_manager()
        db = get_database_manager()
        
        # Check if username already exists
        try:
            existing_user = user_manager.get_user(username)
            if existing_user:
                logger.warning(f"❌ Username '{username}' already exists")
                return templates.TemplateResponse("auth/register.html", {
                    "request": request,
                    "error": "Username already exists",
                    "email": email
                }, status_code=400)
        except Exception:
            # User doesn't exist, this is fine
            pass
        
        # Check if email already exists
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_email = cursor.fetchone()
                if existing_email:
                    logger.warning(f"❌ Email '{email}' already registered")
                    return templates.TemplateResponse("auth/register.html", {
                        "request": request,
                        "error": "Email already registered",
                        "username": username
                    }, status_code=400)
        except Exception as e:
            logger.error(f"Error checking email: {e}")
        
        # Create new user
        try:
            logger.info(f"✅ Creating new user: {username}")
            new_user = user_manager.create_user(
                username=username,
                password=password,
                email=email,
                is_admin=False
            )
            logger.info(f"✅ User created successfully: {username}")
            
            # Automatically log in the new user
            user = user_manager.authenticate_user(username, password)
            if user:
                # Create access token
                token = user_manager.create_access_token(user)
                
                # Create redirect response to dashboard
                redirect_response = RedirectResponse(url="/", status_code=303)
                
                # Set token as cookie
                redirect_response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=True,
                    max_age=30 * 24 * 60 * 60,  # 30 days
                    samesite="lax"
                )
                
                logger.info(f"✅ User {username} automatically logged in after registration")
                return redirect_response
            else:
                # Fallback: redirect to login if authentication fails
                return RedirectResponse(
                    url=f"/auth/login?success=Account created successfully! Please log in.",
                    status_code=303
                )
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "error": f"Error creating account: {str(e)}",
                "username": username,
                "email": email
            }, status_code=500)
    
    except Exception as e:
        logger.error("❌❌❌ EXCEPTION IN REGISTRATION HANDLER ❌❌❌")
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "An unexpected error occurred. Please try again.",
            "username": username,
            "email": email
        }, status_code=500)
