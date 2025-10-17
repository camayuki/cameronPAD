"""
Middleware configuration for the API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from ..core.middleware import AuthenticationMiddleware
from ..core.config import AppConfig


def setup_middleware(app: FastAPI, config: AppConfig = None):
    """Set up all middleware for the application."""
    
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
