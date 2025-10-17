"""
API router configuration.
"""
from fastapi import APIRouter
from .admin import router as admin_router
from .auth import router as auth_router
from .services import router as services_router


def create_api_router() -> APIRouter:
    """Create the main API router with all sub-routers."""
    api_router = APIRouter(prefix="/api")
    
    # Include admin routes
    api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
    
    # Include services monitoring routes
    api_router.include_router(services_router, tags=["services"])
    
    return api_router
