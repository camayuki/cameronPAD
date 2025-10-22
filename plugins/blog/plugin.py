"""Blog Plugin - Reddit-style community forum with posts, comments, and voting."""

from __future__ import annotations

import sqlite3
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from math import log

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app_new.plugins.base import WebPlugin, PluginConfig, PluginMetadata
from .models import init_blog_db, get_db_connection

logger = logging.getLogger(__name__)


def extract_video_metadata(file_path: Path) -> Optional[datetime]:
    """
    Extract original creation date from video metadata.
    Tries multiple methods to get the most accurate creation date.
    """
    try:
        # Try using ffmpeg/ffprobe if available
        import subprocess
        import json
        
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                
                # Try to get creation_time from format tags
                if 'format' in metadata and 'tags' in metadata['format']:
                    tags = metadata['format']['tags']
                    
                    # Check various date fields
                    for date_field in ['creation_time', 'date', 'creation_date', 'encoded_date']:
                        if date_field in tags:
                            date_str = tags[date_field]
                            try:
                                # Parse ISO format date
                                if 'T' in date_str:
                                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                else:
                                    return datetime.strptime(date_str, '%Y-%m-%d')
                            except:
                                continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback to file modification time
        return datetime.fromtimestamp(file_path.stat().st_mtime)
        
    except Exception as e:
        logger.warning(f"Could not extract video metadata: {e}")
        return None


class BlogPlugin(WebPlugin):
    """Reddit-style blog system with posts, comments, threading, and voting."""
    
    def __init__(self, config: PluginConfig):
        """Initialize the blog plugin."""
        super().__init__(config)
        
        # Set up template directory with ChoiceLoader to find base.html
        template_dir = Path(__file__).parent / "templates"
        main_template_dir = Path(__file__).parent.parent.parent / "templates"
        
        # Use ChoiceLoader to search in plugin templates first, then main templates
        loader = ChoiceLoader([
            FileSystemLoader(str(template_dir)),
            FileSystemLoader(str(main_template_dir))
        ])
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.templates.env.loader = loader
        
        # Database path
        self.db_path = "data/cameronpad_dev.db"
        
        # Upload directory for media
        self.upload_dir = Path("data/blog_uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📝 Initializing Blog plugin...")

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="blog",
            version="1.0.0",
            description="Reddit-style community blog with posts, comments, and voting",
            author="CameronPAD",
            dependencies=[],
            api_version="1.0",
            enabled=True,
            priority=100,
            requires_auth=False
        )

    async def initialize(self):
        """Initialize the plugin and create database tables."""
        logger.info("📝 Initializing Blog plugin database...")
        try:
            # Initialize database tables
            init_blog_db(self.db_path)
            logger.info("✅ Blog database tables initialized")
            
            # Register routes
            self.register_routes()
            logger.info("✅ Blog routes registered")
            
            logger.info("✅ Blog plugin initialized successfully")
        except Exception as e:
            logger.error(f"❌ Blog plugin initialization failed: {e}", exc_info=True)
            raise

    async def shutdown(self):
        """Clean up resources."""
        logger.info("🛑 Blog plugin shutting down")

    def register_routes(self):
        """Register all blog routes."""
        
        def get_user_from_request(request: Request):
            """Extract user info from request state."""
            user_id = getattr(request.state, 'user_id', None)
            username = getattr(request.state, 'username', None)
            is_admin = getattr(request.state, 'is_admin', False)
            
            if user_id and username:
                return {
                    'id': user_id,
                    'username': username,
                    'is_admin': is_admin
                }
            return None
        
        def convert_datetime_fields(item: dict):
            """Convert ISO string datetime fields to datetime objects if needed."""
            if 'created_at' in item:
                if isinstance(item['created_at'], str):
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                # If it's already a datetime, leave it as is
            if 'updated_at' in item:
                if isinstance(item['updated_at'], str):
                    item['updated_at'] = datetime.fromisoformat(item['updated_at'])
            if 'media_created_at' in item and item['media_created_at']:
                if isinstance(item['media_created_at'], str):
                    item['media_created_at'] = datetime.fromisoformat(item['media_created_at'])
            return item
        
        def get_datetime_from_field(field):
            """Safely get datetime object from a field that might be string or datetime."""
            if isinstance(field, str):
                return datetime.fromisoformat(field)
            elif isinstance(field, datetime):
                return field
            else:
                return datetime.now()  # Fallback
        
        @self._router.get("/", response_class=HTMLResponse)
        async def blog_home(request: Request, sort: str = "hot"):
            """Display blog home page with posts."""
            try:
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                # Build query based on sort type
                if sort == "new":
                    query = "SELECT * FROM blog_posts WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT 50"
                elif sort == "top":
                    query = "SELECT * FROM blog_posts WHERE is_deleted = 0 ORDER BY (upvotes - downvotes) DESC LIMIT 50"
                else:  # hot
                    query = "SELECT * FROM blog_posts WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT 50"
                
                cur.execute(query)
                posts = [dict(row) for row in cur.fetchall()]
                
                # Convert datetime fields and calculate scores
                for post in posts:
                    convert_datetime_fields(post)
                    post['score'] = post['upvotes'] - post['downvotes']
                    
                    # Calculate hot score (Reddit-style algorithm)
                    if sort == "hot":
                        score = post['score']
                        order = log(max(abs(score), 1), 10)
                        sign = 1 if score > 0 else -1 if score < 0 else 0
                        
                        # Time decay based on post age
                        created = get_datetime_from_field(post['created_at'])
                        age_hours = (datetime.now() - created).total_seconds() / 3600
                        post['hot_score'] = sign * order - age_hours / 12
                    else:
                        post['hot_score'] = 0
                
                # Re-sort by hot score if needed
                if sort == "hot":
                    posts.sort(key=lambda p: p['hot_score'], reverse=True)
                
                conn.close()
                
                # Get user info from session if available
                user = get_user_from_request(request)
                
                return self.templates.TemplateResponse(
                    "blog.html",
                    {
                        "request": request,
                        "posts": posts,
                        "sort": sort,
                        "user": user
                    }
                )
            except Exception as e:
                logger.error(f"Error loading blog home: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to load blog")

        @self._router.get("/post/{post_id}", response_class=HTMLResponse)
        async def view_post(request: Request, post_id: int):
            """View a single post with comments."""
            try:
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                # Get the post
                cur.execute("SELECT * FROM blog_posts WHERE id = ? AND is_deleted = 0", (post_id,))
                post = cur.fetchone()
                
                if not post:
                    conn.close()
                    raise HTTPException(status_code=404, detail="Post not found")
                
                post = dict(post)
                convert_datetime_fields(post)
                post['score'] = post['upvotes'] - post['downvotes']
                
                # Increment view count
                cur.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE id = ?", (post_id,))
                conn.commit()
                
                # Get top-level comments (parent_id IS NULL)
                cur.execute("""
                    SELECT * FROM blog_comments 
                    WHERE post_id = ? AND parent_id IS NULL AND is_deleted = 0
                    ORDER BY (upvotes - downvotes) DESC, created_at ASC
                """, (post_id,))
                comments = [dict(row) for row in cur.fetchall()]
                
                # For each comment, get its replies and convert datetime fields
                for comment in comments:
                    convert_datetime_fields(comment)
                    comment['score'] = comment['upvotes'] - comment['downvotes']
                    
                    cur.execute("""
                        SELECT * FROM blog_comments 
                        WHERE parent_id = ? AND is_deleted = 0
                        ORDER BY (upvotes - downvotes) DESC, created_at ASC
                    """, (comment['id'],))
                    comment['replies'] = [dict(row) for row in cur.fetchall()]
                    
                    for reply in comment['replies']:
                        convert_datetime_fields(reply)
                        reply['score'] = reply['upvotes'] - reply['downvotes']
                
                conn.close()
                
                # Get user info from session if available
                user = get_user_from_request(request)
                
                return self.templates.TemplateResponse(
                    "post_detail.html",
                    {
                        "request": request,
                        "post": post,
                        "comments": comments,
                        "user": user
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error loading post {post_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to load post")

        @self._router.post("/post/create")
        async def create_post(
            request: Request,
            title: str = Form(...),
            content: Optional[str] = Form(None),
            media: Optional[UploadFile] = File(None)
        ):
            """Create a new post."""
            try:
                # Get user from session
                user = get_user_from_request(request)
                if not user:
                    return RedirectResponse(url="/api/v1/auth/login", status_code=303)
                
                # Handle media upload
                media_url = None
                media_type = None
                media_created_at = None
                
                if media and media.filename:
                    # Validate file type
                    ext = Path(media.filename).suffix.lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        media_type = 'image'
                    elif ext in ['.mp4', '.webm', '.mov', '.avi']:
                        media_type = 'video'
                    else:
                        raise HTTPException(status_code=400, detail="Unsupported file type")
                    
                    # Save file
                    file_id = str(uuid.uuid4())
                    filename = f"{file_id}{ext}"
                    file_path = self.upload_dir / filename
                    
                    with open(file_path, "wb") as f:
                        content_bytes = await media.read()
                        f.write(content_bytes)
                    
                    media_url = f"/api/v1/plugins/blog/media/{filename}"
                    
                    # Extract video metadata if it's a video
                    if media_type == 'video':
                        media_created_at = extract_video_metadata(file_path)
                        if media_created_at:
                            logger.info(f"📹 Extracted video creation date: {media_created_at}")
                
                # Insert post into database
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO blog_posts (
                        title, content, author_id, author_name, 
                        image_url, video_url, media_type, media_created_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    content or "",
                    user['id'],
                    user['username'],
                    media_url if media_type == 'image' else None,
                    media_url if media_type == 'video' else None,
                    media_type,
                    media_created_at.isoformat() if media_created_at else None,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                post_id = cur.lastrowid
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Created post {post_id} by user {user['username']}")
                
                return RedirectResponse(url=f"/api/v1/plugins/blog/post/{post_id}", status_code=303)
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating post: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to create post")

        @self._router.post("/post/{post_id}/comment")
        async def add_comment(
            request: Request,
            post_id: int,
            content: str = Form(...),
            parent_id: Optional[int] = Form(None),
            media: Optional[UploadFile] = File(None)
        ):
            """Add a comment to a post."""
            try:
                # Get user from session
                user = get_user_from_request(request)
                if not user:
                    return RedirectResponse(url="/api/v1/auth/login", status_code=303)
                
                # Handle media upload
                media_url = None
                media_type = None
                
                if media and media.filename:
                    ext = Path(media.filename).suffix.lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        media_type = 'image'
                    elif ext in ['.mp4', '.webm', '.mov', '.avi']:
                        media_type = 'video'
                    else:
                        raise HTTPException(status_code=400, detail="Unsupported file type")
                    
                    file_id = str(uuid.uuid4())
                    filename = f"{file_id}{ext}"
                    file_path = self.upload_dir / filename
                    
                    with open(file_path, "wb") as f:
                        content_bytes = await media.read()
                        f.write(content_bytes)
                    
                    media_url = f"/api/v1/plugins/blog/media/{filename}"
                
                # Insert comment
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO blog_comments (
                        post_id, parent_id, author_id, author_name, content,
                        image_url, video_url, media_type, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id,
                    parent_id,
                    user['id'],
                    user['username'],
                    content,
                    media_url if media_type == 'image' else None,
                    media_url if media_type == 'video' else None,
                    media_type,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                # Update post comment count
                cur.execute("UPDATE blog_posts SET comment_count = comment_count + 1 WHERE id = ?", (post_id,))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Added comment to post {post_id} by user {user['username']}")
                
                return RedirectResponse(url=f"/api/v1/plugins/blog/post/{post_id}", status_code=303)
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error adding comment: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to add comment")

        @self._router.post("/post/{post_id}/vote")
        async def vote_post(request: Request, post_id: int, vote_type: str = Form(...)):
            """Vote on a post (upvote/downvote)."""
            try:
                # Get user from session
                user = get_user_from_request(request)
                if not user:
                    return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)
                
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                # Check if user has already voted
                cur.execute("SELECT vote_type FROM post_votes WHERE post_id = ? AND user_id = ?", (post_id, user['id']))
                existing_vote = cur.fetchone()
                
                if existing_vote:
                    existing_type = existing_vote['vote_type']
                    
                    if existing_type == vote_type:
                        # Remove vote
                        cur.execute("DELETE FROM post_votes WHERE post_id = ? AND user_id = ?", (post_id, user['id']))
                        
                        # Update post counts
                        if vote_type == 'upvote':
                            cur.execute("UPDATE blog_posts SET upvotes = upvotes - 1 WHERE id = ?", (post_id,))
                        else:
                            cur.execute("UPDATE blog_posts SET downvotes = downvotes - 1 WHERE id = ?", (post_id,))
                    else:
                        # Change vote
                        cur.execute("UPDATE post_votes SET vote_type = ? WHERE post_id = ? AND user_id = ?", 
                                  (vote_type, post_id, user['id']))
                        
                        # Update post counts
                        if vote_type == 'upvote':
                            cur.execute("UPDATE blog_posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?", (post_id,))
                        else:
                            cur.execute("UPDATE blog_posts SET downvotes = downvotes + 1, upvotes = upvotes - 1 WHERE id = ?", (post_id,))
                else:
                    # New vote
                    cur.execute("INSERT INTO post_votes (post_id, user_id, vote_type, created_at) VALUES (?, ?, ?, ?)",
                              (post_id, user['id'], vote_type, datetime.now().isoformat()))
                    
                    # Update post counts
                    if vote_type == 'upvote':
                        cur.execute("UPDATE blog_posts SET upvotes = upvotes + 1 WHERE id = ?", (post_id,))
                    else:
                        cur.execute("UPDATE blog_posts SET downvotes = downvotes + 1 WHERE id = ?", (post_id,))
                
                conn.commit()
                
                # Get updated score
                cur.execute("SELECT upvotes, downvotes FROM blog_posts WHERE id = ?", (post_id,))
                post = cur.fetchone()
                score = post['upvotes'] - post['downvotes']
                
                conn.close()
                
                return JSONResponse({"success": True, "score": score})
            
            except Exception as e:
                logger.error(f"Error voting on post {post_id}: {e}", exc_info=True)
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @self._router.post("/comment/{comment_id}/vote")
        async def vote_comment(request: Request, comment_id: int, vote_type: str = Form(...)):
            """Vote on a comment (upvote/downvote)."""
            try:
                # Get user from session
                user = get_user_from_request(request)
                if not user:
                    return JSONResponse({"success": False, "error": "Not authenticated"}, status_code=401)
                
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                # Check if user has already voted
                cur.execute("SELECT vote_type FROM comment_votes WHERE comment_id = ? AND user_id = ?", (comment_id, user['id']))
                existing_vote = cur.fetchone()
                
                if existing_vote:
                    existing_type = existing_vote['vote_type']
                    
                    if existing_type == vote_type:
                        # Remove vote
                        cur.execute("DELETE FROM comment_votes WHERE comment_id = ? AND user_id = ?", (comment_id, user['id']))
                        
                        # Update comment counts
                        if vote_type == 'upvote':
                            cur.execute("UPDATE blog_comments SET upvotes = upvotes - 1 WHERE id = ?", (comment_id,))
                        else:
                            cur.execute("UPDATE blog_comments SET downvotes = downvotes - 1 WHERE id = ?", (comment_id,))
                    else:
                        # Change vote
                        cur.execute("UPDATE comment_votes SET vote_type = ? WHERE comment_id = ? AND user_id = ?", 
                                  (vote_type, comment_id, user['id']))
                        
                        # Update comment counts
                        if vote_type == 'upvote':
                            cur.execute("UPDATE blog_comments SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?", (comment_id,))
                        else:
                            cur.execute("UPDATE blog_comments SET downvotes = downvotes + 1, upvotes = upvotes - 1 WHERE id = ?", (comment_id,))
                else:
                    # New vote
                    cur.execute("INSERT INTO comment_votes (comment_id, user_id, vote_type, created_at) VALUES (?, ?, ?, ?)",
                              (comment_id, user['id'], vote_type, datetime.now().isoformat()))
                    
                    # Update comment counts
                    if vote_type == 'upvote':
                        cur.execute("UPDATE blog_comments SET upvotes = upvotes + 1 WHERE id = ?", (comment_id,))
                    else:
                        cur.execute("UPDATE blog_comments SET downvotes = downvotes + 1 WHERE id = ?", (comment_id,))
                
                conn.commit()
                
                # Get updated score
                cur.execute("SELECT upvotes, downvotes FROM blog_comments WHERE id = ?", (comment_id,))
                comment = cur.fetchone()
                score = comment['upvotes'] - comment['downvotes']
                
                conn.close()
                
                return JSONResponse({"success": True, "score": score})
            
            except Exception as e:
                logger.error(f"Error voting on comment {comment_id}: {e}", exc_info=True)
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @self._router.post("/post/{post_id}/delete")
        async def delete_post(request: Request, post_id: int):
            """Delete a post (admin only)."""
            try:
                user = get_user_from_request(request)
                if not user or not user.get('is_admin'):
                    raise HTTPException(status_code=403, detail="Admin access required")
                
                conn = get_db_connection(self.db_path)
                cur = conn.cursor()
                
                # Soft delete the post
                cur.execute("""
                    UPDATE blog_posts 
                    SET is_deleted = 1, updated_at = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), post_id))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Admin {user['username']} deleted post {post_id}")
                return RedirectResponse(url="/api/v1/plugins/blog/", status_code=303)
            
            except Exception as e:
                logger.error(f"Error deleting post {post_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to delete post")

        @self._router.get("/media/{filename}")
        async def get_media(filename: str):
            """Serve uploaded media files."""
            from fastapi.responses import FileResponse
            file_path = self.upload_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Media file not found")
            
            # Determine media type
            suffix = file_path.suffix.lower()
            if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                media_type = f"image/{suffix[1:]}"
            elif suffix in ['.mp4', '.webm', '.ogg']:
                media_type = f"video/{suffix[1:]}"
            else:
                media_type = "application/octet-stream"
            
            return FileResponse(file_path, media_type=media_type)

        @self._router.get("/status")
        async def status():
            """Health check endpoint."""
            return {"status": "healthy", "plugin": "blog"}




