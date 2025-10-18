"""
Middleware configuration for the API.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.middleware import AuthenticationMiddleware
from ..core.config import AppConfig


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware with permissive CSP for development"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # CRITICAL: Meta tag CSP doesn't work for 'unsafe-eval'
        # Must be sent via HTTP header from server
        # DEVELOPMENT ONLY - allows Babel/React eval()
        if not response.headers.get("Content-Security-Policy"):
            response.headers["Content-Security-Policy"] = (
                "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
                "script-src * 'unsafe-inline' 'unsafe-eval'; "
                "style-src * 'unsafe-inline';"
            )
        
        return response


def setup_middleware(app: FastAPI, config: AppConfig = None):
    """Set up all middleware for the application."""
    
    # Security headers middleware (must be first to add headers to all responses)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS middleware
    cors_origins = ["*"] if config and config.debug else (config.security.cors_origins if config else ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Authentication middleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Trusted host middleware for production
    # if config and not config.debug:
    #     app.add_middleware(
    #         TrustedHostMiddleware,
    #         allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    #     )
