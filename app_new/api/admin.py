# Admin User Management Routes

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app_new.core.middleware import get_current_user, require_admin
from app_new.core.database import get_database_manager
from app_new.core.auth import SecurityManager

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

# Web routes for admin interface
@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user = Depends(require_admin)
):
    """Admin users management page"""
    db = get_database_manager()
    users = await db.get_all_users()
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "current_user": current_user
        }
    )

@router.get("/users/create", response_class=HTMLResponse)
async def create_user_page(
    request: Request,
    current_user = Depends(require_admin)
):
    """Create user page"""
    return templates.TemplateResponse(
        "admin/create_user.html",
        {
            "request": request,
            "current_user": current_user,
            "roles": ["user", "moderator", "admin"]
        }
    )

# API routes for admin interface
@router.get("/api/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(require_admin)
):
    """List all users"""
    db = get_database_manager()
    users = await db.get_users(skip=skip, limit=limit)
    return users

@router.post("/api/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user = Depends(require_admin)
):
    """Create new user"""
    db = get_database_manager()
    security = SecurityManager()
    
    # Check if username or email already exists
    existing_user = await db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    existing_email = await db.get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash password
    hashed_password = security.hash_password(user_data.password)
    
    # Create user
    user = await db.create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    return user

@router.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(require_admin)
):
    """Get user by ID"""
    db = get_database_manager()
    user = await db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user = Depends(require_admin)
):
    """Update user"""
    db = get_database_manager()
    
    # Get existing user
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from disabling themselves
    if user_id == current_user.id and user_data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    
    # Update user
    updated_user = await db.update_user(user_id, user_data.dict(exclude_unset=True))
    return updated_user

@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(require_admin)
):
    """Delete user"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db = get_database_manager()
    success = await db.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@router.post("/api/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    current_user = Depends(require_admin)
):
    """Reset user password"""
    db = get_database_manager()
    security = SecurityManager()
    
    # Hash new password
    hashed_password = security.hash_password(new_password)
    
    # Update password
    success = await db.update_user_password(user_id, hashed_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully"}

@router.post("/api/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user = Depends(require_admin)
):
    """Toggle user active status"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own status")
    
    db = get_database_manager()
    user = await db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Toggle status
    new_status = not user.is_active
    await db.update_user(user_id, {"is_active": new_status})
    
    status_text = "activated" if new_status else "deactivated"
    return {"message": f"User {status_text} successfully"}

# Dashboard route
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user = Depends(require_admin)
):
    """Admin dashboard"""
    db = get_database_manager()
    
    # Get dashboard stats
    stats = {
        "total_users": await db.count_users(),
        "active_users": await db.count_active_users(),
        "total_plugins": len(await db.get_enabled_plugins()),
        "recent_logins": await db.get_recent_logins(limit=10)
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats
        }
    )