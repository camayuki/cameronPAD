"""
Admin API Routes for User and Group Management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import logging
import bcrypt

from app_new.core.database import get_database_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    is_active: bool = True
    is_admin: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class GroupAssignment(BaseModel):
    group_ids: List[int]

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# User Management Endpoints
@router.get("/users")
async def list_users():
    """List all users with their groups"""
    db = get_database_manager()
    
    try:
        # Get all users
        users = db.execute_query("""
            SELECT id, username, email, is_active, is_admin, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        
        # Get groups for each user
        for user in users:
            groups = db.execute_query("""
                SELECT g.id, g.name
                FROM groups g
                JOIN user_groups ug ON g.id = ug.group_id
                WHERE ug.user_id = ?
            """, (user['id'],))
            user['groups'] = groups
        
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user with their groups"""
    db = get_database_manager()
    
    try:
        user = db.execute_query("""
            SELECT id, username, email, is_active, is_admin, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user[0]
        
        # Get groups
        groups = db.execute_query("""
            SELECT g.id, g.name
            FROM groups g
            JOIN user_groups ug ON g.id = ug.group_id
            WHERE ug.user_id = ?
        """, (user_id,))
        user['groups'] = groups
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
async def create_user(user_data: UserCreate):
    """Create a new user"""
    db = get_database_manager()
    
    try:
        # Check if username exists
        existing = db.execute_query("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists (if provided)
        if user_data.email:
            existing = db.execute_query("SELECT id FROM users WHERE email = ?", (user_data.email,))
            if existing:
                raise HTTPException(status_code=400, detail="Email already exists")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Insert user (using hashed_password to match existing schema)
        db.execute_update("""
            INSERT INTO users (username, email, hashed_password, is_active, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (user_data.username, user_data.email, password_hash, 
              1 if user_data.is_active else 0,
              1 if user_data.is_admin else 0))
        
        # Get the created user
        user = db.execute_query("SELECT * FROM users WHERE username = ?", (user_data.username,))[0]
        
        # Add to "Everyone" group
        everyone_group = db.execute_query("SELECT id FROM groups WHERE name = 'Everyone'")
        if everyone_group:
            db.execute_update("""
                INSERT INTO user_groups (user_id, group_id)
                VALUES (?, ?)
            """, (user['id'], everyone_group[0]['id']))
        
        # Add to "Admins" group if admin
        if user_data.is_admin:
            admins_group = db.execute_query("SELECT id FROM groups WHERE name = 'Admins'")
            if admins_group:
                db.execute_update("""
                    INSERT INTO user_groups (user_id, group_id)
                    VALUES (?, ?)
                """, (user['id'], admins_group[0]['id']))
        
        logger.info(f"✅ Created user: {user_data.username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate):
    """Update a user"""
    db = get_database_manager()
    
    try:
        # Check if user exists
        existing = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update query
        updates = []
        params = []
        
        if user_data.username is not None:
            updates.append("username = ?")
            params.append(user_data.username)
        
        if user_data.email is not None:
            updates.append("email = ?")
            params.append(user_data.email)
        
        if user_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if user_data.is_active else 0)
        
        if user_data.is_admin is not None:
            updates.append("is_admin = ?")
            params.append(1 if user_data.is_admin else 0)
        
        if updates:
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            db.execute_update(query, tuple(params))
        
        # Get updated user
        user = db.execute_query("SELECT id, username, email, is_active, is_admin, created_at FROM users WHERE id = ?", (user_id,))[0]
        
        logger.info(f"✅ Updated user: {user['username']}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    db = get_database_manager()
    
    try:
        # Check if user exists
        existing = db.execute_query("SELECT username FROM users WHERE id = ?", (user_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        username = existing[0]['username']
        
        # Delete user (cascades to user_groups)
        db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
        
        logger.info(f"🗑️ Deleted user: {username}")
        return {"message": f"User {username} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/groups")
async def assign_user_to_groups(user_id: int, assignment: GroupAssignment):
    """Assign a user to groups"""
    db = get_database_manager()
    
    try:
        # Check if user exists
        existing = db.execute_query("SELECT id FROM users WHERE id = ?", (user_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove all current group assignments
        db.execute_update("DELETE FROM user_groups WHERE user_id = ?", (user_id,))
        
        # Add new assignments
        for group_id in assignment.group_ids:
            db.execute_update("""
                INSERT INTO user_groups (user_id, group_id)
                VALUES (?, ?)
            """, (user_id, group_id))
        
        logger.info(f"✅ Updated group assignments for user {user_id}")
        return {"message": "Group assignments updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Group Management Endpoints
@router.get("/groups")
async def list_groups():
    """List all groups with member counts"""
    db = get_database_manager()
    
    try:
        groups = db.execute_query("""
            SELECT g.*, COUNT(ug.user_id) as member_count
            FROM groups g
            LEFT JOIN user_groups ug ON g.id = ug.group_id
            GROUP BY g.id
            ORDER BY g.created_at DESC
        """)
        
        # Get members for each group
        for group in groups:
            members = db.execute_query("""
                SELECT u.id, u.username
                FROM users u
                JOIN user_groups ug ON u.id = ug.user_id
                WHERE ug.group_id = ?
            """, (group['id'],))
            group['members'] = members
        
        return groups
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}")
async def get_group(group_id: int):
    """Get a specific group with members"""
    db = get_database_manager()
    
    try:
        group = db.execute_query("SELECT * FROM groups WHERE id = ?", (group_id,))
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        group = group[0]
        
        # Get members
        members = db.execute_query("""
            SELECT u.id, u.username, u.email
            FROM users u
            JOIN user_groups ug ON u.id = ug.user_id
            WHERE ug.group_id = ?
        """, (group_id,))
        group['members'] = members
        
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups")
async def create_group(group_data: GroupCreate, request: Request):
    """Create a new group"""
    db = get_database_manager()
    
    try:
        # Check if group name exists
        existing = db.execute_query("SELECT id FROM groups WHERE name = ?", (group_data.name,))
        if existing:
            raise HTTPException(status_code=400, detail="Group name already exists")
        
        # Get current user ID from request state (set by middleware)
        created_by = getattr(request.state, 'user_id', None)
        
        # Insert group
        db.execute_update("""
            INSERT INTO groups (name, description, created_by)
            VALUES (?, ?, ?)
        """, (group_data.name, group_data.description, created_by))
        
        # Get the created group
        group = db.execute_query("SELECT * FROM groups WHERE name = ?", (group_data.name,))[0]
        
        logger.info(f"✅ Created group: {group_data.name}")
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/groups/{group_id}")
async def update_group(group_id: int, group_data: GroupUpdate):
    """Update a group"""
    db = get_database_manager()
    
    try:
        # Check if group exists
        existing = db.execute_query("SELECT * FROM groups WHERE id = ?", (group_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Build update query
        updates = []
        params = []
        
        if group_data.name is not None:
            updates.append("name = ?")
            params.append(group_data.name)
        
        if group_data.description is not None:
            updates.append("description = ?")
            params.append(group_data.description)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(group_id)
            
            query = f"UPDATE groups SET {', '.join(updates)} WHERE id = ?"
            db.execute_update(query, tuple(params))
        
        # Get updated group
        group = db.execute_query("SELECT * FROM groups WHERE id = ?", (group_id,))[0]
        
        logger.info(f"✅ Updated group: {group['name']}")
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/groups/{group_id}")
async def delete_group(group_id: int):
    """Delete a group"""
    db = get_database_manager()
    
    try:
        # Check if group exists
        existing = db.execute_query("SELECT name FROM groups WHERE id = ?", (group_id,))
        if not existing:
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_name = existing[0]['name']
        
        # Prevent deletion of system groups
        if group_name in ['Everyone', 'Admins']:
            raise HTTPException(status_code=400, detail="Cannot delete system groups")
        
        # Delete group (cascades to user_groups and notes)
        db.execute_update("DELETE FROM groups WHERE id = ?", (group_id,))
        
        logger.info(f"🗑️ Deleted group: {group_name}")
        return {"message": f"Group {group_name} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/members")
async def get_group_members(group_id: int):
    """Get all members of a group"""
    db = get_database_manager()
    
    try:
        members = db.execute_query("""
            SELECT u.id, u.username, u.email, u.is_admin, ug.joined_at
            FROM users u
            JOIN user_groups ug ON u.id = ug.user_id
            WHERE ug.group_id = ?
            ORDER BY ug.joined_at DESC
        """, (group_id,))
        
        return members
    except Exception as e:
        logger.error(f"Error getting group members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics Endpoint
@router.get("/stats")
async def get_admin_stats():
    """Get admin dashboard statistics"""
    db = get_database_manager()
    
    try:
        # Get user stats
        user_stats = db.execute_query("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admin_users
            FROM users
        """)[0]
        
        # Get group stats
        group_stats = db.execute_query("SELECT COUNT(*) as total_groups FROM groups")[0]
        
        # Get notes stats
        notes_stats = db.execute_query("SELECT COUNT(*) as total_notes FROM notes")[0]
        
        return {
            "total_users": user_stats['total_users'],
            "active_users": user_stats['active_users'],
            "admin_users": user_stats['admin_users'],
            "total_groups": group_stats['total_groups'],
            "total_notes": notes_stats['total_notes']
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
