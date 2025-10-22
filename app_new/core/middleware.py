# Enhanced Authentication Middleware

import logging
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse
import jwt
from typing import Optional
from app_new.core.auth import get_security_manager
from app_new.core.database import get_database_manager

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication on all routes except public ones"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_manager = get_security_manager()
        self.public_plugins = []  # Will be populated by app
        
        # Routes that don't require authentication
        self.public_routes = {
            "/auth/login",
            "/auth/register",
            "/auth/logout",
            "/health",
            "/docs",
            "/openapi.json",
            "/static",
            "/favicon.ico"
        }
        
        # API routes that don't require authentication
        self.public_api_routes = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/health"
        }
    
    def add_public_plugin(self, plugin_name: str):
        """Add a plugin to the public access list"""
        plugin_path = f"/api/v1/plugins/{plugin_name}"
        self.public_plugins.append(plugin_path)
        logger.info(f"🔓 Registered public plugin: {plugin_path}")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        logger.debug(f"🔍 Middleware: {request.method} {path}")
        
        # Check if route is public (including dynamic plugin check)
        is_public = self._is_public_route(path, request)
        if is_public:
            logger.debug(f"✅ Public route allowed: {path}")
            # Even for public routes, try to extract user info if token exists
            token = self._extract_token(request)
            if token:
                try:
                    payload = self.security_manager.verify_token(token)
                    request.state.user_id = payload.get("sub")
                    request.state.username = payload.get("username")
                    request.state.is_admin = payload.get("is_admin")
                    request.state.token_payload = payload
                    logger.debug(f"✅ Optional auth for public route: {payload.get('username')}")
                except:
                    # Silently fail for public routes - user just won't be authenticated
                    pass
            return await call_next(request)
        
        # Check for authentication
        token = self._extract_token(request)
        
        if not token:
            logger.warning(f"❌ No token found, redirecting to login")
            # For API requests return a JSON 401 to avoid raising exceptions from middleware
            if path.startswith('/api/'):
                return JSONResponse(status_code=401, content={"detail": "Authentication required"})
            return self._redirect_to_login(request)
        
        try:
            # Verify token
            logger.info(f"🔍 Verifying token...")
            payload = self.security_manager.verify_token(token)
            logger.info(f"✅ Token verified! Payload: {payload}")
            
            # Add user info to request state
            # Token payload already contains user info, just store it
            request.state.user_id = payload.get("sub")
            request.state.username = payload.get("username")
            request.state.is_admin = payload.get("is_admin")
            request.state.token_payload = payload
            
            # Load user's theme preference
            try:
                from .themes import get_theme_manager
                theme_manager = get_theme_manager()
                user_theme = theme_manager.get_user_theme(request.state.user_id)
                request.state.theme = user_theme
            except Exception as theme_error:
                logger.warning(f"Could not load theme: {theme_error}")
                request.state.theme = None
            
            logger.info(f"✅ User authenticated: {payload.get('username')}")
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Invalid token: {e}")
            if path.startswith('/api/'):
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
            return self._redirect_to_login(request)
        except Exception as e:
            logger.error(f"❌ Middleware error: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if path.startswith("/api/"):
                return JSONResponse(status_code=401, content={"detail": "Authentication required"})
            return self._redirect_to_login(request)
        
        return await call_next(request)
    
    def _is_public_route(self, path: str, request: Request = None) -> bool:
        """Check if route is public"""
        # Exact matches
        if path in self.public_routes or path in self.public_api_routes:
            return True
        
        # Check if path matches any registered public plugin
        for plugin_path in self.public_plugins:
            if path.startswith(plugin_path):
                return True
        
        # Dynamically check plugin manager for public plugins
        if request and hasattr(request.app.state, 'plugin_manager'):
            try:
                plugin_manager = request.app.state.plugin_manager
                # Extract plugin name from path like /api/v1/plugins/tradingview/...
                if path.startswith("/api/v1/plugins/"):
                    path_parts = path[16:].split("/")  # Remove /api/v1/plugins/
                    if path_parts:
                        plugin_name = path_parts[0]
                        plugins = plugin_manager.get_enabled_plugins()
                        if plugin_name in plugins:
                            plugin = plugins[plugin_name]
                            metadata = plugin.get_metadata()
                            if not metadata.requires_auth:
                                logger.debug(f"🔓 Plugin {plugin_name} is public (requires_auth=False)")
                                return True
            except Exception as e:
                logger.debug(f"Error checking plugin public status: {e}")
        
        # Prefix matches for static files
        public_prefixes = ["/static/", "/docs", "/redoc"]
        return any(path.startswith(prefix) for prefix in public_prefixes)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract token from Authorization header or cookie"""
        # Try Authorization header first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            logger.info(f"🔑 Token from Authorization header")
            return auth_header.split(" ")[1]
        
        # Try cookie
        token = request.cookies.get("access_token")
        logger.info(f"🍪 Token from cookie: {token[:20] if token else 'None'}...")
        logger.info(f"🍪 All cookies: {list(request.cookies.keys())}")
        return token
    
    def _redirect_to_login(self, request: Request):
        """Redirect to login page"""
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # For web routes, redirect to login
        login_url = f"/auth/login?next={request.url.path}"
        return RedirectResponse(url=login_url, status_code=302)


# Dependency for getting current user
async def get_current_user(request: Request):
    """Get current authenticated user"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.user


# Admin permission dependency
async def require_admin(current_user = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Optional user dependency (for public routes that want user info if available)
async def get_current_user_optional(request: Request):
    """Get current user if authenticated, None otherwise"""
    return getattr(request.state, "user", None)